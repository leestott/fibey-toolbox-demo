@description('Name of the Azure AI Search service.')
param name string

@description('Azure region for the search service.')
param location string

@description('Tags applied to the search service.')
param tags object = {}

@description('SKU for the search service.')
@allowed(['basic', 'standard', 'standard2', 'standard3'])
param sku string = 'basic'

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    hostingMode: 'default'
    partitionCount: 1
    replicaCount: 1
    publicNetworkAccess: 'enabled'
    disableLocalAuth: true
    semanticSearch: 'standard'
  }
}

@description('Resource ID of the search service.')
output id string = searchService.id

@description('Name of the search service.')
output name string = searchService.name

@description('Endpoint URL of the search service.')
output endpoint string = 'https://${searchService.name}.search.windows.net'

@description('Principal ID for the search service managed identity.')
output principalId string = searchService.identity.principalId
