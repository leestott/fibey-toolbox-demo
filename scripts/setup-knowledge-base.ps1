#Requires -Version 7.2
<#
Run after provisioning: pwsh -File scripts/setup-knowledge-base.ps1 [-EnvironmentName <name>]
Requires az login, azd auth login, and provisioned azd environment outputs.
Operator: Storage Blob Data Contributor, Search Service Contributor, Search Index Data Reader,
and permission to create Foundry project connections. Search's system identity needs Storage
Blob Data Reader; Foundry's project identity needs Search Index Data Reader. Infra owns RBAC.
This script uploads/overwrites demo Markdown and upserts Search objects and a Foundry connection.
It never provisions infrastructure, assigns roles, retrieves account keys, or deletes documents.
Reruns reindex all uploaded Markdown; removing a local file does not delete its existing blob.
Do not run with PowerShell tracing/transcripts or az/azd debug logging: CLI output stays in memory.

Search objects use 2026-04-01 GA. Knowledge-base defaults and MCP use the preview API
so minimal/extractive retrieval is explicit and does not require another model:
https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base
https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-search-index
https://learn.microsoft.com/azure/search/search-how-to-index-azure-blob-storage
https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-pipeline
#>
[CmdletBinding()]
param(
    [string] $EnvironmentName,
    [ValidateRange(30, 3600)] [int] $TimeoutSeconds = 900,
    [switch] $CheckOnly
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path $PSScriptRoot -Parent
$azdOptions = @('--cwd', $root, '--no-prompt')
if ($EnvironmentName) { $azdOptions += @('--environment', $EnvironmentName) }

function Invoke-QuietCli {
    param([string] $Command, [string[]] $Arguments, [string] $Step)
    # Never include native output or arguments in errors; either can contain credentials.
    try { $text = & $Command @Arguments 2>$null | Out-String }
    catch { throw "$Step failed. Check CLI installation and authentication (output suppressed)." }
    if ($LASTEXITCODE -ne 0) { throw "$Step failed (exit $LASTEXITCODE). Check authentication, configuration and RBAC; CLI output suppressed." }
    return $text.Trim()
}

function Get-Setting {
    param([string] $Name, [string[]] $Aliases = @())
    foreach ($key in @($Name) + $Aliases) {
        if (-not [string]::IsNullOrWhiteSpace($settings[$key])) { return [string] $settings[$key] }
    }
    throw "Missing azd setting $Name. Provision first or set it in the selected azd environment."
}

function Assert-HttpsEndpoint {
    param([string] $Value, [string] $Name)
    $uri = $null
    if (-not [uri]::TryCreate($Value, [UriKind]::Absolute, [ref] $uri) -or
        $uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Query -or $uri.Fragment) {
        throw "$Name must be an absolute HTTPS endpoint without credentials, query or fragment."
    }
}

foreach ($command in @('az', 'azd')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "Install $command before running this script." }
}
try {
    $settings = Invoke-QuietCli azd (@('env', 'get-values', '--output', 'json') + $azdOptions) 'Read azd environment' |
        ConvertFrom-Json -AsHashtable
} catch { throw 'Cannot read the selected azd environment as JSON. Run azd env select and authenticate; values suppressed.' }
$subscription = Get-Setting 'AZURE_SUBSCRIPTION_ID'
$resourceGroup = Get-Setting 'AZURE_RESOURCE_GROUP'
$storage = Get-Setting 'AZURE_STORAGE_ACCOUNT_NAME'
$search = Get-Setting 'AZURE_SEARCH_NAME' @('AZURE_SEARCH_SERVICE_NAME')
$searchEndpoint = (Get-Setting 'AZURE_SEARCH_ENDPOINT').TrimEnd('/')
$projectEndpoint = (Get-Setting 'FOUNDRY_PROJECT_ENDPOINT').TrimEnd('/')
$projectName = Get-Setting 'AZURE_AI_PROJECT_NAME'
$foundryGroup = Get-Setting 'AZURE_FOUNDRY_RESOURCE_GROUP'
$account = Get-Setting 'AZURE_AI_ACCOUNT_NAME'
$expectedProjectId = "/subscriptions/$subscription/resourceGroups/$foundryGroup/providers/Microsoft.CognitiveServices/accounts/$account/projects/$projectName"
if ($settings['AZURE_AI_PROJECT_ID'] -and $settings['AZURE_AI_PROJECT_ID'].TrimEnd('/') -ne $expectedProjectId) {
    throw 'AZURE_AI_PROJECT_ID does not match the subscription, Foundry resource group, account and project settings.'
}
Assert-HttpsEndpoint $searchEndpoint 'AZURE_SEARCH_ENDPOINT'
Assert-HttpsEndpoint $projectEndpoint 'FOUNDRY_PROJECT_ENDPOINT'
if ($searchEndpoint -ne "https://$search.search.windows.net") { throw 'Search name and endpoint do not match.' }
if (([uri] $projectEndpoint).AbsolutePath.TrimEnd('/') -ne "/api/projects/$projectName") {
    throw 'FOUNDRY_PROJECT_ENDPOINT must end with /api/projects/AZURE_AI_PROJECT_NAME.'
}
$docs = Join-Path (Join-Path (Join-Path $root 'services') 'foundry-iq-docs') 'docs'
$documentCount = @(Get-ChildItem $docs -Filter '*.md' -File -Recurse).Count
if ($documentCount -eq 0) { throw 'No Markdown documents found in services/foundry-iq-docs/docs.' }
$connectionHelp = Invoke-QuietCli azd @('ai', 'connection', 'create', '--help') 'Check azd AI connection extension'
if ($connectionHelp -notmatch 'project-managed-identity' -or $connectionHelp -notmatch '--force') {
    throw 'Update the azd AI connections extension; project-managed-identity and --force are required.'
}
if ($CheckOnly) {
    Write-Host "Configuration valid; $documentCount Markdown documents. No cloud requests or writes performed."
    return
}

