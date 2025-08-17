"""Data models for container tracking."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ContainerInfo:
    """Represents a Docker container's information."""
    container_id: str
    container_name: str
    service_name: Optional[str]
    image_name: str
    image_tag: str
    digest: str
    project_name: Optional[str]
    created_at: datetime
    
    def __str__(self):
        return f"{self.container_name} ({self.image_name}:{self.image_tag})"


@dataclass
class DigestChange:
    """Represents a change in container digest."""
    container_name: str
    old_digest: str
    new_digest: str
    change_timestamp: datetime
    
    def __str__(self):
        return f"{self.container_name}: {self.old_digest[:12]}... -> {self.new_digest[:12]}..."