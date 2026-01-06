---
description: Generate deployment configuration for data applications
argument-hint: <application> to <environment>
agent: kubernetes-specialist
---

# Deploy

Generate deployment configuration and scripts for data applications.

## Usage

```
/deploy <application> to <environment> [--platform <platform>]
```

## Platforms

- **kubernetes**: K8s manifests and Helm charts
- **ecs**: AWS ECS task definitions
- **lambda**: AWS Lambda deployment
- **airflow**: Airflow deployment (MWAA, Astronomer)

## Environments

- **dev**: Development environment
- **staging**: Staging/QA environment
- **prod**: Production environment

## Generated Files

### Kubernetes
```
deploy/
├── kubernetes/
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   └── ingress.yaml
└── helm/
    ├── Chart.yaml
    ├── values.yaml
    ├── values-dev.yaml
    ├── values-staging.yaml
    ├── values-prod.yaml
    └── templates/
```

### AWS ECS
```
deploy/
├── ecs/
│   ├── task-definition.json
│   ├── service.json
│   └── appspec.yaml
└── terraform/
    ├── main.tf
    ├── ecs.tf
    └── variables.tf
```

### AWS Lambda
```
deploy/
├── lambda/
│   ├── template.yaml (SAM)
│   └── requirements.txt
└── terraform/
    ├── main.tf
    ├── lambda.tf
    └── iam.tf
```

## Configuration

Generates environment-specific configurations:

- Resource sizing (CPU, memory)
- Replica counts
- Environment variables
- Secrets references
- Health checks
- Scaling policies

## Example

```
/deploy etl-pipeline to prod --platform kubernetes
```

Generates:
- Kubernetes deployment with production settings
- ConfigMap for environment config
- Secrets for credentials
- Service for internal access
- HPA for auto-scaling
- PDB for high availability