$apiVersion = '2026-04-01'
$mcpApiVersion = '2026-08-01-preview'
$container = 'foundry-iq-docs'
$index = 'foundry-iq-docs-index'
$datasource = 'foundry-iq-docs-ds'
$indexer = 'foundry-iq-docs-indexer'
$knowledgeSource = 'fibey-field-ops-ks'
$knowledgeBase = 'fibey-field-ops-kb'
$connection = 'kb-fibey-field-ops-kb'
$script:searchToken = $null
$script:tokenTime = [datetime]::MinValue

function Invoke-Search {
    param([string] $Method, [string] $Path, [object] $Body, [int[]] $Accept = @(),
        [string] $Version = $apiVersion)
    for ($attempt = 0; $attempt -lt 7; $attempt++) {
        if (-not $script:searchToken -or ([datetime]::UtcNow - $script:tokenTime).TotalMinutes -gt 45) {
            $script:searchToken = Invoke-QuietCli az @(
                'account', 'get-access-token', '--subscription', $subscription,
                '--scope', 'https://search.azure.com/.default', '--query', 'accessToken', '--output', 'tsv', '--only-show-errors'
            ) 'Get Search bearer token'
            $script:tokenTime = [datetime]::UtcNow
        }
        $request = @{
            Uri = "$searchEndpoint/$($Path)?api-version=$Version"
            Method = $Method
            Headers = @{ Authorization = "Bearer $script:searchToken" }
            ContentType = 'application/json'
            SkipHttpErrorCheck = $true
            TimeoutSec = 60
        }
        if ($null -ne $Body) { $request.Body = $Body | ConvertTo-Json -Depth 40 -Compress }
        try { $response = Invoke-WebRequest @request }
        catch { throw "Search $Method $Path could not connect. Check the endpoint, firewall and network; details suppressed." }
        $code = [int] $response.StatusCode
        if (($code -ge 200 -and $code -lt 300) -or $code -in $Accept) {
            $data = if ($response.Content -and $code -ge 200 -and $code -lt 300) {
                $response.Content | ConvertFrom-Json -AsHashtable
            } else { $null }
            return @{ StatusCode = $code; Data = $data }
        }
        if ($code -eq 401) { $script:searchToken = $null }
        if ($code -notin @(401, 403, 429, 500, 502, 503, 504) -or $attempt -eq 6) {
            throw "Search $Method $Path failed (HTTP $code). Check Search roles, API schema, semantic ranker and service networking."
        }
        Start-Sleep -Seconds ([math]::Min(2 * [math]::Pow(2, $attempt), 15))
    }
}

