
# 🐳 Dockge Companion

**A comprehensive Docker container digest monitoring and management tool with both command-line and web interfaces.**

Dockge Companion helps you track Docker container image changes over time, check for updates, and manage container versions with precision. Perfect for production environments where you need to monitor container updates and maintain rollback capabilities.

## 📸 Screenshots

### Web Interface Dashboard
![Web Interface Dashboard](img/Screenshot%20from%202025-08-17%2012-20-53.png)

### Terminal User Interface (TUI)
![Terminal User Interface](img/Screenshot%20from%202025-08-17%2013-03-33.png)

## ✨ Features

### 🔍 **Container Monitoring**
- **Automatic digest tracking** - Monitor container image changes automatically
- **Update detection** - Check for available image updates across all containers
- **Change history** - Complete timeline of container image changes
- **Project grouping** - Organize containers by Docker Compose projects

### 🖥️ **Dual Interface**
- **Command Line Interface (CLI)** - Perfect for automation and scripting
- **Terminal User Interface (TUI)** - Interactive menu-driven interface
- **Web Interface** - Modern responsive web dashboard with real-time updates

### 📊 **Comprehensive Reporting**
- **Status dashboards** - Overview of all container states
- **Detailed reports** - Export-ready comprehensive reports
- **Change analytics** - Track container update patterns
- **Rollback instructions** - Step-by-step rollback guidance

### 🔄 **Version Management**
- **Precise rollbacks** - Roll back to any previous container version
- **Image pinning** - Pin containers to specific digests
- **Copy-paste ready** - Generate `image@digest` references for docker-compose
- **Backup current versions** - Save current state before updates

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/dockgecompanion.git
   cd dockgecompanion
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (for web interface):**
   ```bash
   cp .env.example .env
   # Edit .env and set DJANGO_SECRET_KEY to a secure random value
   ```

4. **Initialize the database:**
   ```bash
   python dockge_companion.py init
   ```

### Basic Usage

#### Command Line Interface
```bash
# Scan all containers and update database
python dockge_companion.py scan

# Check container status
python dockge_companion.py status

# Check for available updates
python dockge_companion.py check-updates

# View container history
python dockge_companion.py history <container_name>

# Generate comprehensive report
python dockge_companion.py report
```

#### Terminal User Interface
```bash
# Launch interactive TUI
python dockge_companion_tui.py
```

#### Web Interface
```bash
# Start web server
cd dockgeweb
python manage.py runserver 0.0.0.0:8000

# Access at http://localhost:8000
```

## ⚙️ Automated Monitoring

### Crontab Setup

For automatic container monitoring, add this to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line to scan containers daily at 5:30 AM
30 5 * * * cd /home/<USER>/Desktop/Programming/dockgecompanion && python3 dockge_companion.py scan

# Optional: Check for updates weekly on Mondays at 6:00 AM
0 6 * * 1 cd /home/<USER>/Desktop/Programming/dockgecompanion && python3 dockge_companion.py check-updates
```

## 🌐 Web Interface

The web interface provides a modern, responsive dashboard with:

- **Real-time container status** with running/stopped indicators
- **Interactive update checking** with AJAX-powered scanning
- **Complete change history** with timeline views
- **Copy-paste ready image references** in `image@digest` format
- **Dark/light theme toggle** for comfortable viewing
- **Mobile-responsive design** for on-the-go monitoring

### Web Interface Features

- **Dashboard** (`/`) - Overview with statistics and recent changes
- **Container Status** (`/status/`) - Detailed container table with update info
- **Container Detail** (`/container/<name>/`) - Individual container management
- **Container History** (`/container/<name>/history/`) - Complete change timeline
- **Reports** (`/report/`) - Comprehensive system reports
- **Settings** (`/settings/`) - Configuration and system status

## 📋 Use Cases

### 🏢 **Production Monitoring**
- Track container updates in production environments
- Get notified when containers change unexpectedly
- Maintain audit trail of all container changes
- Quick rollback capabilities for incident response

### 🔄 **Update Management**
- Check for available updates across all containers
- Plan update schedules based on change frequency
- Test updates in staging before production deployment
- Maintain version consistency across environments

### 🛡️ **Security & Compliance**
- Monitor for security updates in base images
- Maintain detailed logs of all container changes
- Generate compliance reports for audits
- Track container provenance and history

### 🚀 **DevOps Automation**
- Integrate with CI/CD pipelines for automated monitoring
- Generate alerts when containers drift from expected versions
- Automate rollback procedures during incidents
- Maintain infrastructure as code with precise version control

## 🔧 Configuration

### Environment Variables

```bash
# Database location (optional)
export DOCKGE_COMPANION_DB_PATH="~/.dockge-companion/containers.db"

# Docker socket (optional)
export DOCKER_HOST="unix:///var/run/docker.sock"
```

### Configuration File

Create `config.py` to customize behavior:

```python
# Database configuration
DATABASE_PATH = "~/.dockge-companion/containers.db"

# Docker configuration
DOCKER_SOCKET = "unix:///var/run/docker.sock"

# Web interface configuration
WEB_HOST = "0.0.0.0"
WEB_PORT = 8000

# Monitoring configuration
DEFAULT_SCAN_INTERVAL = 24  # hours
RETENTION_DAYS = 90  # days to keep history
```

## 📊 Output Formats

### Container Status
```
| Container       | Status    | Image                    | Updates |
|================ |=========== |========================= |======== |
| dockge-dockge-1 | 🟢 Running | louislam/dockge:1       | ✅ Latest |
| test-python-1   | 🔴 Stopped | python:3.9              | 🔄 Available |
```

### Image References (Copy-Paste Ready)
```
python@sha256:68d0775234842868248bfe185eece56e725d3cb195f511a21233d0f564dee501
louislam/dockge@sha256:abc123def456789012345678901234567890123456789012345678901234567890
```

### Docker Compose Integration
```yaml
services:
  app:
    # Before: Unpinned version
    # image: python:3.9
    
    # After: Pinned to specific digest
    image: python@sha256:68d0775234842868248bfe185eece56e725d3cb195f511a21233d0f564dee501
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for Docker container management and monitoring
- Inspired by the need for precise container version control
- Designed for production reliability and ease of use

---

**Made with ❤️ for the Dockge community**
