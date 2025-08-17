"""Core tracking logic for container digest monitoring."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional

from .docker_scanner import DockerScanner
from .database import DatabaseManager
from .models import ContainerInfo, DigestChange


logger = logging.getLogger(__name__)


class ContainerTracker:
    """Main class for tracking container digests and changes."""
    
    def __init__(self, db_manager: DatabaseManager = None, docker_scanner: DockerScanner = None):
        self.db_manager = db_manager or DatabaseManager()
        self.docker_scanner = docker_scanner or DockerScanner()
    
    def initialize(self) -> bool:
        """
        Initialize the tracker by performing the first scan.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing Dockge Companion...")
            
            # Check Docker availability
            if not self.docker_scanner.is_docker_available():
                logger.error("Docker is not available or accessible")
                return False
            
            # Perform initial scan
            containers = self.docker_scanner.scan_containers()
            
            if not containers:
                logger.warning("No containers found during initialization")
                return True
            
            # Store initial container information
            scan_timestamp = datetime.now()
            for container in containers:
                self.db_manager.store_container_info(container, scan_timestamp)
            
            logger.info(f"Initialization complete. Tracked {len(containers)} containers.")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def scan_and_update(self, include_stopped: bool = True) -> Dict[str, any]:
        """
        Perform a scan of current containers and update the database.
        
        Args:
            include_stopped: Whether to include stopped containers
            
        Returns:
            Dictionary with scan results and statistics
        """
        try:
            logger.info("Starting container scan...")
            scan_timestamp = datetime.now()
            
            # Scan current containers (include stopped by default for complete tracking)
            current_containers = self.docker_scanner.scan_containers(include_stopped)
            
            if not current_containers:
                logger.warning("No containers found during scan")
                return {
                    'success': True,
                    'containers_scanned': 0,
                    'changes_detected': 0,
                    'new_containers': 0,
                    'scan_timestamp': scan_timestamp
                }
            
            # Get previously tracked containers
            previous_containers = self.db_manager.get_latest_containers()
            previous_by_name = {c.container_name: c for c in previous_containers}
            
            # Track statistics
            changes_detected = 0
            new_containers = 0
            scanned_container_names = []
            changed_container_names = []
            new_container_names = []

            # Process each current container
            for container in current_containers:
                scanned_container_names.append(container.container_name)

                # Store container information (this will automatically detect changes)
                self.db_manager.store_container_info(container, scan_timestamp)

                # Check if this is a new container or has changes
                if container.container_name not in previous_by_name:
                    new_containers += 1
                    new_container_names.append(container.container_name)
                    logger.info(f"New container detected: {container.container_name}")
                else:
                    previous = previous_by_name[container.container_name]
                    if previous.digest != container.digest:
                        changes_detected += 1
                        changed_container_names.append(container.container_name)
                        logger.info(f"Digest change detected for {container.container_name}")

            result = {
                'success': True,
                'containers_scanned': len(current_containers),
                'changes_detected': changes_detected,
                'new_containers': new_containers,
                'scan_timestamp': scan_timestamp,
                'scanned_container_names': scanned_container_names,
                'changed_container_names': changed_container_names,
                'new_container_names': new_container_names
            }

            # Log with container names
            container_list = ", ".join(scanned_container_names) if scanned_container_names else "none"
            logger.info(f"Scan complete: {len(current_containers)} containers ({container_list}), "
                       f"{changes_detected} changes, {new_containers} new")
            
            return result
            
        except Exception as e:
            logger.error(f"Scan failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'scan_timestamp': datetime.now()
            }
    
    def compare_with_previous(self, hours_back: int = 24) -> Dict[str, any]:
        """
        Compare current state with previous state.
        
        Args:
            hours_back: How many hours back to compare with
            
        Returns:
            Dictionary with comparison results
        """
        try:
            # Get current containers
            current_containers = self.db_manager.get_latest_containers()
            current_by_name = {c.container_name: c for c in current_containers}
            
            # Get recent changes
            recent_changes = self.db_manager.get_recent_changes(hours_back)
            
            # Categorize containers
            unchanged = []
            changed = []
            new_containers = []
            
            # Get containers from hours_back ago for comparison
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for container in current_containers:
                # Check if container has recent changes
                container_changes = [c for c in recent_changes 
                                   if c.container_name == container.container_name]
                
                if container_changes:
                    changed.append({
                        'container': container,
                        'changes': container_changes
                    })
                else:
                    # Check if container is new (created after cutoff)
                    if container.created_at > cutoff_time:
                        new_containers.append(container)
                    else:
                        unchanged.append(container)
            
            return {
                'success': True,
                'comparison_period_hours': hours_back,
                'total_containers': len(current_containers),
                'unchanged': unchanged,
                'changed': changed,
                'new_containers': new_containers,
                'total_changes': len(recent_changes)
            }
            
        except Exception as e:
            logger.error(f"Comparison failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_container_status(self) -> List[Dict[str, any]]:
        """
        Get current status of all tracked containers.
        
        Returns:
            List of container status dictionaries
        """
        try:
            containers = self.db_manager.get_latest_containers()
            status_list = []
            
            for container in containers:
                # Get recent changes for this container
                recent_changes = self.db_manager.get_digest_history(container.container_name)
                
                # Check if container is currently running
                is_running = self.docker_scanner.is_container_running(container.container_name)
                
                status = {
                    'container_name': container.container_name,
                    'service_name': container.service_name,
                    'image': f"{container.image_name}:{container.image_tag}",
                    'digest': container.digest,
                    'digest_short': container.digest[:12] if container.digest else 'unknown',
                    'project_name': container.project_name,
                    'is_running': is_running,
                    'last_seen': container.created_at,
                    'change_count': len(recent_changes),
                    'last_change': recent_changes[0].change_timestamp if recent_changes else None
                }
                
                status_list.append(status)
            
            return status_list
            
        except Exception as e:
            logger.error(f"Failed to get container status: {e}")
            return []
    
    def get_container_history(self, container_name: str) -> Dict[str, any]:
        """
        Get detailed history for a specific container.
        
        Args:
            container_name: Name of the container
            
        Returns:
            Dictionary with container history
        """
        try:
            # Get current container info
            current_containers = self.db_manager.get_latest_containers()
            current_container = next(
                (c for c in current_containers if c.container_name == container_name), 
                None
            )
            
            if not current_container:
                return {
                    'success': False,
                    'error': f"Container '{container_name}' not found in tracking database"
                }
            
            # Get digest history
            digest_changes = self.db_manager.get_digest_history(container_name)
            
            # Check if container is currently running
            is_running = self.docker_scanner.is_container_running(container_name)

            return {
                'success': True,
                'container_name': container_name,
                'current_info': current_container,
                'is_running': is_running,
                'digest_changes': digest_changes,
                'total_changes': len(digest_changes)
            }
            
        except Exception as e:
            logger.error(f"Failed to get container history: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_report(self) -> Dict[str, any]:
        """
        Generate a comprehensive report of all tracked containers.
        
        Returns:
            Dictionary with comprehensive report data
        """
        try:
            # Get all container statuses
            container_statuses = self.get_container_status()
            
            # Get recent changes (last 7 days)
            recent_changes = self.db_manager.get_recent_changes(hours=24*7)
            
            # Calculate statistics
            total_containers = len(container_statuses)
            running_containers = sum(1 for c in container_statuses if c['is_running'])
            containers_with_changes = sum(1 for c in container_statuses if c['change_count'] > 0)
            
            # Group changes by day
            changes_by_day = {}
            for change in recent_changes:
                day = change.change_timestamp.date()
                if day not in changes_by_day:
                    changes_by_day[day] = []
                changes_by_day[day].append(change)
            
            # Get projects
            projects = set(c['project_name'] for c in container_statuses if c['project_name'])
            
            return {
                'success': True,
                'generated_at': datetime.now(),
                'summary': {
                    'total_containers': total_containers,
                    'running_containers': running_containers,
                    'stopped_containers': total_containers - running_containers,
                    'containers_with_changes': containers_with_changes,
                    'total_projects': len(projects),
                    'recent_changes_7days': len(recent_changes)
                },
                'containers': container_statuses,
                'recent_changes': recent_changes,
                'changes_by_day': changes_by_day,
                'projects': list(projects)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def check_for_updates(self) -> Dict[str, any]:
        """
        Check all tracked containers for available updates.

        Returns:
            Dictionary with update check results
        """
        try:
            logger.info("Checking for container updates...")

            # Get current containers
            containers = self.db_manager.get_latest_containers()

            if not containers:
                return {
                    'success': True,
                    'total_containers': 0,
                    'updates_available': 0,
                    'containers': [],
                    'errors': []
                }

            update_results = []
            updates_available = 0
            errors = []

            for container in containers:
                logger.debug(f"Checking updates for {container.container_name}")

                # Check for updates
                update_info = self.docker_scanner.check_container_updates(container)
                update_results.append(update_info)

                if update_info.get('update_available', False):
                    updates_available += 1
                    logger.info(f"Update available for {container.container_name}")

                if update_info.get('error'):
                    errors.append(f"{container.container_name}: {update_info['error']}")

            result = {
                'success': True,
                'total_containers': len(containers),
                'updates_available': updates_available,
                'containers': update_results,
                'errors': errors,
                'check_timestamp': datetime.now()
            }

            logger.info(f"Update check complete: {updates_available}/{len(containers)} containers have updates available")
            return result

        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'check_timestamp': datetime.now()
            }