# Preflight the existing service before uploading. No API-key fallback is permitted.
$null = Invoke-Search GET "indexes/$index" -Accept @(404)
$storageId = Invoke-QuietCli az @(
    'storage', 'account', 'show', '--name', $storage, '--resource-group', $resourceGroup,
    '--subscription', $subscription, '--query', 'id', '--output', 'tsv', '--only-show-errors'
) 'Resolve storage resource ID'
if ($storageId -notmatch '^/subscriptions/.+/providers/Microsoft.Storage/storageAccounts/[^/]+$') {
    throw 'Storage account lookup returned an invalid resource ID.'
}

Write-Host "Uploading $documentCount Markdown documents using your signed-in identity..."
$null = Invoke-QuietCli az @(
    'storage', 'container', 'create', '--name', $container, '--account-name', $storage,
    '--subscription', $subscription, '--auth-mode', 'login', '--public-access', 'off', '--output', 'none', '--only-show-errors'
) 'Ensure private document container'
$null = Invoke-QuietCli az @(
    'storage', 'blob', 'upload-batch', '--source', $docs, '--destination', $container,
    '--account-name', $storage, '--subscription', $subscription, '--auth-mode', 'login',
    '--pattern', '*.md', '--overwrite', 'true', '--no-progress', '--output', 'none', '--only-show-errors'
) 'Upload documents (requires Storage Blob Data Contributor)'
$null = Invoke-Search PUT "datasources/$datasource" @{
    name = $datasource; type = 'azureblob'
    credentials = @{ connectionString = "ResourceId=$storageId/;" }
    container = @{ name = $container }
}
$null = Invoke-Search PUT "indexes/$index" @{
    name = $index
    fields = @(
        @{ name = 'id'; type = 'Edm.String'; key = $true; filterable = $true; retrievable = $true }
        @{ name = 'content'; type = 'Edm.String'; searchable = $true; retrievable = $true }
        @{ name = 'metadata_storage_path'; type = 'Edm.String'; filterable = $true; retrievable = $true }
        @{ name = 'metadata_storage_name'; type = 'Edm.String'; searchable = $true; filterable = $true; retrievable = $true }
    )
    semantic = @{
        defaultConfiguration = 'default'
        configurations = @(@{
            name = 'default'
            prioritizedFields = @{
                titleField = @{ fieldName = 'metadata_storage_name' }
                prioritizedContentFields = @(@{ fieldName = 'content' })
            }
        })
    }
}
$null = Invoke-Search PUT "indexers/$indexer" @{
    name = $indexer; dataSourceName = $datasource; targetIndexName = $index
    fieldMappings = @(@{
        sourceFieldName = 'metadata_storage_path'; targetFieldName = 'id'
        mappingFunction = @{ name = 'base64Encode' }
    })
    parameters = @{
        maxFailedItems = 0; maxFailedItemsPerBatch = 0
        configuration = @{ parsingMode = 'default'; dataToExtract = 'contentAndMetadata'; indexedFileNameExtensions = '.md' }
    }
    schedule = $null
}

# Creation can start an automatic run. Wait for it, then reset/run explicitly so an old
# successful lastResult cannot be mistaken for completion of this upload.
$deadline = [datetime]::UtcNow.AddSeconds($TimeoutSeconds)
do {
    $previous = (Invoke-Search GET "indexers/$indexer/status").Data.lastResult
    if ($previous.status -ne 'inProgress') {
        $reset = Invoke-Search POST "indexers/$indexer/reset" -Accept @(409)
        if ($reset.StatusCode -ne 409) {
            $run = Invoke-Search POST "indexers/$indexer/run" -Accept @(409)
            if ($run.StatusCode -ne 409) { break }
        }
    }
    if ([datetime]::UtcNow -ge $deadline) { throw 'Timed out waiting to start the indexer. Check its execution history.' }
    Start-Sleep -Seconds 5
} while ($true)

