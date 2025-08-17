"""Views for the containers app."""

import json
import logging
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

# Import the existing tracker
try:
    from src.tracker import ContainerTracker
    from src.models import ContainerInfo, DigestChange
except ImportError as e:
    logging.error(f"Failed to import tracker: {e}")
    ContainerTracker = None

logger = logging.getLogger(__name__)


def get_tracker():
    """Get a ContainerTracker instance."""
    if ContainerTracker is None:
        raise ImportError("ContainerTracker not available")
    return ContainerTracker()


def dashboard(request):
    """Main dashboard view."""
    try:
        tracker = get_tracker()

        # Get basic statistics
        containers = tracker.get_container_status()
        total_containers = len(containers)
        running_containers = sum(1 for c in containers if c['is_running'])
        stopped_containers = total_containers - running_containers

        # Get recent activity
        report_data = tracker.generate_report()
        recent_changes = []
        if report_data.get('success'):
            raw_changes = report_data.get('recent_changes', [])[:5]  # Last 5 changes

            # Enrich changes with image information
            for change in raw_changes:
                # Get container info for this change
                container_info = None
                for container in containers:
                    if container['container_name'] == change.container_name:
                        container_info = container
                        break

                if container_info:
                    # Add image name to the change object
                    change.image_name = container_info['image'].split(':')[0]  # Extract image name from image:tag
                else:
                    # Fallback if container not found in current containers
                    change.image_name = 'unknown'

                recent_changes.append(change)

        context = {
            'total_containers': total_containers,
            'running_containers': running_containers,
            'stopped_containers': stopped_containers,
            'recent_changes': recent_changes,
            'containers': containers[:6],  # Show first 6 containers on dashboard
        }

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        context = {
            'error': str(e),
            'total_containers': 0,
            'running_containers': 0,
            'stopped_containers': 0,
            'recent_changes': [],
            'containers': [],
        }

    return render(request, 'containers/dashboard.html', context)


def container_status(request):
    """Container status view with update information."""
    try:
        tracker = get_tracker()

        # Get container status
        containers = tracker.get_container_status()

        # Get update information
        update_result = tracker.check_for_updates()
        update_by_name = {}

        if update_result.get('success', False):
            for update_info in update_result.get('containers', []):
                update_by_name[update_info['container_name']] = update_info

        # Combine data
        containers_data = []
        for container in containers:
            container_data = container.copy()
            container_data['update_info'] = update_by_name.get(container['container_name'], {})
            containers_data.append(container_data)

        context = {
            'containers': containers_data,
            'update_check_success': update_result.get('success', False),
            'update_errors': update_result.get('errors', []),
        }

    except Exception as e:
        logger.error(f"Container status error: {e}")
        context = {
            'error': str(e),
            'containers': [],
            'update_check_success': False,
            'update_errors': [],
        }

    return render(request, 'containers/container_status.html', context)


def container_detail(request, container_name):
    """Container detail view for individual management."""
    try:
        tracker = get_tracker()

        # Get container history
        history_result = tracker.get_container_history(container_name)

        if not history_result.get('success', False):
            context = {
                'error': history_result.get('error', 'Container not found'),
                'container_name': container_name,
            }
            return render(request, 'containers/container_detail.html', context)

        # Get update information for this container
        update_result = tracker.check_for_updates()
        container_update_info = {}

        if update_result.get('success', False):
            for update_info in update_result.get('containers', []):
                if update_info['container_name'] == container_name:
                    container_update_info = update_info
                    break

        context = {
            'container_name': container_name,
            'container_info': history_result['current_info'],
            'is_running': history_result['is_running'],
            'digest_changes': history_result['digest_changes'][:10],  # Last 10 changes
            'total_changes': history_result['total_changes'],
            'update_info': container_update_info,
        }

    except Exception as e:
        logger.error(f"Container detail error: {e}")
        context = {
            'error': str(e),
            'container_name': container_name,
        }

    return render(request, 'containers/container_detail.html', context)


