param registryName string
param foundryAccountName string
param foundryProjectName string
param searchName string
param foundryPrincipalId string
param gatewayPrincipalId string
param appPrincipals array
param storageName string
param operatorPrincipalId string

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: registryName
}

resource registryPullRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for principal in appPrincipals: {
    name: guid(registry.id, principal, 'acrpull')
    scope: registry
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
      principalId: principal
      principalType: 'ServicePrincipal'
    }
  }
]

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: foundryAccountName
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' existing = {
  parent: account
  name: foundryProjectName
}

resource gatewayFoundryRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(project.id, gatewayPrincipalId, 'foundry-user')
  scope: project
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '53ca6127-db72-4b80-b1b0-d745d6d5456d')
    principalId: gatewayPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource search 'Microsoft.Search/searchServices@2024-06-01-preview' existing = {
  name: searchName
}

resource searchReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(search.id, foundryPrincipalId, 'search-reader')
  scope: search
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '1407120a-92aa-4202-b7e9-c0e197c71c8f')
    principalId: foundryPrincipalId
    principalType: 'ServicePrincipal'
  }
}

resource operatorSearchRoles 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for roleId in [
    '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
  ]: {
    name: guid(search.id, operatorPrincipalId, roleId)
    scope: search
    properties: {
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
      principalId: operatorPrincipalId
      principalType: 'User'
    }
  }
]

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = {
  name: storageName
}

resource operatorBlobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storage.id, operatorPrincipalId, 'blob-contributor')
  scope: storage
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: operatorPrincipalId
    principalType: 'User'
  }
}
