@description('Unique environment name used for resource naming.')
param environmentName string

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Tags applied to all resources.')
param tags object = {
  'azd-env-name': environmentName
}

@description('Container image for the ui service.')
param uiImageName string = ''

@description('Container image for the gateway service.')
param gatewayImageName string = ''

@description('Container image for the inventory-mcp service.')
param inventoryMcpImageName string = ''

@description('Container image for the work-orders-api service.')
param workOrdersApiImageName string = ''

@description('Container image for the status-dashboard service.')
param statusDashboardImageName string = ''

@description('Azure AI Foundry project endpoint used by the gateway.')
param foundryProjectEndpoint string = ''

@description('Azure AI Foundry model deployment name used by the gateway.')
param foundryModel string = ''

@description('Foundry Toolbox MCP endpoint used by the gateway.')
param toolboxMcpUrl string = ''

param registryResourceId string
param foundryAccountName string
param foundryProjectName string
param uiClientId string
param allowedUserId string

@secure()
param uiClientSecret string

@secure()
@minLength(32)
param inventoryApiKey string

@secure()
@minLength(32)
param workOrdersApiKey string

var resourceToken = toLower(uniqueString(subscription().subscriptionId, resourceGroup().id, environmentName))
var sanitizedEnvironmentName = replace(toLower(environmentName), '-', '')

var containerAppsEnvironmentName = '${environmentName}-cae'
var logAnalyticsWorkspaceName = '${environmentName}-logs'
var registryName = last(split(registryResourceId, '/'))
var storageAccountName = 'st${take(sanitizedEnvironmentName, 10)}${take(resourceToken, 12)}'
var searchServiceName = '${environmentName}-search'

var uiAppName = '${environmentName}-ui'
var gatewayAppName = '${environmentName}-gateway'
var inventoryMcpAppName = '${take(environmentName, 22)}-inventory'
var workOrdersApiAppName = '${take(environmentName, 25)}-orders'
var statusDashboardAppName = '${take(environmentName, 25)}-status'

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'log-analytics'
  params: {
    name: logAnalyticsWorkspaceName
    location: location
    tags: tags
  }
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: registryName
}

module storageAccount 'modules/storage-account.bicep' = {
  name: 'storage-account'
  params: {
    name: storageAccountName
    location: location
    tags: tags
  }
}

module aiSearch 'modules/ai-search.bicep' = {
  name: 'ai-search'
  params: {
    name: searchServiceName
    location: location
    tags: tags
    sku: 'basic'
  }
}

// Grant AI Search managed identity "Storage Blob Data Reader" on the storage account
resource storageAccountRef 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageAccountName
}

resource searchBlobReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccountRef.id, searchServiceName, 'Storage Blob Data Reader')
  scope: storageAccountRef
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
    principalId: aiSearch.outputs.principalId
    principalType: 'ServicePrincipal'
  }
}

module containerAppsEnvironment 'modules/container-apps-environment.bicep' = {
  name: 'container-apps-environment'
  params: {
    name: containerAppsEnvironmentName
    location: location
    logAnalyticsWorkspaceCustomerId: logAnalytics.outputs.customerId
    logAnalyticsWorkspaceSharedKey: logAnalytics.outputs.sharedKey
    tags: tags
  }
}

module inventoryMcp 'modules/container-app.bicep' = {
  name: 'inventory-mcp-app'
  params: {
    name: inventoryMcpAppName
    serviceName: 'inventory-mcp'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: inventoryMcpImageName
    registryServer: containerRegistry.properties.loginServer
    targetPort: 8001
    env: [
      { name: 'API_KEY', secretRef: 'api-key' }
      { name: 'REQUIRE_API_KEY', value: 'true' }
      { name: 'STATUS_DASHBOARD_URL', value: 'https://${statusDashboard.outputs.fqdn}' }
    ]
    secrets: { 'api-key': inventoryApiKey }
    healthPath: '/health'
    maxReplicas: 1
    tags: tags
  }
}

module workOrdersApi 'modules/container-app.bicep' = {
  name: 'work-orders-api-app'
  params: {
    name: workOrdersApiAppName
    serviceName: 'work-orders-api'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: workOrdersApiImageName
    registryServer: containerRegistry.properties.loginServer
    targetPort: 8002
    env: [
      { name: 'API_KEY', secretRef: 'api-key' }
      { name: 'REQUIRE_API_KEY', value: 'true' }
    ]
    secrets: { 'api-key': workOrdersApiKey }
    healthPath: '/health'
    maxReplicas: 1
    tags: tags
  }
}

module statusDashboard 'modules/container-app.bicep' = {
  name: 'status-dashboard-app'
  params: {
    name: statusDashboardAppName
    serviceName: 'status-dashboard'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: statusDashboardImageName
    registryServer: containerRegistry.properties.loginServer
    targetPort: 8003
    env: []
    external: false
    healthPath: '/healthz'
    tags: tags
  }
}

