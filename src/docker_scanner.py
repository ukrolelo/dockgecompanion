"""Docker API integration for scanning containers and extracting digest information."""

import docker
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from docker.errors import DockerException, APIError

from .models import ContainerInfo
import config


logger = logging.getLogger(__name__)


class DockerScanner:
    """Handles Docker API interactions for container scanning."""
    
    def __init__(self, docker_socket: str = None):
        self.docker_socket = docker_socket or config.DOCKER_SOCKET
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Docker client."""
        if self._client is None:
            try:
                self._client = docker.from_env()
                # Test connection
                self._client.ping()
                logger.info("Docker client connected successfully")
            except DockerException as e:
                logger.error(f"Failed to connect to Docker: {e}")
                raise
        return self._client
    
    def scan_containers(self, include_stopped: bool = False) -> List[ContainerInfo]:
        """
        Scan all containers and extract their information.
        
        Args:
            include_stopped: Whether to include stopped containers
            
        Returns:
            List of ContainerInfo objects
        """
        containers = []
        
        try:
            # Get containers (running by default, or all if include_stopped=True)
            docker_containers = self.client.containers.list(all=include_stopped)
            
            for container in docker_containers:
                try:
                    container_info = self._extract_container_info(container)
                    if container_info:
                        containers.append(container_info)
                except Exception as e:
                    logger.warning(f"Failed to extract info for container {container.name}: {e}")
                    continue
            
            logger.info(f"Scanned {len(containers)} containers")
            return containers
            
        except APIError as e:
            logger.error(f"Docker API error during scan: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during container scan: {e}")
            raise
    
    def _extract_container_info(self, container) -> Optional[ContainerInfo]:
        """
        Extract detailed information from a Docker container.
        
        Args:
            container: Docker container object
            
        Returns:
            ContainerInfo object or None if extraction fails
        """
        try:
            # Get container attributes
            attrs = container.attrs
            config_data = attrs.get('Config', {})
            
            # Extract basic information
            container_id = container.id
            container_name = container.name
            
            # Get image information
            image_name, image_tag = self._parse_image_name(config_data.get('Image', ''))
            
            # Get image digest - this is the key information we need
            digest = self._get_image_digest(container)
            
            if not digest:
                logger.warning(f"Could not get digest for container {container_name}")
                return None
            
            # Extract service name from labels (common in docker-compose)
            labels = config_data.get('Labels') or {}
            service_name = self._extract_service_name(labels)
            project_name = self._extract_project_name(labels)
            
            # Get creation time
            created_str = attrs.get('Created', '')
            created_at = self._parse_docker_timestamp(created_str)
            
            return ContainerInfo(
                container_id=container_id,
                container_name=container_name,
                service_name=service_name,
                image_name=image_name,
                image_tag=image_tag,
                digest=digest,
                project_name=project_name,
                created_at=created_at
            )
            
        except Exception as e:
            logger.error(f"Error extracting container info: {e}")
            return None
    
    def _parse_image_name(self, image_string: str) -> tuple[str, str]:
        """
        Parse image name and tag from image string.
        
        Args:
            image_string: Full image string (e.g., 'nginx:latest' or 'registry.com/nginx:1.21')
            
        Returns:
            Tuple of (image_name, tag)
        """
        if not image_string:
            return 'unknown', 'unknown'
        
        # Handle digest-based images (e.g., nginx@sha256:...)
        if '@sha256:' in image_string:
            image_name = image_string.split('@')[0]
            tag = 'digest'
        elif ':' in image_string:
            image_name, tag = image_string.rsplit(':', 1)
        else:
            image_name = image_string
            tag = 'latest'
        
        return image_name, tag
    
    def _get_image_digest(self, container) -> Optional[str]:
        """
        Get the image digest for a container.
        
        Args:
            container: Docker container object
            
        Returns:
            Image digest string or None
        """
        try:
            # Try to get digest from image
            image = container.image
            
            # Check if image has RepoDigests
            if hasattr(image, 'attrs') and image.attrs:
                repo_digests = image.attrs.get('RepoDigests', [])
                if repo_digests:
                    # Extract digest from first repo digest
                    for repo_digest in repo_digests:
                        if '@sha256:' in repo_digest:
                            return repo_digest.split('@')[1]
            
            # Fallback: try to get from image ID
            if hasattr(image, 'id'):
                # Image ID is usually sha256:... format
                image_id = image.id
                if image_id.startswith('sha256:'):
                    return image_id
            
            # Last resort: use short image ID
            if hasattr(image, 'short_id'):
                return f"short:{image.short_id}"
            
            return None
            
        except Exception as e:
            logger.warning(f"Could not get digest for container: {e}")
            return None
    
    def _extract_service_name(self, labels: Dict[str, str]) -> Optional[str]:
        """
        Extract service name from container labels.
        
        Common label patterns:
        - com.docker.compose.service
        - com.docker.swarm.service.name
        """
        service_labels = [
            'com.docker.compose.service',
            'com.docker.swarm.service.name',
            'service'
        ]
        
        for label in service_labels:
            if label in labels:
                return labels[label]
        
        return None
    
    def _extract_project_name(self, labels: Dict[str, str]) -> Optional[str]:
        """
        Extract project name from container labels.
        
        Common label patterns:
        - com.docker.compose.project
        - com.docker.swarm.stack.name
        """
        project_labels = [
            'com.docker.compose.project',
            'com.docker.swarm.stack.name',
            'project'
        ]
        
        for label in project_labels:
            if label in labels:
                return labels[label]
        
        return None
    
    def _parse_docker_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse Docker timestamp string to datetime object.
        
        Args:
            timestamp_str: Docker timestamp string
            
        Returns:
            datetime object
        """
        try:
            # Docker timestamps are usually in ISO format
            # Remove microseconds if present and parse
            if '.' in timestamp_str:
                timestamp_str = timestamp_str.split('.')[0] + 'Z'
            
            # Handle different timestamp formats
            for fmt in ['%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(timestamp_str.rstrip('Z'), fmt.rstrip('Z'))
                except ValueError:
                    continue
            
            # Fallback to current time
            logger.warning(f"Could not parse timestamp: {timestamp_str}")
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def get_container_by_name(self, name: str) -> Optional[ContainerInfo]:
        """
        Get specific container information by name.

        Args:
            name: Container name

        Returns:
            ContainerInfo object or None if not found
        """
        try:
            container = self.client.containers.get(name)
            return self._extract_container_info(container)
        except docker.errors.NotFound:
            logger.warning(f"Container '{name}' not found")
            return None
        except Exception as e:
            logger.error(f"Error getting container '{name}': {e}")
            return None

    def is_container_running(self, name: str) -> bool:
        """
        Check if a specific container is currently running.

        Args:
            name: Container name

        Returns:
            True if container is running, False otherwise
        """
        try:
            container = self.client.containers.get(name)
            # Check the container status
            container.reload()  # Refresh container state
            return container.status == 'running'
        except docker.errors.NotFound:
            logger.debug(f"Container '{name}' not found")
            return False
        except Exception as e:
            logger.error(f"Error checking container '{name}' status: {e}")
            return False
    
    def is_docker_available(self) -> bool:
        """
        Check if Docker is available and accessible.

        Returns:
            True if Docker is available, False otherwise
        """
        try:
            self.client.ping()
            return True
        except Exception:
            return False

    def get_remote_image_digest(self, image_name: str, tag: str = 'latest') -> Optional[str]:
        """
        Get the digest of an image from the remote registry without pulling it.

        Args:
            image_name: Name of the image (e.g., 'nginx', 'louislam/dockge')
            tag: Tag to check (default: 'latest')

        Returns:
            Remote image digest or None if not found/error
        """
        try:
            full_image = f"{image_name}:{tag}"
            logger.debug(f"Checking remote digest for {full_image}")

            # Method 1: Try to get registry data without pulling
            try:
                registry_data = self.client.images.get_registry_data(full_image)

                if hasattr(registry_data, 'id') and registry_data.id:
                    remote_digest = registry_data.id
                    if remote_digest.startswith('sha256:'):
                        return remote_digest

                # Try to get from attrs
                if hasattr(registry_data, 'attrs'):
                    manifest = registry_data.attrs
                    if 'Descriptor' in manifest and 'digest' in manifest['Descriptor']:
                        return manifest['Descriptor']['digest']

            except (AttributeError, docker.errors.APIError) as e:
                logger.debug(f"get_registry_data failed for {full_image}: {e}")

            # Method 2: Use low-level API to inspect remote image
            try:
                # This uses the Docker API to inspect the image without pulling
                image_info = self.client.api.inspect_image(full_image)

                if 'RepoDigests' in image_info and image_info['RepoDigests']:
                    for repo_digest in image_info['RepoDigests']:
                        if '@sha256:' in repo_digest:
                            return repo_digest.split('@')[1]

                # Fallback to image ID
                if 'Id' in image_info and image_info['Id'].startswith('sha256:'):
                    return image_info['Id']

            except docker.errors.ImageNotFound:
                logger.debug(f"Image {full_image} not found locally, trying to pull manifest info")
            except docker.errors.APIError as e:
                logger.debug(f"API inspect failed for {full_image}: {e}")

            # Method 3: Pull image info only (manifest) without downloading layers
            try:
                # This will pull the manifest but not the image layers
                image = self.client.images.pull(full_image, platform=None)
                if hasattr(image, 'id') and image.id:
                    digest = image.id
                    # Remove the pulled image to save space
                    try:
                        self.client.images.remove(image.id, force=True)
                    except:
                        pass  # Ignore cleanup errors
                    return digest

            except Exception as e:
                logger.debug(f"Pull method failed for {full_image}: {e}")

            logger.warning(f"Could not get remote digest for {full_image}")
            return None

        except docker.errors.NotFound:
            logger.warning(f"Image {full_image} not found in registry")
            return None
        except docker.errors.APIError as e:
            logger.warning(f"API error getting remote digest for {full_image}: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error getting remote digest for {full_image}: {e}")
            return None

    def check_container_updates(self, container_info: ContainerInfo) -> Dict[str, Any]:
        """
        Check if a container has updates available.

        Args:
            container_info: Container information

        Returns:
            Dictionary with update information
        """
        try:
            # Get remote digest
            remote_digest = self.get_remote_image_digest(
                container_info.image_name,
                container_info.image_tag
            )

            if not remote_digest:
                return {
                    'container_name': container_info.container_name,
                    'image': f"{container_info.image_name}:{container_info.image_tag}",
                    'current_digest': container_info.digest,
                    'remote_digest': None,
                    'update_available': False,
                    'error': 'Could not fetch remote digest'
                }

            # Compare digests
            update_available = container_info.digest != remote_digest

            return {
                'container_name': container_info.container_name,
                'image': f"{container_info.image_name}:{container_info.image_tag}",
                'current_digest': container_info.digest,
                'remote_digest': remote_digest,
                'update_available': update_available,
                'error': None
            }

        except Exception as e:
            logger.error(f"Error checking updates for {container_info.container_name}: {e}")
            return {
                'container_name': container_info.container_name,
                'image': f"{container_info.image_name}:{container_info.image_tag}",
                'current_digest': container_info.digest,
                'remote_digest': None,
                'update_available': False,
                'error': str(e)
            }