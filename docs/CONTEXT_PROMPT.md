# Sugartalking Development Context Prompt

## Purpose

This document provides a comprehensive prompt you can use to bring Claude (or another AI) up to speed on the Sugartalking project in a new conversation session. Copy and paste this into a fresh chat to continue development.

---

## 📋 COPY THIS PROMPT FOR NEW SESSIONS ⬇️

```
I need help continuing development on the Sugartalking project - a universal web-based control interface for Audio/Video Receivers (AVRs). Here's the complete context:

## Project Overview

**Name**: Sugartalking (branded name) / denon_avr_x2300w_webGUI (repo name)
**Purpose**: Kubernetes-deployable web application for controlling AVRs from multiple manufacturers
**Version**: 2.0.0
**Primary Language**: Python 3.11
**Framework**: Flask with Gunicorn
**Database**: SQLite
**Deployment**: Docker + Kubernetes

## Architecture

**Database-Driven Command System**:
- Receiver models and their commands stored in SQLite database
- `Receiver` table: manufacturer, model, protocol, default port
- `Command` table: action type, endpoint, HTTP method, command template
- `CommandParameter` table: parameter specs with validation
- `DiscoveredReceiver` table: auto-discovered devices on network
- `ErrorLog` table: error tracking for auto-reporting

**Key Features**:
1. **Multi-Receiver Support**: Single GUI works with any configured receiver model
2. **Auto-Discovery**: mDNS and HTTP probing to find receivers on LAN
3. **Auto-Error Reporting**: Bugs automatically reported to GitHub Issues
4. **Admin Panel**: Web UI for managing receivers and commands
5. **Network Scanning**: Automatic device detection on local network

## Directory Structure

```
denon_avr_x2300w_webGUI/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── models.py             # SQLAlchemy database models
│   ├── routes/
│   │   ├── api.py           # REST API endpoints
│   │   ├── admin.py         # Admin panel routes
│   │   └── web.py           # Frontend serving
│   └── services/
│       ├── command_executor.py    # Execute commands via database
│       ├── discovery.py           # Network auto-discovery (mDNS + HTTP)
│       └── error_reporter.py      # GitHub Issues integration
├── static/
│   └── index.html           # Frontend web UI
├── scripts/
│   └── seed_database.py     # Database seeding with Denon X2300W
├── docker/
│   ├── Dockerfile          # Multi-stage build with Gunicorn
│   ├── docker-compose.yml  # Local testing setup
│   └── .dockerignore
├── kubernetes/
│   ├── base/
│   │   ├── deployment.yaml  # Main app deployment
│   │   ├── service.yaml     # ClusterIP service
│   │   ├── configmap.yaml   # App configuration
│   │   ├── secret-template.yaml  # GitHub token template
│   │   ├── persistentvolumeclaim.yaml  # Storage for DB/logs
│   │   └── ingress.yaml     # Optional ingress
│   ├── installer.sh         # Linux/macOS installer
│   └── installer.ps1        # Windows PowerShell installer
├── docs/
│   ├── ADDING_RECEIVERS.md  # Guide for adding new receiver models
│   ├── PHASE4_DOC_PARSER.md # Future: AI doc parsing architecture
│   ├── GITHUB_BOT_SETUP.md  # GitHub bot account setup
│   └── CONTEXT_PROMPT.md    # This file
├── wsgi.py                  # Gunicorn entry point
├── requirements.txt
├── .gitignore
└── README.md

OLD FILES (to be removed):
├── app.py                  # Legacy Flask app
├── main.py                 # Legacy CLI tool
├── lib/                    # Legacy command library
├── poc/                    # Proof-of-concept (duplicate code)
└── config/                 # Old config files
```

## Technology Stack

**Backend**:
- Flask 3.0+ (web framework)
- Gunicorn (WSGI server)
- SQLAlchemy 2.0+ (ORM)
- zeroconf (mDNS discovery)
- requests (HTTP client)

**Deployment**:
- Docker multi-stage builds
- Kubernetes (tested on homelab)
- Host network mode (to access LAN devices)

**Development**:
- pytest (testing)
- alembic (migrations, if needed)

## Current Status

**Completed (Phase 1-3)**:
✅ Database schema designed and implemented
✅ Command executor using database-driven approach
✅ Network auto-discovery (mDNS + HTTP probing)
✅ GitHub auto-error reporting
✅ Admin panel for database management
✅ Kubernetes manifests (Deployment, Service, ConfigMap, Secret, PVC, Ingress)
✅ Docker setup with multi-stage build
✅ Installer scripts for Linux/macOS and Windows
✅ Denon AVR-X2300W fully seeded in database
✅ Documentation for adding new receivers

**Not Yet Done**:
❌ Frontend update for receiver selection/discovery
❌ Move static files to proper location
❌ Clean up old files (app.py, main.py, lib/, poc/)
❌ Test Docker build
❌ Build and push Docker images (AMD64 + ARM64)
❌ Update README.md
❌ Final testing

**Future (Phase 4)**:
- AI-powered documentation parser
- Automatic command extraction from PDFs/docs

## Key Decisions Made

1. **SQLite over PostgreSQL**: Single-instance use case, embedded DB is simpler
2. **Database-driven commands**: Makes adding receivers easy without code changes
3. **Bot account for error reporting**: Zero user config required
4. **Host network mode**: Required for LAN device discovery
5. **Single replica**: Homelab use, no need for HA
6. **Opt-in philosophy changed to auto-enabled**: Error reporting enabled by default

## Configuration

**Environment Variables**:
- `DATA_DIR=/data` - Database and logs location
- `LOG_LEVEL=INFO` - Logging verbosity
- `GITHUB_TOKEN` - Personal access token for error reporting (from Secret)
- `GITHUB_REPO=builderOfTheWorlds/denon_avr_x2300w_webGUI`
- `AUTO_REPORT_ERRORS=true` - Enable/disable auto-reporting

**Kubernetes ConfigMap**:
See `kubernetes/base/configmap.yaml`

**Kubernetes Secret** (needs user to create):
GitHub bot token for issue creation

## Example API Usage

```bash
# Health check
curl http://localhost:5000/api/health

