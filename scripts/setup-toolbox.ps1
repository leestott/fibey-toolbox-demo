#Requires -Version 7.2
<#
Run after setup-knowledge-base.ps1 and the protected inventory/work-orders services are deployed:
  pwsh -File scripts/setup-toolbox.ps1 [-EnvironmentName <name>]
Requires azd auth login, the azd AI connection/toolbox extensions, and Foundry project
connection/toolbox write permission. It does not provision infrastructure or assign roles.
The selected ignored azd environment must contain INVENTORY_API_KEY and WORK_ORDERS_API_KEY.
Values and native output stay in memory; never enable tracing/transcripts/CLI debug logging.
Only the Foundry connections store credentials; the disposable toolbox JSON contains references.
The rendered JSON is created under the project's ignored .azure directory, not system temp.

Demo limitation: the UI has no approval workflow. MCP require_approval is deliberately never,
and OpenAPI writes execute without human approval. Work orders are resettable synthetic data.
Do NOT reuse this policy for real operational work orders without adding an approval workflow.
get_network_status is already on inventory MCP; no Browser Automation resource is created.

https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox
https://learn.microsoft.com/azure/foundry/agents/how-to/tools/openapi
https://learn.microsoft.com/azure/foundry/agents/how-to/tools/model-context-protocol
#>
[CmdletBinding()]
param([string] $EnvironmentName, [switch] $CheckOnly)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
$root = Split-Path $PSScriptRoot -Parent
$azdOptions = @('--cwd', $root, '--no-prompt')
if ($EnvironmentName) { $azdOptions += @('--environment', $EnvironmentName) }

function Invoke-QuietAzd {
    param([string[]] $Arguments, [string] $Step)
    # azd extensions may emit diagnostics on stderr even with --output json.
    try { $text = & azd @Arguments 2>$null | Out-String }
    catch { throw "$Step failed. Check azd installation and authentication; output suppressed." }
    if ($LASTEXITCODE -ne 0) { throw "$Step failed (exit $LASTEXITCODE). Check project permissions and azd authentication; output suppressed." }
    return $text.Trim()
}

function Get-Setting {
    param([string] $Name, [string[]] $Aliases = @())
    foreach ($key in @($Name) + $Aliases) {
        if (-not [string]::IsNullOrWhiteSpace($settings[$key])) { return [string] $settings[$key] }
    }
    throw "Missing azd setting $Name. Provision/deploy first or set it in the selected ignored azd environment."
}

function Assert-HttpsEndpoint {
    param([string] $Value, [string] $Name)
    $uri = $null
    if (-not [uri]::TryCreate($Value, [UriKind]::Absolute, [ref] $uri) -or
        $uri.Scheme -ne 'https' -or $uri.UserInfo -or $uri.Query -or $uri.Fragment) {
        throw "$Name must be an absolute HTTPS endpoint without credentials, query or fragment."
    }
}