Write-Host 'Waiting for the new indexer execution to succeed...'
do {
    $last = (Invoke-Search GET "indexers/$indexer/status").Data.lastResult
    if ($last -and $last.startTime -and $last.startTime -ne $previous.startTime) {
        if ($last.status -eq 'success') {
            if ($last.itemsFailed -gt 0 -or $last.errors) {
                throw 'Indexer reported document failures. Check Search execution history and Storage Blob Data Reader on the Search identity.'
            }
            break
        }
        if ($last.status -in @('transientFailure', 'persistentFailure')) {
            throw "New indexer execution ended with $($last.status). Check Search execution history, storage networking and managed-identity RBAC; rerun after correcting it."
        }
    }
    if ([datetime]::UtcNow -ge $deadline) { throw 'Indexer did not finish successfully before the timeout. No knowledge base/connection was configured.' }
    Start-Sleep -Seconds 5
} while ($true)

# Search visibility can lag an otherwise successful indexer execution.
do {
    $indexed = (Invoke-Search POST "indexes/$index/docs/search" @{ search = '*'; top = 0; count = $true }).Data
    if ($indexed['@odata.count'] -ge $documentCount) { break }
    if ([datetime]::UtcNow -ge $deadline) { throw 'The index contains fewer documents than uploaded; inspect the indexer before continuing.' }
    Start-Sleep -Seconds 5
} while ($true)
$null = Invoke-Search PUT "knowledgesources/$knowledgeSource" @{
    name = $knowledgeSource; kind = 'searchIndex'
    description = 'Fibey field operations procedures, safety guidance and troubleshooting.'
    searchIndexParameters = @{
        searchIndexName = $index; semanticConfigurationName = 'default'
        sourceDataFields = @(
            @{ name = 'id' }, @{ name = 'content' },
            @{ name = 'metadata_storage_name' }, @{ name = 'metadata_storage_path' }
        )
        searchFields = @(@{ name = 'content' })
    }
}
$null = Invoke-Search PUT "knowledgebases/$knowledgeBase" @{
    name = $knowledgeBase
    description = 'Fibey Field Ops: minimal, extractive retrieval over the field documentation.'
    knowledgeSources = @(@{ name = $knowledgeSource })
    retrievalReasoningEffort = @{ kind = 'minimal' }
    outputMode = 'extractiveData'
    retrieveDefaults = @{ maxOutputDocuments = 3; maxOutputSizeInTokens = 6000 }
} -Version $mcpApiVersion
$mcpEndpoint = "$searchEndpoint/knowledgebases/$knowledgeBase/mcp?api-version=$mcpApiVersion"
$null = Invoke-QuietCli azd (@(
    'ai', 'connection', 'create', $connection, '--kind', 'remote-tool',
    '--target', $mcpEndpoint, '--auth-type', 'project-managed-identity',
    '--audience', 'https://search.azure.com/', '--metadata', 'ApiType=Azure', '--force',
    '--project-endpoint', $projectEndpoint, '--output', 'json'
) + $azdOptions) 'Upsert Foundry IQ project-managed-identity connection'
$verified = (Invoke-Search GET "knowledgebases/$knowledgeBase" -Version $mcpApiVersion).Data
if ($verified.name -ne $knowledgeBase -or $verified.retrievalReasoningEffort.kind -ne 'minimal' -or
    $verified.outputMode -ne 'extractiveData') {
    throw 'Knowledge base read-back verification failed: minimal/extractive retrieval is required.'
}
$script:searchToken = $null
$settings = $null
Write-Host "Knowledge base ready: $knowledgeBase ($($indexed['@odata.count']) indexed documents)."
Write-Host "Foundry connection: $connection. Next run scripts/setup-toolbox.ps1."
