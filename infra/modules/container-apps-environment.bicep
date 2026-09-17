@description('Name of the Container Apps environment.')
param name string

@description('Azure region for the Container Apps environment.')
param location string

@description('Log Analytics workspace customer ID for Container Apps logs.')
param logAnalyticsWorkspaceCustomerId string

@secure()
@description('Log Analytics workspace shared key for Container Apps logs.')
param logAnalyticsWorkspaceSharedKey string

@description('Tags applied to the Container Apps environment.')
param tags object = {}

resource containerAppsEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspaceCustomerId
        sharedKey: logAnalyticsWorkspaceSharedKey
      }
    }
  }
}

@description('Resource ID of the Container Apps environment.')
output id string = containerAppsEnvironment.id

@description('Name of the Container Apps environment.')
output environmentName string = containerAppsEnvironment.name