# Discover receivers
curl -X POST http://localhost:5000/api/discover \
  -H "Content-Type: application/json" \
  -d '{"method": "both", "duration": 5}'

# Power on
curl -X POST http://localhost:5000/api/power/on \
  -H "Content-Type: application/json" \
  -d '{"receiver_ip": "192.168.1.182", "receiver_model": "AVR-X2300W"}'

# Get available commands
curl http://localhost:5000/api/commands/AVR-X2300W
```

## Testing Denon AVR-X2300W

The original receiver that prompted this project:
- IP: 192.168.1.182
- Model: Denon AVR-X2300W
- Protocol: HTTP on port 80
- Working commands: power on/off via `/MainZone/index.put.asp`

## Development Workflow

1. **Database changes**: Update models.py, create migration if needed
2. **New receiver**: Create seed script in `scripts/`, run it
3. **New feature**: Add route in `app/routes/`, service in `app/services/`
4. **Testing**: Use docker-compose for local testing before K8s
5. **Deployment**: Build Docker image, push to registry, update K8s

## Common Tasks

**Add a new receiver**:
See `docs/ADDING_RECEIVERS.md`

**Update Kubernetes deployment**:
```bash
kubectl apply -f kubernetes/base/
kubectl rollout restart deployment/sugartalking
```

**View logs**:
```bash
kubectl logs -l app=sugartalking -f
```

**Access admin panel**:
```bash
kubectl port-forward svc/sugartalking 5000:80
# Visit http://localhost:5000/admin
```

## Important Notes

- **Host network required**: App needs access to LAN for device discovery
- **Single instance**: Database is SQLite, no concurrent writes
- **Error reporting**: Requires GitHub bot account setup (see GITHUB_BOT_SETUP.md)
- **Security**: Non-root user (uid 1000) in container
- **Persistence**: PVC for database and logs

## Known Issues / TODOs

1. Frontend still references old single-receiver model
2. Old files (app.py, main.py, lib/, poc/) need to be removed
3. Docker image not yet built/pushed
4. Multi-arch build (AMD64 + ARM64) not tested
5. README needs complete rewrite for v2.0

## Repository

**GitHub**: builderOfTheWorlds/denon_avr_x2300w_webGUI
**Branch**: claude/kubernetes-refactor-011CUw13kGUFxwooo5Fto8t9
**Main Branch**: (to be determined)

## Questions to Help Me

When asking for help, please specify:
1. What are you trying to accomplish?
2. Which component needs work (frontend, backend, K8s, Docker, docs)?
3. Any specific error messages or issues?
4. Testing environment (local Docker, K8s, etc.)?

## Next Steps

The most urgent remaining tasks are:
1. Update frontend for multi-receiver support
2. Clean up old files
3. Test Docker build
4. Build multi-arch images
5. Update README

That's the complete context! What would you like to work on?
```

---

## How to Use This Prompt

### Starting a New Session

1. **Copy everything between the ``` marks above**
2. **Paste into a new Claude conversation**
3. **Add your specific request**, for example:
   - "I want to update the frontend to support receiver selection"
   - "Help me build and push the Docker images"
   - "I need to add support for a Yamaha receiver"

### Example Usage

```
[Paste the context prompt above]

Additionally, I want to add support for the Yamaha RX-V685 receiver.
I have the API documentation at: [URL or attach PDF]
Please help me create a seed script and test it.
```

### Updating This Prompt

As the project evolves, update this document with:
- New features added
- Architectural changes
- Updated directory structure
- New dependencies
- Lessons learned

### For Major Changes

If you make significant changes to the architecture:

1. Update this file first
2. Document the "why" behind decisions
3. Include migration paths from old to new
4. Update examples and common tasks

## Tips for Effective Prompting

### ✅ Good Prompts

- "Add support for Onkyo TX-NR696 using the seed script pattern"
- "Fix the auto-discovery service - it's not detecting my receiver at 192.168.1.100"
- "Update the frontend to show a dropdown of discovered receivers"

### ❌ Vague Prompts

- "Make it better"
- "Fix the bugs"
- "Add more features"

### Pro Tips

1. **Include error messages**: Paste full error logs
2. **Specify environment**: Docker/K8s/local, OS, etc.
3. **Describe desired behavior**: What should happen vs what's happening
4. **Reference files**: "In `app/services/discovery.py` line 123..."

## Version History

- **v2.0.0** (2025-11-08): Complete Kubernetes refactor, database-driven commands, auto-discovery
- **v1.0.0** (2025): Initial POC with Denon X2300W hardcoded

## Related Documentation

- `ADDING_RECEIVERS.md` - How to add new receiver models
- `PHASE4_DOC_PARSER.md` - Future AI documentation parser
- `GITHUB_BOT_SETUP.md` - Setting up auto-error reporting
- `README.md` - Project overview (needs update)

---

**Last Updated**: 2025-11-08
**Maintainer**: Use this prompt freely to continue development with Claude or share with other developers.