if (-not (Get-Command azd -ErrorAction SilentlyContinue)) { throw 'Install azd and its AI connection/toolbox extensions first.' }
try {
    $settings = Invoke-QuietAzd (@('env', 'get-values', '--output', 'json') + $azdOptions) 'Read azd environment' |
        ConvertFrom-Json -AsHashtable
} catch { throw 'Cannot read the selected azd environment as JSON. Run azd env select and authenticate; values suppressed.' }
$subscription = Get-Setting 'AZURE_SUBSCRIPTION_ID'
$projectEndpoint = (Get-Setting 'FOUNDRY_PROJECT_ENDPOINT').TrimEnd('/')
$projectName = Get-Setting 'AZURE_AI_PROJECT_NAME'
$foundryGroup = Get-Setting 'AZURE_FOUNDRY_RESOURCE_GROUP'
$account = Get-Setting 'AZURE_AI_ACCOUNT_NAME'
$inventoryUrl = (Get-Setting 'INVENTORY_MCP_URL').TrimEnd('/')
$ordersUrl = (Get-Setting 'WORK_ORDERS_API_URL').TrimEnd('/')
$searchEndpoint = (Get-Setting 'AZURE_SEARCH_ENDPOINT').TrimEnd('/')
$search = Get-Setting 'AZURE_SEARCH_NAME' @('AZURE_SEARCH_SERVICE_NAME')
$inventoryKey = Get-Setting 'INVENTORY_API_KEY'
$ordersKey = Get-Setting 'WORK_ORDERS_API_KEY'
if ($inventoryKey.Length -lt 32 -or $ordersKey.Length -lt 32) {
    throw 'INVENTORY_API_KEY and WORK_ORDERS_API_KEY must each contain at least 32 characters, matching the protected deployments.'
}
$projectId = "/subscriptions/$subscription/resourceGroups/$foundryGroup/providers/Microsoft.CognitiveServices/accounts/$account/projects/$projectName"
if ($settings['AZURE_AI_PROJECT_ID'] -and $settings['AZURE_AI_PROJECT_ID'].TrimEnd('/') -ne $projectId) {
    throw 'AZURE_AI_PROJECT_ID does not match the subscription, Foundry resource group, account and project settings.'
}
Assert-HttpsEndpoint $projectEndpoint 'FOUNDRY_PROJECT_ENDPOINT'
Assert-HttpsEndpoint $inventoryUrl 'INVENTORY_MCP_URL'
Assert-HttpsEndpoint $ordersUrl 'WORK_ORDERS_API_URL'
Assert-HttpsEndpoint $searchEndpoint 'AZURE_SEARCH_ENDPOINT'
if ($searchEndpoint -ne "https://$search.search.windows.net") { throw 'Search name and endpoint do not match.' }
if (([uri] $projectEndpoint).AbsolutePath.TrimEnd('/') -ne "/api/projects/$projectName") {
    throw 'FOUNDRY_PROJECT_ENDPOINT must end with /api/projects/AZURE_AI_PROJECT_NAME.'
}
$help = Invoke-QuietAzd @('ai', 'connection', 'create', '--help') 'Check connections extension'
if ($help -notmatch '--custom-key' -or $help -notmatch 'project-managed-identity' -or $help -notmatch '--force') {
    throw 'Update the azd AI connections extension: custom-keys, project-managed-identity and --force are required.'
}
$null = Invoke-QuietAzd @('ai', 'toolbox', 'deploy', '--help') 'Check toolbox deploy extension'
$null = Invoke-QuietAzd @('ai', 'toolbox', 'publish', '--help') 'Check toolbox publish extension'
if ($CheckOnly) {
    Write-Host 'Configuration valid. No cloud requests or writes performed; service/spec checks require a real run.'
    return
}

