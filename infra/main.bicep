targetScope = 'subscription'

param environmentName string
param location string
param resourceGroupName string
param registryResourceId string
param foundryAccountName string
param foundryProjectName string
param foundryProjectEndpoint string
param foundryModel string
param toolboxMcpUrl string
param uiClientId string
param allowedUserId string

@secure()
param uiClientSecret string

@secure()
param inventoryApiKey string

@secure()
param workOrdersApiKey string

param uiImageName string = ''
param gatewayImageName string = ''
param inventoryMcpImageName string = ''
param workOrdersApiImageName string = ''
param statusDashboardImageName string = ''

resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' existing = {
  name: resourceGroupName
}

module apps 'apps.bicep' = {
  name: '${environmentName}-apps'
  scope: resourceGroup
  params: {
    environmentName: environmentName
    location: location
    registryResourceId: registryResourceId
    foundryAccountName: foundryAccountName
    foundryProjectName: foundryProjectName
    foundryProjectEndpoint: foundryProjectEndpoint
    foundryModel: foundryModel
    toolboxMcpUrl: toolboxMcpUrl
    uiClientId: uiClientId
    allowedUserId: allowedUserId
    uiClientSecret: uiClientSecret
    inventoryApiKey: inventoryApiKey
    workOrdersApiKey: workOrdersApiKey
    uiImageName: uiImageName
    gatewayImageName: gatewayImageName
    inventoryMcpImageName: inventoryMcpImageName
    workOrdersApiImageName: workOrdersApiImageName
    statusDashboardImageName: statusDashboardImageName
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroup.name
output AZURE_CONTAINER_REGISTRY_NAME string = last(split(registryResourceId, '/'))
output WEB_URL string = 'https://${apps.outputs.uiFqdn}'
output GATEWAY_URL string = 'https://${apps.outputs.gatewayFqdn}'
output INVENTORY_MCP_URL string = 'https://${apps.outputs.inventoryMcpFqdn}/mcp'
output WORK_ORDERS_API_URL string = 'https://${apps.outputs.workOrdersApiFqdn}'
output STATUS_DASHBOARD_URL string = 'https://${apps.outputs.statusDashboardFqdn}'
output AZURE_STORAGE_ACCOUNT_NAME string = apps.outputs.storageAccountName
output AZURE_SEARCH_SERVICE_NAME string = apps.outputs.searchServiceName
output AZURE_SEARCH_ENDPOINT string = apps.outputs.searchServiceEndpoint
