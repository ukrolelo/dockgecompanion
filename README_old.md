# Dockge Companion

A companion tool for Dockge that tracks Docker container digests to help you know which specific version you have installed when using 'latest' tags.

## Problem Solved

When using Docker Compose with `latest` tags, you lose track of which specific version is actually running when the `latest` tag gets updated on Docker Hub. This tool tracks the actual image digests so you always know exactly which version you have deployed.

**Example scenario:**
- You deploy `nginx:latest` in your docker-compose.yml
- A few weeks later, nginx releases a new version and updates the `latest` tag
- You run `docker-compose pull && docker-compose up -d`
- Now you have a new version, but you don't know which specific version you had before or which one you have now

**Dockge Companion solves this by:**
- Tracking the actual SHA256 digest of each container image
- Storing historical data of digest changes
- Showing you exactly when versions changed and what changed

## Features

- 🔍 **Digest Tracking**: Track actual SHA256 digests of container images
- 📊 **Change Detection**: Automatically detect when container images are updated
- 📈 **Historical Data**: Keep history of all digest changes with timestamps
- 🔄 **Comparison Tools**: Compare current state with previous scans
- 📋 **Detailed Reports**: Generate comprehensive reports of all tracked containers
- 🚀 **Easy Integration**: Works alongside Dockge and docker-compose
- ⚡ **CLI Interface**: Simple command-line interface for automation
- 🏷️ **Project Support**: Automatically detects docker-compose projects and services

## Installation

### Option 1: Automatic Installation (Recommended)

1. Clone or download this repository
2. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

This will create a virtual environment and install all dependencies.

### Option 2: Manual Installation

1. Clone or download this repository
2. Create a virtual environment:
```bash
# On Ubuntu/Debian, first install python3-venv if needed:
sudo apt install python3-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

3. Make the script executable (optional):
```bash
chmod +x dockge_companion.py
```

### System Requirements

- Python 3.7 or higher
- Docker (running and accessible)
- Linux/macOS (Windows should work but is untested)

**Note**: Always activate the virtual environment before using the tool:
```bash
source venv/bin/activate
```

## Quick Start

```bash
# 1. Initialize the database and perform first scan
python dockge_companion.py init

# 2. Scan current containers (run this regularly)
python dockge_companion.py scan

# 3. Check status of tracked containers
python dockge_companion.py status

# 4. Compare current state with previous state
python dockge_companion.py compare

# 5. View history for a specific container
python dockge_companion.py history nginx

# 6. Check for available updates
python dockge_companion.py check-updates

# 7. Generate comprehensive report
python dockge_companion.py report
```

## Commands Reference

### `init`
Initialize the database and perform the first scan. Run this once when setting up.

```bash
python dockge_companion.py init
```

### `scan`
Scan current containers and update the database. This is the main command you'll run regularly.

```bash
python dockge_companion.py scan [--include-stopped]
```

Options:
- `--include-stopped`: Also scan stopped containers

### `status`
Show current status of all tracked containers in a nice table format.

```bash
python dockge_companion.py status [--format table|json]
```

Example output:
```
📊 Container Status (3 containers)
┌─────────────┬─────────┬──────────────┬──────────────┬─────────────┬─────────┬─────────┐
│ Container   │ Service │ Image        │ Digest       │ Status      │ Project │ Changes │
├─────────────┼─────────┼──────────────┼──────────────┼─────────────┼─────────┼─────────┤
│ nginx       │ web     │ nginx:latest │ sha256:abc12 │ 🟢 Running  │ myapp   │ 2       │
│ postgres    │ db      │ postgres:15  │ sha256:def34 │ 🟢 Running  │ myapp   │ 0       │
│ redis       │ cache   │ redis:alpine │ sha256:ghi56 │ 🔴 Stopped  │ myapp   │ 1       │
└─────────────┴─────────┴──────────────┴──────────────┴─────────────┴─────────┴─────────┘
```

### `compare`
Compare current state with a previous point in time.

```bash
python dockge_companion.py compare [--hours 24]
```

Options:
- `--hours N`: Compare with state from N hours ago (default: 24)

### `history`
Show detailed digest change history for a specific container.

```bash
python dockge_companion.py history <container_name>
```

Example:
```bash
python dockge_companion.py history nginx
```

### `check-updates`
Check for available updates by comparing local container digests with the latest versions available online.

```bash
python dockge_companion.py check-updates [--format table|json]
```

This command:
- Connects to Docker registries (Docker Hub, etc.)
- Fetches the latest digest for each image tag
- Compares with your currently running digests
- Shows which containers have updates available

Example output:
```
🔍 Update Check Results
📦 Total containers: 2
🆙 Updates available: 1
⚠️  1 container(s) have updates available

📋 Container Update Status:
┌─────────────┬─────────────────┬─────────────────┬─────────────────┬──────────────────┐
│ Container   │ Image           │ Current         │ Remote          │ Status           │
├─────────────┼─────────────────┼─────────────────┼─────────────────┼──────────────────┤
│ nginx       │ nginx:latest    │ sha256:abc123...│ sha256:def456...│ 🆙 Update Available│
│ postgres    │ postgres:15     │ sha256:ghi789...│ sha256:ghi789...│ ✅ Up to date     │
└─────────────┴─────────────────┴─────────────────┴─────────────────┴──────────────────┘
```

### `report`
Generate a comprehensive report of all containers and recent changes.

```bash
python dockge_companion.py report [--format table|json]
```

## Integration with Dockge

Dockge Companion works seamlessly alongside Dockge:

1. **Automatic Detection**: Automatically detects containers managed by docker-compose
2. **Service Names**: Extracts service names from docker-compose labels
3. **Project Names**: Groups containers by docker-compose project
4. **No Interference**: Doesn't interfere with Dockge operations

### Recommended Workflow

1. Set up your docker-compose stacks in Dockge as usual
2. Run `python dockge_companion.py init` to start tracking
3. Set up automated scanning (see Automation section)
4. Check for available updates before updating:
   ```bash
   python dockge_companion.py check-updates
   ```
5. Before updating containers in Dockge, check current versions:
   ```bash
   python dockge_companion.py status
   ```
6. After updating, scan again to record changes:
   ```bash
   python dockge_companion.py scan
   ```
7. Compare to see what changed:
   ```bash
   python dockge_companion.py compare
   ```

## Automation

### Cron Job Setup

Add to your crontab for regular scanning:

```bash
# Edit crontab
crontab -e

