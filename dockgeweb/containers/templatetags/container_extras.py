"""Custom template tags for container management."""

from django import template
from urllib.parse import quote

register = template.Library()


@register.filter
def docker_hub_url(image_name, digest):
    """
    Generate a Docker Hub URL for a specific image digest.
    
    Args:
        image_name: The Docker image name (e.g., 'python', 'nginx', 'library/ubuntu')
        digest: The image digest (e.g., 'sha256:abc123...')
    
    Returns:
        A URL to the specific image layer on Docker Hub
    """
    if not image_name or not digest:
        return "#"
    
    # Handle different image name formats
    if '/' not in image_name:
        # Official images (e.g., 'python' -> 'library/python')
        namespace = 'library'
        repo = image_name
    elif image_name.count('/') == 1:
        # User/org images (e.g., 'louislam/dockge')
        namespace, repo = image_name.split('/', 1)
    else:
        # Registry images (e.g., 'registry.com/user/repo')
        # For non-Docker Hub registries, we can't generate a Docker Hub URL
        parts = image_name.split('/')
        if not parts[0].endswith('.com') and not parts[0].endswith('.io'):
            # Assume it's still Docker Hub format
            namespace = parts[0]
            repo = '/'.join(parts[1:])
        else:
            # External registry - return a generic search URL
            return f"https://hub.docker.com/search?q={quote(image_name)}"
    
    # Clean the digest (remove sha256: prefix if present)
    clean_digest = digest.replace('sha256:', '') if digest.startswith('sha256:') else digest
    
    # Generate Docker Hub layers URL
    # Format: https://hub.docker.com/layers/namespace/repo/tag/images/sha256-digest
    # Note: We use 'latest' as tag since we don't have the specific tag info in this context
    return f"https://hub.docker.com/layers/{namespace}/{repo}/latest/images/sha256-{clean_digest}"


@register.filter
def docker_hub_search_url(image_name):
    """
    Generate a Docker Hub search URL for an image.
    
    Args:
        image_name: The Docker image name
    
    Returns:
        A URL to search for the image on Docker Hub
    """
    if not image_name:
        return "#"
    
    return f"https://hub.docker.com/search?q={quote(image_name)}"


@register.filter
def format_digest_short(digest, length=12):
    """
    Format a digest to show only the first N characters.
    
    Args:
        digest: The full digest
        length: Number of characters to show (default: 12)
    
    Returns:
        Shortened digest with ellipsis
    """
    if not digest:
        return 'unknown'
    
    if len(digest) <= length:
        return digest
    
    return f"{digest[:length]}..."


@register.filter
def is_docker_hub_image(image_name):
    """
    Check if an image is from Docker Hub (vs external registry).
    
    Args:
        image_name: The Docker image name
    
    Returns:
        True if it's a Docker Hub image, False otherwise
    """
    if not image_name:
        return False
    
    # If it contains a domain (has dots), it's likely an external registry
    parts = image_name.split('/')
    if len(parts) > 1 and ('.' in parts[0] or ':' in parts[0]):
        return False
    
    return True
