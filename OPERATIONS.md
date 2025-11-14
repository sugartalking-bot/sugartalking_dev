# Sugartalking Operations Reference

## Quick Commands

### Application Management
```bash
# Start application (scales to 1 replica, runs migrations)
./st_start

# Stop application (scales to 0 replicas)
./st_stop

# View logs
kubectl logs -f -l app=sugartalking
```

### Build and Deploy
```bash
# Full rebuild and deploy (builds Docker image, pushes to registry, deploys to k8s)
./scripts/build-and-deploy.sh

# Manual steps:
# 1. Build image
cmd.exe /c "docker build -t sugartalking:latest -f docker/Dockerfile ."

# 2. Tag for registry
cmd.exe /c "docker tag sugartalking:latest localhost:5001/sugartalking:latest"

# 3. Push to registry
cmd.exe /c "docker push localhost:5001/sugartalking:latest"

# 4. Apply k8s manifests
kubectl apply -f kubernetes/base/

# 5. Restart deployment
kubectl rollout restart deployment/sugartalking
kubectl rollout status deployment/sugartalking --timeout=120s
```

### Hot Reload (without rebuild - for quick code changes)
```bash
# Get pod name
POD_NAME=$(kubectl get pods -l app=sugartalking -o jsonpath='{.items[0].metadata.name}')

# Copy updated file(s) to pod
kubectl cp app/routes/api.py ${POD_NAME}:/app/app/routes/api.py
kubectl cp static/denon-control.js ${POD_NAME}:/app/static/denon-control.js

# Reload Gunicorn workers (sends HUP signal)
kubectl exec ${POD_NAME} -- sh -c "kill -HUP 1"
```

### Database Operations
```bash
POD_NAME=$(kubectl get pods -l app=sugartalking -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec ${POD_NAME} -- python scripts/migrate_all_commands.py

# Seed database
kubectl exec ${POD_NAME} -- python scripts/seed_database.py

# Run custom script
kubectl exec ${POD_NAME} -- python scripts/fix_toggle_commands.py

# Direct database query
kubectl exec -it sugar-talking-db -- psql -U denonuser -d denondb -c "SELECT * FROM receiver_commands LIMIT 10;"
```

### Pod Management
```bash
# Get pod status
kubectl get pods -l app=sugartalking

# Describe pod
kubectl describe pod -l app=sugartalking

# Get pod details
kubectl get pods -l app=sugartalking -o wide

# Execute shell in pod
kubectl exec -it $(kubectl get pods -l app=sugartalking -o jsonpath='{.items[0].metadata.name}') -- /bin/bash

# Scale replicas
kubectl scale deployment/sugartalking --replicas=1
kubectl scale deployment/sugartalking --replicas=0
```

### Debugging
```bash
# View real-time logs
kubectl logs -f -l app=sugartalking

# View last N lines
kubectl logs -l app=sugartalking --tail=100

# Check deployment status
kubectl rollout status deployment/sugartalking

# Get events
kubectl get events --sort-by='.lastTimestamp' | grep sugartalking

# Port forward (if ingress not working)
kubectl port-forward deployment/sugartalking 5000:5000
```

### Database Management
```bash
# Connect to database pod
kubectl exec -it sugar-talking-db -- psql -U denonuser -d denondb

# Common queries
# - List all tables
\dt

# - View all receivers
SELECT * FROM receivers;

# - View all commands for a receiver
SELECT r.model, c.action_name, c.command_template
FROM receiver_commands c
JOIN receivers r ON c.receiver_id = r.id
WHERE r.model = 'AVR-X2300W';

# - Count commands by type
SELECT action_type, COUNT(*)
FROM receiver_commands c
JOIN receivers r ON c.receiver_id = r.id
WHERE r.model = 'AVR-X2300W'
GROUP BY action_type;
```

### Testing API Endpoints
```bash
# Health check
curl http://localhost:5000/api/health

# Get status
curl "http://localhost:5000/api/status?receiver_ip=192.168.1.182"

# Power on
curl -X POST http://localhost:5000/api/power/on \
  -H "Content-Type: application/json" \
  -d '{"receiver_ip":"192.168.1.182"}'

# Set volume
curl -X POST http://localhost:5000/api/volume/set \
  -H "Content-Type: application/json" \
  -d '{"value":-30}'

# Mute
curl -X POST http://localhost:5000/api/volume/mute \
  -H "Content-Type: application/json" \
  -d '{"mute_state":false}'
```

## Common Issues

### Docker not available in WSL
**Problem**: `docker: command not found` in WSL
**Solution**: Use `cmd.exe /c "docker ..."` to run Docker commands through Windows

### PowerShell execution policy
**Problem**: Cannot run `.ps1` scripts
**Solution**: Use manual kubectl/docker commands or use bash scripts instead

### Pod stuck in pending
```bash
# Check what's wrong
kubectl describe pod -l app=sugartalking

# Common fixes:
# - Check if PVC is bound: kubectl get pvc
# - Check if image is available: kubectl describe pod -l app=sugartalking | grep -A 5 Events
```

### Changes not reflecting
1. For code changes: Use hot reload (copy + HUP signal)
2. For dependencies: Full rebuild required
3. For database: Run migration scripts
4. For config: `kubectl rollout restart deployment/sugartalking`

## Application URLs
- Main UI: http://localhost:5000
- API Health: http://localhost:5000/api/health
- API Config: http://localhost:5000/api/config

## File Locations in Pod
- Application code: `/app/app/`
- Static files: `/app/static/`
- Scripts: `/app/scripts/`
- Data directory: `/data/`
- Logs: `/data/logs/`

## Environment Variables
Set in `kubernetes/base/configmap.yaml`:
- `RECEIVER_IP`: Default receiver IP (192.168.1.182)
- `DATABASE_URL`: PostgreSQL connection string
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)
- `AUTO_REPORT_ERRORS`: Enable/disable error reporting

## Architecture Notes
- **Runtime**: Gunicorn with 2 workers, 4 threads each
- **Database**: PostgreSQL in separate pod (sugar-talking-db)
- **Image Registry**: Local registry at localhost:5001
- **Kubernetes**: Deployment with 1 replica, PVC for data persistence
- **Networking**: Ingress on port 5000