def container_history(request, container_name):
    """Container history view."""
    try:
        tracker = get_tracker()

        # Get container history
        history_result = tracker.get_container_history(container_name)

        if not history_result.get('success', False):
            context = {
                'error': history_result.get('error', 'Container not found'),
                'container_name': container_name,
            }
            return render(request, 'containers/container_history.html', context)

        context = {
            'container_name': container_name,
            'container_info': history_result['current_info'],
            'is_running': history_result['is_running'],
            'digest_changes': history_result['digest_changes'],
            'total_changes': history_result['total_changes'],
        }

    except Exception as e:
        logger.error(f"Container history error: {e}")
        context = {
            'error': str(e),
            'container_name': container_name,
        }

    return render(request, 'containers/container_history.html', context)


def generate_report(request):
    """Generate and display comprehensive report."""
    try:
        tracker = get_tracker()

        # Generate report
        report_result = tracker.generate_report()

        if not report_result.get('success', False):
            context = {
                'error': report_result.get('error', 'Failed to generate report'),
            }
            return render(request, 'containers/report.html', context)

        # Enrich recent changes with image information
        raw_changes = report_result['recent_changes'][:20]  # Last 20 changes
        enriched_changes = []
        containers = report_result['containers']

        for change in raw_changes:
            # Get container info for this change
            container_info = None
            for container in containers:
                if container['container_name'] == change.container_name:
                    container_info = container
                    break

            if container_info:
                # Add image name to the change object
                change.image_name = container_info['image'].split(':')[0]  # Extract image name from image:tag
            else:
                # Fallback if container not found in current containers
                change.image_name = 'unknown'

            enriched_changes.append(change)

        context = {
            'report': report_result,
            'summary': report_result['summary'],
            'containers': report_result['containers'],
            'recent_changes': enriched_changes,
            'projects': report_result['projects'],
            'generated_at': report_result['generated_at'],
        }

    except Exception as e:
        logger.error(f"Report generation error: {e}")
        context = {
            'error': str(e),
        }

    return render(request, 'containers/report.html', context)


def settings(request):
    """Settings view."""
    try:
        tracker = get_tracker()

        # Check Docker availability
        docker_available = tracker.docker_scanner.is_docker_available()

        context = {
            'docker_available': docker_available,
            'database_path': '~/.dockge-companion/containers.db',
            'docker_socket': 'unix://var/run/docker.sock',
        }

    except Exception as e:
        logger.error(f"Settings error: {e}")
        context = {
            'error': str(e),
            'docker_available': False,
        }

    return render(request, 'containers/settings.html', context)


# API endpoints for AJAX

@require_http_methods(["POST"])
@csrf_exempt
def api_scan_containers(request):
    """API endpoint to scan containers."""
    try:
        tracker = get_tracker()

        # Perform scan
        result = tracker.scan_and_update(include_stopped=True)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"API scan error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["POST"])
@csrf_exempt
def api_check_updates(request):
    """API endpoint to check for updates."""
    try:
        tracker = get_tracker()

        # Check for updates
        result = tracker.check_for_updates()

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"API update check error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["GET"])
def api_container_status(request):
    """API endpoint to get container status."""
    try:
        tracker = get_tracker()

        # Get container status
        containers = tracker.get_container_status()

        return JsonResponse({
            'success': True,
            'containers': containers
        })

    except Exception as e:
        logger.error(f"API container status error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@require_http_methods(["GET"])
def api_container_updates(request, container_name):
    """API endpoint to get updates for a specific container."""
    try:
        tracker = get_tracker()

        # Check for updates
        update_result = tracker.check_for_updates()

        if not update_result.get('success', False):
            return JsonResponse({
                'success': False,
                'error': update_result.get('error', 'Update check failed')
            })

        # Find the specific container
        container_update_info = None
        for update_info in update_result.get('containers', []):
            if update_info['container_name'] == container_name:
                container_update_info = update_info
                break

        if container_update_info is None:
            return JsonResponse({
                'success': False,
                'error': f'Container {container_name} not found'
            })

        return JsonResponse({
            'success': True,
            'container': container_update_info
        })

    except Exception as e:
        logger.error(f"API container updates error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
