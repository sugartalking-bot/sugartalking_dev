# 🎛️ Sugartalking

**Universal Web-Based Control for Audio/Video Receivers**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/builderOfTheWorlds/denon_avr_x2300w_webGUI)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Kubernetes](https://img.shields.io/badge/kubernetes-ready-326CE5.svg)](https://kubernetes.io/)
[![Docker](https://img.shields.io/badge/docker-multi--arch-2496ED.svg)](https://www.docker.com/)

---

## 🌟 What is Sugartalking?

Sugartalking is a Kubernetes-native web application that provides universal control for Audio/Video Receivers (AVRs) from multiple manufacturers. Instead of hardcoding support for specific models, Sugartalking uses a **database-driven architecture** where receiver commands are stored as data, making it trivial to add support for new models without changing any code.

### Key Features

- ✅ **Multi-Receiver Support** - Control receivers from Denon, Yamaha, Onkyo, and more
- ✅ **Auto-Discovery** - Automatically finds receivers on your network via mDNS and HTTP probing
- ✅ **Database-Driven** - Add new receivers by seeding the database, no code changes needed
- ✅ **Kubernetes-Ready** - Fully containerized with Helm-like installers
- ✅ **Auto-Error Reporting** - Bugs automatically reported to GitHub Issues
- ✅ **Admin Panel** - Web UI for managing receivers and commands
- ✅ **Modern UI** - Responsive glassmorphism design
- ✅ **Homelab-Friendly** - Designed for self-hosted environments

### Currently Supported Receivers

- **Denon AVR-X2300W** (fully tested)
- *Add yours!* See [Adding New Receivers](docs/ADDING_RECEIVERS.md)

---

## 🚀 Quick Start

### Prerequisites

- **Kubernetes cluster** (local or cloud)
- **kubectl** configured
- *Optional:* Docker for local testing

### Installation (Kubernetes)

#### Linux/macOS
```bash
git clone https://github.com/builderOfTheWorlds/denon_avr_x2300w_webGUI.git
cd denon_avr_x2300w_webGUI/kubernetes
chmod +x installer.sh
./installer.sh
```

#### Windows (PowerShell)
```powershell
git clone https://github.com/builderOfTheWorlds/denon_avr_x2300w_webGUI.git
cd denon_avr_x2300w_webGUI\kubernetes
.\installer.ps1
```

The installer will:
1. ✅ Check prerequisites
2. ✅ Create namespace (if needed)
3. ✅ Set up GitHub error reporting (optional)
4. ✅ Deploy all Kubernetes resources
5. ✅ Wait for pods to be ready
6. ✅ Display access instructions

### Accessing the Application

**Option 1: Port Forward** (quick access)
```bash
kubectl port-forward svc/sugartalking 5000:80 -n default
```
Then visit: http://localhost:5000

**Option 2: Ingress** (permanent URL)
```bash
# Edit kubernetes/base/ingress.yaml with your hostname
kubectl apply -f kubernetes/base/ingress.yaml
```
Then visit: http://sugartalking.local (add to /etc/hosts)

---

## 🐳 Docker (Local Testing)

### Using Docker Compose

```bash
cd docker
docker-compose up
```

Visit: http://localhost:5000

### Building from Source

```bash
docker build -f docker/Dockerfile -t sugartalking:latest .
docker run -p 5000:5000 --network host sugartalking:latest
```

*Note: `--network host` is required for LAN device discovery*

---

## 📖 Documentation

- **[Adding New Receivers](docs/ADDING_RECEIVERS.md)** - How to add support for new AVR models
- **[GitHub Bot Setup](docs/GITHUB_BOT_SETUP.md)** - Configure automatic error reporting
- **[Phase 4: Doc Parser](docs/PHASE4_DOC_PARSER.md)** - Future AI-powered documentation parsing
- **[Context Prompt](docs/CONTEXT_PROMPT.md)** - Guide for continuing development with AI

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│  Flask + WSGI   │
│   (Gunicorn)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────┐   ┌─────────┐
│ DB  │   │ Network │
│SQLite│  │Discovery│
└─────┘   └────┬────┘
              │ mDNS/HTTP
              ▼
         ┌──────────┐
         │ AVR      │
         │Receivers │
         └──────────┘
```

### Database Schema

**Receivers** → **Commands** → **CommandParameters**

- `receivers`: Manufacturer, model, protocol, default port
- `commands`: Action type, endpoint, HTTP method, command template
- `command_parameters`: Parameter specs with validation
- `discovered_receivers`: Auto-discovered devices on network
- `error_logs`: Error tracking for auto-reporting

### Directory Structure

```
denon_avr_x2300w_webGUI/
├── app/                    # Main application
│   ├── models.py          # SQLAlchemy models
│   ├── routes/            # API endpoints
│   └── services/          # Business logic
├── static/                # Frontend files
├── docker/                # Docker configuration
├── kubernetes/            # K8s manifests + installers
├── scripts/               # Database seeding
├── docs/                  # Documentation
└── wsgi.py               # Gunicorn entry point
```

---

## 🎮 Usage

### Web Interface

1. **Access the app**: http://localhost:5000
2. **Discover receivers**: Click "Scan Network" to find devices
3. **Select receiver**: Choose from dropdown
4. **Control**: Use power, volume, input buttons

### Admin Panel

Access at http://localhost:5000/admin

- View receiver models and commands
- See discovered devices
- Monitor error logs
- Check statistics

### API

#### Discover Receivers
```bash
curl -X POST http://localhost:5000/api/discover \
  -H "Content-Type: application/json" \
  -d '{"method": "both", "duration": 5}'
```

#### Power Control
```bash
curl -X POST http://localhost:5000/api/power/on \
  -H "Content-Type: application/json" \
  -d '{
    "receiver_ip": "192.168.1.182",
    "receiver_model": "AVR-X2300W"
  }'
```

#### List Commands
```bash
curl http://localhost:5000/api/commands/AVR-X2300W
```

#### Health Check
```bash
curl http://localhost:5000/api/health
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `/data` | Database and logs directory |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `PORT` | `5000` | Application port |
| `AUTO_REPORT_ERRORS` | `true` | Enable GitHub error reporting |
| `GITHUB_TOKEN` | - | GitHub personal access token |
| `GITHUB_REPO` | `builderOfTheWorlds/denon_avr_x2300w_webGUI` | Target repository for issues |

### Kubernetes ConfigMap

Edit `kubernetes/base/configmap.yaml` to customize settings.

### Kubernetes Secret

Create a secret for GitHub error reporting:
```bash
kubectl create secret generic sugartalking-secrets \
  --from-literal=GITHUB_TOKEN='your_token_here' \
  -n default
```

See [GitHub Bot Setup](docs/GITHUB_BOT_SETUP.md) for details.

---

## 🤝 Contributing

### Adding a New Receiver

1. Research the receiver's API (HTTP, telnet, serial, etc.)
2. Test commands manually
3. Create a seed script in `scripts/`
4. Run the script to populate the database
5. Test via the web UI or API
6. Submit a pull request!

See [Adding New Receivers](docs/ADDING_RECEIVERS.md) for detailed instructions.

### Reporting Issues

- **Bugs**: Automatically reported to GitHub (if enabled)
- **Manual reports**: [Open an issue](https://github.com/builderOfTheWorlds/denon_avr_x2300w_webGUI/issues)

### Development Workflow

1. Clone the repository
2. Make changes in a feature branch
3. Test locally with Docker Compose
4. Test in Kubernetes (minikube or real cluster)
5. Update documentation
6. Submit pull request

---

## 🛠️ Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python scripts/seed_database.py

# Run development server
python wsgi.py
```

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

---

## 📊 Project Status

### Version 2.0.0 (Current)

✅ **Completed**:
- Database-driven command system
- Kubernetes deployment
- Auto-discovery (mDNS + HTTP)
- Auto-error reporting
- Admin panel
- Multi-receiver support framework
- Denon AVR-X2300W fully implemented

🚧 **In Progress**:
- Frontend updates for multi-receiver selection
- Additional receiver models
- Comprehensive testing

📋 **Planned**:
- Phase 4: AI-powered documentation parser
- Mobile app
- Voice control integration (Alexa, Google Home)
- Advanced scheduling and automation

---

## 🐛 Troubleshooting

### App won't start

**Check logs**:
```bash
kubectl logs -l app=sugartalking -n default
```

**Common issues**:
- PersistentVolume not bound → Check storage class
- ImagePullBackOff → Check image name/registry
- CrashLoopBackOff → Check logs for Python errors

### Can't discover receivers

**Checklist**:
- [ ] App using `hostNetwork: true` in deployment
- [ ] Receiver powered on and connected to same network
- [ ] Firewall not blocking discovery
- [ ] Receiver supports mDNS or responds to HTTP on port 80

**Test manually**:
```bash
# From inside the pod
kubectl exec -it <pod-name> -- curl http://192.168.1.182
```

### Error reporting not working

**Checklist**:
- [ ] GitHub token configured in secret
- [ ] Token has `repo` scope
- [ ] Bot account has write access to repository
- [ ] `AUTO_REPORT_ERRORS=true` in ConfigMap

See [GitHub Bot Setup](docs/GITHUB_BOT_SETUP.md) for troubleshooting.

---

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Original Denon AVR-X2300W protocol research
- Flask and Python ecosystem
- Kubernetes community
- Everyone who contributes receiver support!

---

## 📞 Support

- **Documentation**: Check the [docs/](docs/) folder
- **Issues**: [GitHub Issues](https://github.com/builderOfTheWorlds/denon_avr_x2300w_webGUI/issues)
- **AI Assistant**: Use the [Context Prompt](docs/CONTEXT_PROMPT.md) with Claude

---

## 🗺️ Roadmap

### Version 2.1 (Next)
- [ ] Frontend multi-receiver support
- [ ] More receiver models (Yamaha, Onkyo, etc.)
- [ ] Volume control implementation
- [ ] Input selection implementation

### Version 3.0 (Future)
- [ ] AI-powered documentation parser (Phase 4)
- [ ] Mobile application
- [ ] Voice control integration
- [ ] Home Assistant integration
- [ ] Advanced automation and scheduling

---

## ⭐ Star History

If you find Sugartalking useful, please consider starring the repository!

---

<p align="center">
  Made with ❤️ for the homelab community
</p>

<p align="center">
  <b>Sugartalking</b> - Because your AVR deserves better control
</p>
