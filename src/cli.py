"""Command-line interface for Dockge Companion."""

import click
import logging
import sys
from datetime import datetime
from tabulate import tabulate

from .tracker import ContainerTracker
from .database import DatabaseManager
from .docker_scanner import DockerScanner


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', '-q', is_flag=True, help='Suppress non-error output')
def main(verbose, quiet):
    """Dockge Companion - Docker Container Digest Tracker"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


@main.command()
def init():
    """Initialize the database and perform first scan."""
    click.echo("🚀 Initializing Dockge Companion...")
    
    try:
        tracker = ContainerTracker()
        
        if tracker.initialize():
            click.echo("✅ Initialization completed successfully!")
            click.echo("You can now use 'scan', 'status', and other commands.")
        else:
            click.echo("❌ Initialization failed. Check logs for details.")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Initialization error: {e}")
        sys.exit(1)


@main.command()
@click.option('--exclude-stopped', is_flag=True, help='Exclude stopped containers (includes them by default)')
def scan(exclude_stopped):
    """Scan current containers and update database."""
    click.echo("🔍 Scanning containers...")
    
    try:
        tracker = ContainerTracker()
        result = tracker.scan_and_update(include_stopped=not exclude_stopped)
        
        if result['success']:
            click.echo(f"✅ Scan completed at {result['scan_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"   📦 Containers scanned: {result['containers_scanned']}")

            # Show scanned container names
            if result.get('scanned_container_names'):
                container_list = ", ".join(result['scanned_container_names'])
                click.echo(f"   📋 Scanned: {container_list}")

            click.echo(f"   🔄 Changes detected: {result['changes_detected']}")
            if result.get('changed_container_names'):
                changed_list = ", ".join(result['changed_container_names'])
                click.echo(f"   🔄 Changed: {changed_list}")

            click.echo(f"   🆕 New containers: {result['new_containers']}")
            if result.get('new_container_names'):
                new_list = ", ".join(result['new_container_names'])
                click.echo(f"   🆕 New: {new_list}")
        else:
            click.echo(f"❌ Scan failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Scan error: {e}")
        sys.exit(1)


@main.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def status(format):
    """Show current status of all tracked containers."""
    try:
        tracker = ContainerTracker()
        containers = tracker.get_container_status()
        
        if not containers:
            click.echo("No containers are currently being tracked.")
            click.echo("Run 'init' or 'scan' to start tracking containers.")
            return
        
        if format == 'json':
            import json
            click.echo(json.dumps(containers, indent=2, default=str))
        else:
            # Table format
            headers = ['Container', 'Service', 'Image', 'Digest', 'Status', 'Project', 'Changes']
            rows = []
            
            for container in containers:
                status_icon = "🟢" if container['is_running'] else "🔴"
                status_text = "Running" if container['is_running'] else "Stopped"
                
                rows.append([
                    container['container_name'],
                    container['service_name'] or '-',
                    container['image'],
                    container['digest_short'],
                    f"{status_icon} {status_text}",
                    container['project_name'] or '-',
                    container['change_count']
                ])
            
            click.echo(f"\n📊 Container Status ({len(containers)} containers)")
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
            
    except Exception as e:
        click.echo(f"❌ Status error: {e}")
        sys.exit(1)


@main.command()
@click.option('--hours', default=24, help='Compare with state from N hours ago')
def compare(hours):
    """Compare current state with previous scan."""
    try:
        tracker = ContainerTracker()
        result = tracker.compare_with_previous(hours)
        
        if not result['success']:
            click.echo(f"❌ Comparison failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        click.echo(f"🔍 Comparison with state from {hours} hours ago")
        click.echo(f"   📦 Total containers: {result['total_containers']}")
        click.echo(f"   🔄 Changed containers: {len(result['changed'])}")
        click.echo(f"   🆕 New containers: {len(result['new_containers'])}")
        click.echo(f"   ✅ Unchanged containers: {len(result['unchanged'])}")
        
        # Show changed containers
        if result['changed']:
            click.echo(f"\n🔄 Changed Containers:")
            for item in result['changed']:
                container = item['container']
                changes = item['changes']
                click.echo(f"   • {container.container_name} ({len(changes)} changes)")
                for change in changes[:3]:  # Show up to 3 recent changes
                    click.echo(f"     - {change.change_timestamp.strftime('%Y-%m-%d %H:%M')} "
                             f"{change.old_digest[:12]}... → {change.new_digest[:12]}...")
        
        # Show new containers
        if result['new_containers']:
            click.echo(f"\n🆕 New Containers:")
            for container in result['new_containers']:
                click.echo(f"   • {container.container_name} ({container.image_name}:{container.image_tag})")
        
    except Exception as e:
        click.echo(f"❌ Comparison error: {e}")
        sys.exit(1)


@main.command()
@click.argument('container_name')
def history(container_name):
    """Show digest history for a specific container."""
    try:
        tracker = ContainerTracker()
        result = tracker.get_container_history(container_name)
        
        if not result['success']:
            click.echo(f"❌ {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        container = result['current_info']
        changes = result['digest_changes']
        
        click.echo(f"📋 History for container: {container_name}")
        click.echo(f"   Image: {container.image_name}:{container.image_tag}")
        click.echo(f"   Service: {container.service_name or 'N/A'}")
        click.echo(f"   Project: {container.project_name or 'N/A'}")
        click.echo(f"   Current Digest: {container.digest}")
        click.echo(f"   Status: {'🟢 Running' if result['is_running'] else '🔴 Stopped'}")
        
        if changes:
            click.echo(f"\n🔄 Digest Changes ({len(changes)} total):")
            headers = ['Date', 'Time', 'Old Digest', 'New Digest']
            rows = []
            
            for change in changes:
                rows.append([
                    change.change_timestamp.strftime('%Y-%m-%d'),
                    change.change_timestamp.strftime('%H:%M:%S'),
                    change.old_digest[:16] + '...',
                    change.new_digest[:16] + '...'
                ])
            
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
        else:
            click.echo("\n✅ No digest changes recorded for this container.")
            
    except Exception as e:
        click.echo(f"❌ History error: {e}")
        sys.exit(1)


@main.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def report(format):
    """Generate comprehensive report of all containers."""
    try:
        tracker = ContainerTracker()
        result = tracker.generate_report()
        
        if not result['success']:
            click.echo(f"❌ Report generation failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
        
        if format == 'json':
            import json
            click.echo(json.dumps(result, indent=2, default=str))
            return
        
        # Table format
        summary = result['summary']
        
        click.echo(f"📊 Dockge Companion Report")
        click.echo(f"Generated: {result['generated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"\n📈 Summary:")
        click.echo(f"   Total Containers: {summary['total_containers']}")
        click.echo(f"   Running: {summary['running_containers']}")
        click.echo(f"   Stopped: {summary['stopped_containers']}")
        click.echo(f"   With Changes: {summary['containers_with_changes']}")
        click.echo(f"   Projects: {summary['total_projects']}")
        click.echo(f"   Recent Changes (7 days): {summary['recent_changes_7days']}")
        
        # Recent changes
        if result['recent_changes']:
            click.echo(f"\n🔄 Recent Changes:")
            headers = ['Container', 'Date', 'Time', 'Change']
            rows = []
            
            for change in result['recent_changes'][:10]:  # Show last 10 changes
                rows.append([
                    change.container_name,
                    change.change_timestamp.strftime('%Y-%m-%d'),
                    change.change_timestamp.strftime('%H:%M'),
                    f"{change.old_digest[:8]}... → {change.new_digest[:8]}..."
                ])
            
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
            
            if len(result['recent_changes']) > 10:
                click.echo(f"... and {len(result['recent_changes']) - 10} more changes")
        
        # Projects
        if result['projects']:
            click.echo(f"\n📁 Projects: {', '.join(result['projects'])}")
            
    except Exception as e:
        click.echo(f"❌ Report error: {e}")
        sys.exit(1)


@main.command()
@click.option('--format', type=click.Choice(['table', 'json']), default='table', help='Output format')
def check_updates(format):
    """Check for available updates for tracked containers."""
    try:
        tracker = ContainerTracker()
        result = tracker.check_for_updates()

        if not result['success']:
            click.echo(f"❌ Update check failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)

        if format == 'json':
            import json
            click.echo(json.dumps(result, indent=2, default=str))
            return

        # Table format
        total = result['total_containers']
        available = result['updates_available']

        click.echo(f"🔍 Update Check Results")
        click.echo(f"Checked: {result['check_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"📦 Total containers: {total}")
        click.echo(f"🆙 Updates available: {available}")

        if available == 0:
            click.echo("✅ All containers are up to date!")
        else:
            click.echo(f"⚠️  {available} container(s) have updates available")

        # Show detailed results
        if result['containers']:
            click.echo(f"\n📋 Container Update Status:")
            headers = ['Container', 'Image', 'Current', 'Remote', 'Status']
            rows = []

            for container in result['containers']:
                if container.get('update_available'):
                    status = "🆙 Update Available"
                elif container.get('error'):
                    status = f"❌ {container['error']}"
                else:
                    status = "✅ Up to date"

                current_short = container['current_digest'][:16] + '...' if container['current_digest'] else 'N/A'
                remote_short = container['remote_digest'][:16] + '...' if container['remote_digest'] else 'N/A'

                rows.append([
                    container['container_name'],
                    container['image'],
                    current_short,
                    remote_short,
                    status
                ])

            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))

        # Show errors if any
        if result['errors']:
            click.echo(f"\n⚠️  Errors encountered:")
            for error in result['errors']:
                click.echo(f"   • {error}")

    except Exception as e:
        click.echo(f"❌ Update check error: {e}")
        sys.exit(1)


@main.command()
def tui():
    """Launch interactive Terminal User Interface."""
    try:
        from .tui import DockgeCompanionTUI
        tui_app = DockgeCompanionTUI()
        tui_app.run()
    except ImportError as e:
        click.echo("❌ TUI dependencies not available. Please install:")
        click.echo("   pip install rich keyboard")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ TUI error: {e}")
        sys.exit(1)


@main.command()
def version():
    """Show version information."""
    from . import __version__
    click.echo(f"Dockge Companion v{__version__}")
    click.echo("Docker Container Digest Tracker")


if __name__ == '__main__':
    main()