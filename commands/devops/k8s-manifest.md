---
description: Generate Kubernetes manifests for an application
argument-hint: <application name> [options]
---

# K8s Manifest

Generate Kubernetes manifests for deploying data applications.

## Usage

```
/k8s-manifest <application name> [options]
```

## Options

- `--replicas <n>`: Number of replicas (default: 2)
- `--namespace <ns>`: Target namespace
- `--ingress`: Include ingress configuration
- `--hpa`: Include horizontal pod autoscaler
- `--pdb`: Include pod disruption budget
- `--secrets`: Include secrets template
- `--helm`: Generate as Helm chart

## Generated Resources

### Basic Set
- Deployment or StatefulSet
- Service (ClusterIP or LoadBalancer)
- ConfigMap
- ServiceAccount

### With Options
- Ingress (--ingress)
- HorizontalPodAutoscaler (--hpa)
- PodDisruptionBudget (--pdb)
- Secret (--secrets)
- NetworkPolicy

## Workload Types

### Deployment (Default)
For stateless applications:
- Web servers
- API services
- Workers

### StatefulSet
For stateful applications:
- Databases
- Message queues
- Applications requiring stable network identity

### Job / CronJob
For batch workloads:
- ETL jobs
- Data processing
- Scheduled tasks

## Example Output

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-pipeline
  labels:
    app: data-pipeline
spec:
  replicas: 2
  selector:
    matchLabels:
      app: data-pipeline
  template:
    metadata:
      labels:
        app: data-pipeline
    spec:
      containers:
        - name: data-pipeline
          image: data-pipeline:latest
          ports:
            - containerPort: 8080
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
          envFrom:
            - configMapRef:
                name: data-pipeline-config
            - secretRef:
                name: data-pipeline-secrets
```

## Best Practices Applied

- Resource requests AND limits
- Liveness and readiness probes
- Non-root security context
- ConfigMaps for configuration
- Secrets for sensitive data
- Labels for identification
