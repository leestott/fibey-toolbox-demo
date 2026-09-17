@description('Name of the Container App.')
param name string

@description('azd service name associated with the Container App.')
param serviceName string

@description('Azure region for the Container App.')
param location string

@description('Resource ID of the Container Apps environment.')
param environmentId string

@description('Container image to deploy.')
param containerImage string
param registryServer string

@description('Ingress target port for the container.')
param targetPort int

@description('Environment variables to inject into the container.')
param env array

@secure()
param secrets object = {}

param external bool = true
param healthPath string = '/health'

@description('Minimum replica count for the Container App.')
param minReplicas int = 1

@description('Maximum replica count for the Container App.')
param maxReplicas int = 3

@description('Tags applied to the Container App.')
param tags object = {}

var resolvedContainerImage = empty(containerImage) ? 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' : containerImage
var appTags = union(tags, {
  'azd-service-name': serviceName
})

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: name
  location: location
  tags: appTags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: external
        targetPort: empty(containerImage) ? 80 : targetPort
        transport: 'auto'
        allowInsecure: false
      }
      registries: [
        {
          server: registryServer
          identity: 'system'
        }
      ]
      secrets: [for secret in items(secrets): { name: secret.key, value: secrets[secret.key] }]
    }
    template: {
      containers: [
        {
          name: serviceName
          image: resolvedContainerImage
          env: env
          probes: empty(containerImage) ? [] : [
            {
              type: 'Readiness'
              httpGet: { path: healthPath, port: targetPort }
              initialDelaySeconds: 5
              periodSeconds: 10
            }
            {
              type: 'Liveness'
              httpGet: { path: healthPath, port: targetPort }
              initialDelaySeconds: 30
              periodSeconds: 30
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: minReplicas
        maxReplicas: maxReplicas
      }
    }
  }
}

@description('Resource ID of the Container App.')
output id string = containerApp.id

@description('Fully qualified domain name of the Container App ingress endpoint.')
output fqdn string = containerApp.properties.configuration.ingress.fqdn

output principalId string = containerApp.identity.principalId
