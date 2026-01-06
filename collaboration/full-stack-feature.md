# Full Stack Feature

Multi-agent collaboration for implementing a feature with API, infrastructure, and deployment.

## Overview

Use this template when building features that span:
- Python backend/API development
- Cloud infrastructure (AWS/GCP)
- Containerization and deployment
- Kubernetes orchestration

## Agent Sequence

```
┌─────────────────────────────────────────────────────────────┐
│  1. Python Developer                                        │
│     └── Implement API/service logic                         │
├─────────────────────────────────────────────────────────────┤
│  2. AWS Specialist                                          │
│     └── Provision cloud resources (IaC)                     │
├─────────────────────────────────────────────────────────────┤
│  3. Container Specialist                                    │
│     └── Create optimized Dockerfile                         │
├─────────────────────────────────────────────────────────────┤
│  4. Kubernetes Specialist                                   │
│     └── Deployment manifests, Helm charts                   │
├─────────────────────────────────────────────────────────────┤
│  5. Documenter                                              │
│     └── API docs, deployment guide                          │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: API Development (python-developer)

### Input
- Feature requirements
- API specifications (OpenAPI/Swagger)
- Integration requirements

### Tasks
1. Implement API endpoints
2. Add business logic
3. Write unit and integration tests
4. Configure environment handling
5. Add health checks and metrics

### Output
```
src/
├── api/
│   ├── routes.py
│   └── handlers.py
├── services/
│   └── feature_service.py
├── models/
│   └── schemas.py
└── tests/
    ├── test_api.py
    └── test_service.py
```

### Quality Gate
- [ ] All endpoints have tests
- [ ] Input validation implemented
- [ ] Error responses follow standard format

## Phase 2: Infrastructure (aws-specialist)

### Input
- Resource requirements from Phase 1
- Security/compliance requirements
- Cost constraints

### Tasks
1. Design cloud architecture
2. Write Terraform/CloudFormation
3. Configure networking (VPC, security groups)
4. Set up secrets management
5. Configure monitoring/logging

### Output
```
infrastructure/
├── main.tf
├── variables.tf
├── outputs.tf
└── modules/
    ├── networking/
    ├── compute/
    └── storage/
```

### Quality Gate
- [ ] Infrastructure is reproducible
- [ ] Secrets not hardcoded
- [ ] Cost estimate reviewed

## Phase 3: Containerization (container-specialist)

### Input
- Application code from Phase 1
- Runtime requirements
- Security policies

### Tasks
1. Create multi-stage Dockerfile
2. Optimize image size
3. Configure health checks
4. Set up non-root user
5. Add security scanning

### Output
```
Dockerfile
.dockerignore
docker-compose.yaml (for local dev)
```

### Quality Gate
- [ ] Image size minimized
- [ ] No security vulnerabilities (HIGH/CRITICAL)
- [ ] Runs as non-root user

## Phase 4: Kubernetes Deployment (kubernetes-specialist)

### Input
- Container from Phase 3
- Infrastructure outputs from Phase 2
- Scaling requirements

### Tasks
1. Create Deployment manifests
2. Configure Services and Ingress
3. Set up HPA for autoscaling
4. Add ConfigMaps and Secrets
5. Create Helm chart (optional)

### Output
```
k8s/
├── deployment.yaml
├── service.yaml
├── ingress.yaml
├── configmap.yaml
├── hpa.yaml
└── helm/
    └── feature-chart/
```

### Quality Gate
- [ ] Resource limits defined
- [ ] Liveness/readiness probes configured
- [ ] Scaling policies appropriate

## Phase 5: Documentation (documenter)

### Input
- All artifacts from Phases 1-4

### Tasks
1. Write API documentation
2. Create deployment guide
3. Document infrastructure
4. Add troubleshooting guide

### Output
```
docs/
├── api-reference.md
├── deployment-guide.md
├── architecture.md
└── troubleshooting.md
```

## Handoff Protocol

Each handoff includes:
1. **Artifacts created**: Files and their purposes
2. **Configuration needed**: Environment variables, secrets
3. **Dependencies**: What the next phase needs from this one
4. **Decisions log**: Choices made and why

## Parallel Execution Option

Phases 2-4 can run in parallel after Phase 1:

```
                    → AWS Specialist →
Python Developer →  → Container Specialist →  → Documenter
                    → Kubernetes Specialist →
```

This reduces total time but requires coordination on:
- Container registry location (AWS ↔ K8s)
- Network configuration (AWS ↔ K8s)
- Image name/tag (Container ↔ K8s)
