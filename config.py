"""Configuration settings for Dockge Companion."""

import os
from pathlib import Path

# Database configuration
DATABASE_PATH = os.path.join(Path.home(), '.dockge-companion', 'containers.db')
DATABASE_DIR = os.path.dirname(DATABASE_PATH)

# Docker configuration
DOCKER_SOCKET = 'unix://var/run/docker.sock'

# Logging configuration
LOG_LEVEL = 'INFO'

# Default settings
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
EXCLUDE_SYSTEM_CONTAINERS = True

# Ensure database directory exists
os.makedirs(DATABASE_DIR, exist_ok=True)