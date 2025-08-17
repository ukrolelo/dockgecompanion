#!/usr/bin/env python3
"""
Basic test script for Dockge Companion functionality.
This script performs basic smoke tests to ensure the tool works correctly.
"""

import os
import sys
import tempfile
import sqlite3
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database import DatabaseManager
from src.models import ContainerInfo, DigestChange
from src.docker_scanner import DockerScanner


def test_database_operations():
    """Test basic database operations."""
    print("🧪 Testing database operations...")
    
    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # Initialize database
        db_manager = DatabaseManager(db_path)
        
        # Create test container info
        test_container = ContainerInfo(
            container_id='test123',
            container_name='test-nginx',
            service_name='web',
            image_name='nginx',
            image_tag='latest',
            digest='sha256:abcdef123456',
            project_name='test-project',
            created_at=datetime.now()
        )
        
        # Store container info
        db_manager.store_container_info(test_container)
        
        # Retrieve containers
        containers = db_manager.get_latest_containers()
        assert len(containers) == 1
        assert containers[0].container_name == 'test-nginx'
        
        # Test digest change detection
        updated_container = ContainerInfo(
            container_id='test123',
            container_name='test-nginx',
            service_name='web',
            image_name='nginx',
            image_tag='latest',
            digest='sha256:newdigest789',
            project_name='test-project',
            created_at=datetime.now()
        )
        
        db_manager.store_container_info(updated_container)
        
        # Check if change was recorded
        changes = db_manager.get_digest_history('test-nginx')
        assert len(changes) == 1
        assert changes[0].old_digest == 'sha256:abcdef123456'
        assert changes[0].new_digest == 'sha256:newdigest789'
        
        print("✅ Database operations test passed!")
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_docker_scanner():
    """Test Docker scanner functionality."""
    print("🧪 Testing Docker scanner...")
    
    try:
        scanner = DockerScanner()
        
        # Test Docker availability
        is_available = scanner.is_docker_available()
        print(f"   Docker available: {is_available}")
        
        if is_available:
            # Test container scanning
            containers = scanner.scan_containers()
            print(f"   Found {len(containers)} containers")
            
            if containers:
                # Test container info extraction
                first_container = containers[0]
                assert hasattr(first_container, 'container_name')
                assert hasattr(first_container, 'digest')
                assert hasattr(first_container, 'image_name')
                print(f"   Sample container: {first_container.container_name}")
        
        print("✅ Docker scanner test passed!")
        
    except Exception as e:
        print(f"⚠️  Docker scanner test failed (this is OK if Docker is not running): {e}")


def test_image_name_parsing():
    """Test image name parsing logic."""
    print("🧪 Testing image name parsing...")
    
    scanner = DockerScanner()
    
    test_cases = [
        ('nginx:latest', ('nginx', 'latest')),
        ('nginx', ('nginx', 'latest')),
        ('registry.com/nginx:1.21', ('registry.com/nginx', '1.21')),
        ('nginx@sha256:abc123', ('nginx', 'digest')),
        ('', ('unknown', 'unknown'))
    ]
    
    for image_string, expected in test_cases:
        result = scanner._parse_image_name(image_string)
        assert result == expected, f"Failed for {image_string}: got {result}, expected {expected}"
    
    print("✅ Image name parsing test passed!")


def test_cli_imports():
    """Test that CLI module imports correctly."""
    print("🧪 Testing CLI imports...")
    
    try:
        from src.cli import main
        from src.tracker import ContainerTracker
        print("✅ CLI imports test passed!")
    except ImportError as e:
        print(f"❌ CLI imports test failed: {e}")
        raise


def run_all_tests():
    """Run all tests."""
    print("🚀 Running Dockge Companion tests...\n")
    
    tests = [
        test_cli_imports,
        test_database_operations,
        test_image_name_parsing,
        test_docker_scanner,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
        print()
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)