# Fetch only the configured deployment's live spec. Disable redirects so its key cannot
# be forwarded to another host. Only the four approved work-order operations are exposed.
try {
    $spec = Invoke-RestMethod -Uri "$ordersUrl/openapi.json" -Headers @{ 'x-api-key' = $ordersKey } `
        -MaximumRedirection 0 -TimeoutSec 60 | ConvertTo-Json -Depth 100 | ConvertFrom-Json -AsHashtable
} catch { throw 'Cannot read the deployed /openapi.json. Check WORK_ORDERS_API_URL and its deployed API key; response suppressed.' }
if ($spec.openapi -notmatch '^3\.') { throw 'The live work-orders endpoint must serve an OpenAPI 3.x document.' }
$scheme = $spec.components.securitySchemes.APIKeyHeader
if ($scheme.type -ne 'apiKey' -or $scheme.in -ne 'header' -or $scheme.name -ne 'x-api-key') {
    throw 'The live spec must declare APIKeyHeader as an apiKey in header x-api-key. Redeploy the protected work-orders service.'
}
$paths = @{}
$operations = @(
    @{ Path = '/work-orders'; Method = 'get'; Id = 'list_work_orders' }
    @{ Path = '/work-orders/{work_order_id}'; Method = 'get'; Id = 'get_work_order' }
    @{ Path = '/work-orders'; Method = 'post'; Id = 'create_work_order' }
    @{ Path = '/work-orders/{work_order_id}'; Method = 'patch'; Id = 'update_work_order' }
)
foreach ($entry in $operations) {
    $item = $spec.paths[$entry.Path]
    if (-not $item) { throw "Live OpenAPI spec is missing path $($entry.Path)." }
    $operation = $item[$entry.Method]
    if (-not $operation) { throw "Live OpenAPI spec is missing $($entry.Method) $($entry.Path)." }
    # Stable IDs conform to Foundry's letters/hyphens/underscores restriction.
    $operation.operationId = $entry.Id
    $operation.security = @(@{ APIKeyHeader = @() })
    $operation.Remove('servers')
    if (-not $paths.ContainsKey($entry.Path)) {
        $paths[$entry.Path] = @{}
        if ($item.parameters) { $paths[$entry.Path].parameters = $item.parameters }
    }
    $paths[$entry.Path][$entry.Method] = $operation
}
$spec.paths = $paths
$spec.servers = @(@{ url = $ordersUrl })
$spec.security = @(@{ APIKeyHeader = @() })
$spec.components.securitySchemes = @{ APIKeyHeader = $scheme }
$spec.info.title = 'Fibey Work Orders'

$inventoryConnection = 'fibey-inventory-mcp'
$ordersConnection = 'fibey-work-orders-api'
$knowledgeConnection = 'kb-fibey-field-ops-kb'
$knowledgeUrl = "$searchEndpoint/knowledgebases/fibey-field-ops-kb/mcp?api-version=2026-08-01-preview"
$common = @('--project-endpoint', $projectEndpoint, '--output', 'json') + $azdOptions
# OpenAPI credentials are keyed by the HTTP header name, not the security scheme identifier.
$null = Invoke-QuietAzd (@(
    'ai', 'connection', 'create', $inventoryConnection, '--kind', 'remote-tool',
    '--target', $inventoryUrl, '--auth-type', 'custom-keys', '--custom-key', "x-api-key=$inventoryKey", '--force'
) + $common) 'Upsert inventory MCP credential connection'
$null = Invoke-QuietAzd (@(
    'ai', 'connection', 'create', $ordersConnection, '--kind', 'custom-keys',
    '--target', $ordersUrl, '--auth-type', 'custom-keys', '--custom-key', "x-api-key=$ordersKey", '--force'
) + $common) 'Upsert work-orders OpenAPI credential connection'
$null = Invoke-QuietAzd (@(
    'ai', 'connection', 'create', $knowledgeConnection, '--kind', 'remote-tool',
    '--target', $knowledgeUrl, '--auth-type', 'project-managed-identity',
    '--audience', 'https://search.azure.com/', '--metadata', 'ApiType=Azure', '--force'
) + $common) 'Upsert Foundry IQ identity connection'

$definition = @{
    name = 'fibey-toolbox'
    description = 'Fibey demo: inventory and network status, synthetic work orders, field knowledge.'
    tools = @(
        @{
            type = 'mcp'; server_label = 'inventory'
            project_connection_id = $inventoryConnection; require_approval = 'never'
        }
        @{
            type = 'openapi'
            openapi = @{
                name = 'work_orders'; spec = $spec
                auth = @{
                    type = 'project_connection'
                    security_scheme = @{ project_connection_id = "$projectId/connections/$ordersConnection" }
                }
            }
        }
        @{
            type = 'mcp'; server_label = 'field_knowledge'
            project_connection_id = $knowledgeConnection; require_approval = 'never'
            allowed_tools = @('knowledge_base_retrieve')
        }
    )
}
$renderDirectory = Join-Path (Join-Path $root '.azure') ("toolbox-render-" + [guid]::NewGuid().ToString('N'))
try {
    $null = New-Item -ItemType Directory -Path $renderDirectory -Force
    $rendered = Join-Path $renderDirectory 'toolbox.json'
    $definition | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $rendered -Encoding utf8
    # deploy upserts the full tool set, unlike create (new toolbox only) or connection add
    # (cannot update an inline OpenAPI spec). Publish explicitly on every successful rerun.
    $deployed = Invoke-QuietAzd (@('ai', 'toolbox', 'deploy', $rendered) + $common) 'Deploy toolbox definition' |
        ConvertFrom-Json -AsHashtable
    $version = $deployed.version
    if ($version -is [System.Collections.IDictionary]) { $version = $version.version }
    if ([string]::IsNullOrWhiteSpace($version)) { throw 'Toolbox deploy returned no version. Inspect azd ai toolbox versions list fibey-toolbox before publishing.' }
    $null = Invoke-QuietAzd (@('ai', 'toolbox', 'publish', 'fibey-toolbox', [string] $version) + $common) 'Publish toolbox default version'
    $shown = Invoke-QuietAzd (@('ai', 'toolbox', 'show', 'fibey-toolbox') + $common) 'Verify toolbox default version' |
        ConvertFrom-Json -AsHashtable
    if ($shown.toolbox.default_version -ne $version) { throw 'Toolbox default-version verification failed.' }
    $endpoint = "$projectEndpoint/toolboxes/fibey-toolbox/mcp?api-version=v1"
    foreach ($name in @('TOOLBOX_MCP_URL', 'TOOLBOX_ENDPOINT', 'TOOLBOX_FIBEY_TOOLBOX_MCP_ENDPOINT')) {
        $null = Invoke-QuietAzd (@('env', 'set', $name, $endpoint) + $azdOptions) "Save $name"
    }
    Write-Host "fibey-toolbox published at version $version."
    Write-Host "MCP endpoint: $endpoint"
} finally {
    if (Test-Path -LiteralPath $renderDirectory) { Remove-Item -LiteralPath $renderDirectory -Recurse -Force }
    $inventoryKey = $null
    $ordersKey = $null
    $settings = $null
}