# Add one of these lines:

# Scan every hour
0 * * * * /usr/bin/python3 /path/to/dockge_companion.py scan

# Scan every 30 minutes
*/30 * * * * /usr/bin/python3 /path/to/dockge_companion.py scan

# Scan daily at 2 AM
0 2 * * * /usr/bin/python3 /path/to/dockge_companion.py scan
```

### Systemd Timer (Alternative)

Create a systemd service and timer for more advanced scheduling:

1. Create `/etc/systemd/system/dockge-companion.service`:
```ini
[Unit]
Description=Dockge Companion Scan
After=docker.service

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/dockge-companion
ExecStart=/usr/bin/python3 dockge_companion.py scan
```

2. Create `/etc/systemd/system/dockge-companion.timer`:
```ini
[Unit]
Description=Run Dockge Companion every hour
Requires=dockge-companion.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

3. Enable and start:
```bash
sudo systemctl enable dockge-companion.timer
sudo systemctl start dockge-companion.timer
```

## Configuration

The tool stores its data in `~/.dockge-companion/containers.db` by default. You can customize this and other settings by modifying `config.py`:

```python
# Database location
DATABASE_PATH = '/custom/path/containers.db'

# Docker socket (if using remote Docker)
DOCKER_SOCKET = 'tcp://remote-docker:2376'

# Exclude system containers
EXCLUDE_SYSTEM_CONTAINERS = True
```

## Data Storage

- **Database**: SQLite database stored in `~/.dockge-companion/containers.db`
- **Container Info**: Stores container name, image, digest, timestamps, and metadata
- **Change History**: Tracks all digest changes with timestamps
- **No External Dependencies**: Everything stored locally

## Troubleshooting

### Docker Permission Issues
If you get permission errors accessing Docker:

```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### Database Issues
If you encounter database corruption:

```bash
# Backup current database
cp ~/.dockge-companion/containers.db ~/.dockge-companion/containers.db.backup

# Reinitialize (will lose history)
python dockge_companion.py init
```

### No Containers Found
If no containers are detected:

1. Make sure Docker is running: `docker ps`
2. Check if containers are running: `docker container ls`
3. Try including stopped containers: `python dockge_companion.py scan --include-stopped`

## Use Cases

### 1. Version Tracking for Production
Track exactly which versions are running in production:

```bash
# Before deployment
python dockge_companion.py status > pre-deployment.txt

# After deployment
python dockge_companion.py scan
python dockge_companion.py compare --hours 1
```

### 2. Rollback Information
Know exactly which version to rollback to:

```bash
python dockge_companion.py history nginx
# Shows all previous digests with timestamps
```

### 3. Change Monitoring
Monitor for unexpected changes:

```bash
# Daily check for changes
python dockge_companion.py compare --hours 24
```

### 4. Update Monitoring
Check for available updates without pulling images:

```bash
# Check for updates
python dockge_companion.py check-updates

# Automated update checking (add to cron)
python dockge_companion.py check-updates --format json | jq '.updates_available'
```

### 5. Audit Trail
Generate reports for compliance:

```bash
python dockge_companion.py report --format json > audit-report.json
```

## Advanced Usage

### Custom Scanning
```bash
# Scan only running containers (default)
python dockge_companion.py scan

# Include stopped containers
python dockge_companion.py scan --include-stopped

# Verbose output
python dockge_companion.py -v scan

# Quiet mode (errors only)
python dockge_companion.py -q scan
```

### Filtering and Reporting
```bash
# Compare with different time periods
python dockge_companion.py compare --hours 1    # Last hour
python dockge_companion.py compare --hours 168  # Last week

# Different output formats
python dockge_companion.py status --format json
python dockge_companion.py report --format json
```

## Contributing

Feel free to submit issues, feature requests, or pull requests. This tool is designed to be simple and focused on the core use case of digest tracking.

## License

This project is open source. Use it freely for personal and commercial projects.

## FAQ

**Q: Does this interfere with Dockge or Docker operations?**
A: No, this tool only reads information from Docker. It doesn't modify containers or images.

**Q: How much disk space does it use?**
A: Very little. The SQLite database typically uses a few KB to MB depending on how many containers you track and for how long.

**Q: Can I use this without Dockge?**
A: Yes! It works with any Docker setup, not just Dockge. It's useful for any Docker environment where you want to track image versions.

**Q: What happens if I delete a container?**
A: The historical data remains in the database. The container will show as "stopped" in status reports.

**Q: Can I export the data?**
A: Yes, use `--format json` with status and report commands, or access the SQLite database directly.

**Q: Does it work with Docker Swarm or Kubernetes?**
A: Currently designed for single-node Docker and docker-compose setups. Swarm mode containers should work but may not extract all metadata correctly.