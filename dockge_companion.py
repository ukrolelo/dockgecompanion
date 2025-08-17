#!/usr/bin/env python3
"""
Dockge Companion - Docker Container Digest Tracker

A companion tool for Dockge that tracks Docker container digests to help you
know which specific version you have installed when using 'latest' tags.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli import main

if __name__ == '__main__':
    main()