module gateway 'modules/container-app.bicep' = {
  name: 'gateway-app'
  params: {
    name: gatewayAppName
    serviceName: 'gateway'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: gatewayImageName
    registryServer: containerRegistry.properties.loginServer
    targetPort: 8000
    external: false
    maxReplicas: 1
    healthPath: '/api/health'
    env: [
      { name: 'AGENT_MODE', value: 'hosted' }
      { name: 'HOSTED_AGENT_ENDPOINT', value: foundryProjectEndpoint }
      { name: 'HOSTED_AGENT_NAME', value: 'fibey-agent' }
      { name: 'AZURE_TENANT_ID', value: tenant().tenantId }
      {
        name: 'FOUNDRY_PROJECT_ENDPOINT'
        value: foundryProjectEndpoint
      }
      {
        name: 'FOUNDRY_MODEL'
        value: foundryModel
      }
      {
        name: 'TOOLBOX_MCP_URL'
        value: toolboxMcpUrl
      }
      {
        name: 'INVENTORY_MCP_URL'
        value: 'https://${inventoryMcp.outputs.fqdn}'
      }
      {
        name: 'WORK_ORDERS_API_URL'
        value: 'https://${workOrdersApi.outputs.fqdn}'
      }
      {
        name: 'STATUS_DASHBOARD_URL'
        value: 'https://${statusDashboard.outputs.fqdn}'
      }
    ]
    tags: tags
  }
}

module ui 'modules/container-app.bicep' = {
  name: 'ui-app'
  params: {
    name: uiAppName
    serviceName: 'ui'
    location: location
    environmentId: containerAppsEnvironment.outputs.id
    containerImage: uiImageName
    registryServer: containerRegistry.properties.loginServer
    targetPort: 80
    env: [
      { name: 'GATEWAY_URL', value: 'https://${gateway.outputs.fqdn}/api/' }
      { name: 'GATEWAY_HOST', value: gateway.outputs.fqdn }
    ]
    secrets: { 'ui-client-secret': uiClientSecret }
    healthPath: '/'
    tags: tags
  }
}

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource foundryProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: foundryAccount
  name: foundryProjectName
}

module access 'modules/access.bicep' = {
  name: 'application-access'
  params: {
    registryName: registryName
    foundryAccountName: foundryAccountName
    foundryProjectName: foundryProjectName
    searchName: aiSearch.outputs.name
    storageName: storageAccount.outputs.name
    operatorPrincipalId: allowedUserId
    foundryPrincipalId: foundryProject.identity.principalId
    gatewayPrincipalId: gateway.outputs.principalId
    appPrincipals: [
      inventoryMcp.outputs.principalId
      workOrdersApi.outputs.principalId
      statusDashboard.outputs.principalId
      gateway.outputs.principalId
      ui.outputs.principalId
    ]
  }
}

resource uiRef 'Microsoft.App/containerApps@2025-07-01' existing = {
  name: uiAppName
}

resource uiAuth 'Microsoft.App/containerApps/authConfigs@2025-07-01' = {
  parent: uiRef
  name: 'current'
  properties: {
    platform: { enabled: true }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureactivedirectory'
    }
    httpSettings: { requireHttps: true }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: uiClientId
          clientSecretSettingName: 'ui-client-secret'
          openIdIssuer: '${environment().authentication.loginEndpoint}${tenant().tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [uiClientId]
          defaultAuthorizationPolicy: {
            allowedPrincipals: { identities: [allowedUserId] }
          }
        }
      }
    }
  }
  dependsOn: [ui]
}

@description('Fully qualified domain name for the ui container app.')
output uiFqdn string = ui.outputs.fqdn

@description('Fully qualified domain name for the gateway container app.')
output gatewayFqdn string = gateway.outputs.fqdn

@description('Fully qualified domain name for the inventory-mcp container app.')
output inventoryMcpFqdn string = inventoryMcp.outputs.fqdn

@description('Fully qualified domain name for the work-orders-api container app.')
output workOrdersApiFqdn string = workOrdersApi.outputs.fqdn

@description('Fully qualified domain name for the status-dashboard container app.')
output statusDashboardFqdn string = statusDashboard.outputs.fqdn

@description('Storage account name for FoundryIQ documents.')
output storageAccountName string = storageAccount.outputs.name

@description('Azure AI Search service name.')
output searchServiceName string = aiSearch.outputs.name

@description('Azure AI Search endpoint.')
output searchServiceEndpoint string = aiSearch.outputs.endpoint

@description('Container registry login server used for service images.')
output registryLoginServer string = containerRegistry.properties.loginServer
