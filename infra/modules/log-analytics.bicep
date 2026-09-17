@description('Name of the Log Analytics workspace.')
param name string

@description('Azure region for the Log Analytics workspace.')
param location string

@description('Tags applied to the Log Analytics workspace.')
param tags object = {}

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
}

@description('Resource ID of the Log Analytics workspace.')
output id string = workspace.id

@description('Name of the Log Analytics workspace.')
output workspaceName string = workspace.name

@description('Customer ID for the Log Analytics workspace.')
output customerId string = workspace.properties.customerId

@secure()
@description('Primary shared key for the Log Analytics workspace.')
output sharedKey string = workspace.listKeys().primarySharedKey
