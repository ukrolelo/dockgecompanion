"""Interactive Terminal User Interface for Dockge Companion."""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional, Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.align import Align
    from rich.columns import Columns
    from rich.prompt import Prompt, Confirm
    import curses
    import threading
except ImportError:
    print("❌ Required packages not installed. Please install:")
    print("   pip install rich")
    sys.exit(1)

from .tracker import ContainerTracker
from .database import DatabaseManager
from .docker_scanner import DockerScanner
from .models import ContainerInfo


class DockgeCompanionTUI:
    """Interactive Terminal User Interface for Dockge Companion."""
    
    def __init__(self):
        self.console = Console()
        self.tracker = ContainerTracker()
        self.current_menu = "main"
        self.selected_index = 0
        self.containers_data = []
        self.running = True
        
        # Menu definitions
        self.main_menu_items = [
            "📊 View Container Status",
            "🔍 Check for Updates", 
            "📋 Container History",
            "🔄 Scan Containers",
            "📈 Generate Report",
            "⚙️  Settings",
            "❌ Exit"
        ]
        
        self.container_actions = [
            "📋 View History",
            "💾 Backup Current Version",
            "🔄 Rollback Version",
            "🔍 Check Updates",
            "⬅️  Back to Main Menu"
        ]
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def create_header(self) -> Panel:
        """Create the application header."""
        header_text = Text("🐳 Dockge Companion - Interactive Mode", style="bold blue")
        subtitle = Text("Navigate with ↑↓ arrows, Enter to select, ESC to go back", style="dim")
        header_content = Align.center(Text.assemble(header_text, "\n", subtitle))
        return Panel(header_content, style="blue")
    
    def create_main_menu(self) -> Table:
        """Create the main menu table."""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Menu", style="cyan", no_wrap=True)
        
        for i, item in enumerate(self.main_menu_items):
            style = "bold green" if i == self.selected_index else "white"
            prefix = "► " if i == self.selected_index else "  "
            table.add_row(f"{prefix}{item}", style=style)
        
        return table
    
    def create_container_list(self) -> Table:
        """Create a table showing container status with update information."""
        table = Table(title="Container Status", show_header=True, header_style="bold magenta")
        table.add_column("Container", style="cyan", no_wrap=True)
        table.add_column("Image", style="yellow")
        table.add_column("Status", justify="center")
        table.add_column("Current Version", style="dim")
        table.add_column("Available", style="dim")
        table.add_column("Updates", justify="center")
        
        if not self.containers_data:
            table.add_row("No containers found", "", "", "", "", "")
            return table
        
        for i, container in enumerate(self.containers_data):
            # Style based on selection
            name_style = "bold green" if i == self.selected_index else "cyan"
            prefix = "► " if i == self.selected_index else "  "
            
            # Status indicators
            status = "🟢 Running" if container.get('is_running', False) else "🔴 Stopped"
            
            # Update status
            update_info = container.get('update_info', {})
            if update_info.get('update_available', False):
                update_status = "🆙 Available"
                update_style = "bold yellow"
            elif update_info.get('error'):
                update_status = "❌ Error"
                update_style = "red"
            else:
                update_status = "✅ Latest"
                update_style = "green"
            
            # Version info (shortened)
            current_version = container.get('digest_short', 'unknown')
            remote_version = update_info.get('remote_digest', '')[:12] + '...' if update_info.get('remote_digest') else 'N/A'
            
            table.add_row(
                f"{prefix}{container.get('container_name', 'unknown')}",
                container.get('image', 'unknown'),
                status,
                current_version,
                remote_version,
                Text(update_status, style=update_style)
            )
        
        return table
    
    def create_container_actions_menu(self, container_name: str) -> Table:
        """Create actions menu for a specific container."""
        table = Table(title=f"Actions for: {container_name}", show_header=False, box=None, padding=(0, 2))
        table.add_column("Action", style="cyan", no_wrap=True)
        
        for i, action in enumerate(self.container_actions):
            style = "bold green" if i == self.selected_index else "white"
            prefix = "► " if i == self.selected_index else "  "
            table.add_row(f"{prefix}{action}", style=style)
        
        return table
    
    def load_container_data(self):
        """Load container data with update information."""
        try:
            # Get container status
            containers = self.tracker.get_container_status()
            
            # Get update information
            update_result = self.tracker.check_for_updates()
            update_by_name = {}
            
            if update_result.get('success', False):
                for update_info in update_result.get('containers', []):
                    update_by_name[update_info['container_name']] = update_info
            
            # Combine data
            self.containers_data = []
            for container in containers:
                container_data = container.copy()
                container_data['update_info'] = update_by_name.get(container['container_name'], {})
                self.containers_data.append(container_data)
                
        except Exception as e:
            self.console.print(f"❌ Error loading container data: {e}", style="red")
            self.containers_data = []
    
    def show_container_history(self, container_name: str):
        """Show detailed history for a container."""
        try:
            result = self.tracker.get_container_history(container_name)
            
            if not result.get('success', False):
                self.console.print(f"❌ Error: {result.get('error', 'Unknown error')}", style="red")
                input("\nPress Enter to continue...")
                return
            
            self.clear_screen()
            
            # Container info
            container = result['current_info']
            info_table = Table(title=f"Container: {container_name}", show_header=False)
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="white")
            
            info_table.add_row("Image", f"{container.image_name}:{container.image_tag}")
            info_table.add_row("Service", container.service_name or "N/A")
            info_table.add_row("Project", container.project_name or "N/A")
            info_table.add_row("Current Digest", container.digest)
            info_table.add_row("Status", "🟢 Running" if result['is_running'] else "🔴 Stopped")
            
            self.console.print(info_table)
            self.console.print()
            
            # History
            changes = result.get('digest_changes', [])
            if changes:
                history_table = Table(title="Digest Change History", show_header=True)
                history_table.add_column("Date", style="cyan")
                history_table.add_column("Time", style="cyan")
                history_table.add_column("From", style="red")
                history_table.add_column("To", style="green")
                
                for change in changes:
                    history_table.add_row(
                        change.change_timestamp.strftime('%Y-%m-%d'),
                        change.change_timestamp.strftime('%H:%M:%S'),
                        change.old_digest[:16] + '...',
                        change.new_digest[:16] + '...'
                    )
                
                self.console.print(history_table)
            else:
                self.console.print("✅ No digest changes recorded for this container.", style="green")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            self.console.print(f"❌ Error showing history: {e}", style="red")
            input("\nPress Enter to continue...")
    
    def backup_current_version(self, container_name: str):
        """Backup current version to database."""
        try:
            # Perform a scan to update database with current state
            result = self.tracker.scan_and_update()
            
            if result.get('success', False):
                self.console.print(f"✅ Current version of {container_name} backed up to database!", style="green")
            else:
                self.console.print(f"❌ Failed to backup: {result.get('error', 'Unknown error')}", style="red")
                
        except Exception as e:
            self.console.print(f"❌ Error backing up version: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def show_rollback_options(self, container_name: str):
        """Show rollback options for a container."""
        try:
            result = self.tracker.get_container_history(container_name)
            
            if not result.get('success', False):
                self.console.print(f"❌ Error: {result.get('error', 'Unknown error')}", style="red")
                input("\nPress Enter to continue...")
                return
            
            changes = result.get('digest_changes', [])
            if not changes:
                self.console.print("ℹ️  No previous versions available for rollback.", style="yellow")
                input("\nPress Enter to continue...")
                return
            
            self.clear_screen()
            
            # Show rollback options
            rollback_table = Table(title=f"Rollback Options for: {container_name}", show_header=True)
            rollback_table.add_column("#", style="cyan", width=3)
            rollback_table.add_column("Date", style="cyan")
            rollback_table.add_column("Time", style="cyan")
            rollback_table.add_column("Digest", style="yellow")
            rollback_table.add_column("Action", style="green")
            
            for i, change in enumerate(changes[:10]):  # Show last 10 changes
                rollback_table.add_row(
                    str(i + 1),
                    change.change_timestamp.strftime('%Y-%m-%d'),
                    change.change_timestamp.strftime('%H:%M:%S'),
                    change.old_digest[:20] + '...',
                    "← Rollback to this version"
                )
            
            self.console.print(rollback_table)
            self.console.print()
            
            # Instructions for rollback
            instructions = Panel(
                Text.assemble(
                    "🔄 To rollback:\n\n",
                    "1. Note the digest you want to rollback to\n",
                    "2. Update your docker-compose.yml:\n",
                    "   Change: ", ("image: nginx:latest", "yellow"), "\n",
                    "   To: ", ("image: nginx@sha256:digest-here", "green"), "\n",
                    "3. Run: ", ("docker-compose up -d", "cyan"), "\n",
                    "4. Run: ", ("python dockge_companion.py scan", "cyan"), " to record the change"
                ),
                title="Rollback Instructions",
                style="blue"
            )
            
            self.console.print(instructions)
            input("\nPress Enter to continue...")
            
        except Exception as e:
            self.console.print(f"❌ Error showing rollback options: {e}", style="red")
            input("\nPress Enter to continue...")
    
    def handle_container_actions(self, container_name: str):
        """Handle actions for a specific container."""
        self.selected_index = 0
        
        while True:
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            # Show container actions menu
            actions_menu = self.create_container_actions_menu(container_name)
            self.console.print(Align.center(actions_menu))
            
            # Handle input
            try:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    if event.name == 'up':
                        self.selected_index = (self.selected_index - 1) % len(self.container_actions)
                    elif event.name == 'down':
                        self.selected_index = (self.selected_index + 1) % len(self.container_actions)
                    elif event.name == 'enter':
                        action = self.container_actions[self.selected_index]
                        
                        if "View History" in action:
                            self.show_container_history(container_name)
                        elif "Backup Current Version" in action:
                            self.backup_current_version(container_name)
                        elif "Rollback Version" in action:
                            self.show_rollback_options(container_name)
                        elif "Check Updates" in action:
                            self.check_single_container_updates(container_name)
                        elif "Back to Main Menu" in action:
                            return
                    elif event.name == 'esc':
                        return
            except KeyboardInterrupt:
                return
    
    def check_single_container_updates(self, container_name: str):
        """Check updates for a single container."""
        try:
            self.console.print(f"🔍 Checking updates for {container_name}...", style="yellow")
            
            # Find container info
            container_info = None
            for container in self.containers_data:
                if container['container_name'] == container_name:
                    container_info = container
                    break
            
            if not container_info:
                self.console.print("❌ Container not found", style="red")
                input("\nPress Enter to continue...")
                return
            
            # Check for updates (this will be implemented in the update check)
            update_result = self.tracker.check_for_updates()
            
            if update_result.get('success', False):
                for update_info in update_result.get('containers', []):
                    if update_info['container_name'] == container_name:
                        if update_info.get('update_available', False):
                            self.console.print(f"🆙 Update available for {container_name}!", style="green")
                            self.console.print(f"Current: {update_info['current_digest'][:20]}...")
                            self.console.print(f"Remote:  {update_info['remote_digest'][:20]}...")
                        else:
                            self.console.print(f"✅ {container_name} is up to date!", style="green")
                        break
            else:
                self.console.print(f"❌ Failed to check updates: {update_result.get('error', 'Unknown error')}", style="red")
                
        except Exception as e:
            self.console.print(f"❌ Error checking updates: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def handle_main_menu(self):
        """Handle main menu navigation and actions."""
        while self.running:
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            # Show main menu
            main_menu = self.create_main_menu()
            self.console.print(Align.center(main_menu))
            
            # Handle input
            try:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    if event.name == 'up':
                        self.selected_index = (self.selected_index - 1) % len(self.main_menu_items)
                    elif event.name == 'down':
                        self.selected_index = (self.selected_index + 1) % len(self.main_menu_items)
                    elif event.name == 'enter':
                        self.handle_main_menu_selection()
                    elif event.name == 'esc' or event.name == 'q':
                        self.running = False
            except KeyboardInterrupt:
                self.running = False
    
    def handle_main_menu_selection(self):
        """Handle main menu item selection."""
        selected_item = self.main_menu_items[self.selected_index]
        
        if "View Container Status" in selected_item:
            self.show_container_status()
        elif "Check for Updates" in selected_item:
            self.check_all_updates()
        elif "Container History" in selected_item:
            self.select_container_for_history()
        elif "Scan Containers" in selected_item:
            self.scan_containers()
        elif "Generate Report" in selected_item:
            self.generate_report()
        elif "Settings" in selected_item:
            self.show_settings()
        elif "Exit" in selected_item:
            self.running = False
    
    def show_container_status(self):
        """Show container status with navigation."""
        self.load_container_data()
        self.selected_index = 0
        
        while True:
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            # Show container list
            container_table = self.create_container_list()
            self.console.print(container_table)
            
            if self.containers_data:
                self.console.print("\n💡 Press Enter to manage selected container, ESC to go back", style="dim")
            else:
                self.console.print("\n💡 Press ESC to go back", style="dim")
            
            # Handle input
            try:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    if event.name == 'up' and self.containers_data:
                        self.selected_index = (self.selected_index - 1) % len(self.containers_data)
                    elif event.name == 'down' and self.containers_data:
                        self.selected_index = (self.selected_index + 1) % len(self.containers_data)
                    elif event.name == 'enter' and self.containers_data:
                        selected_container = self.containers_data[self.selected_index]
                        self.handle_container_actions(selected_container['container_name'])
                    elif event.name == 'esc':
                        break
                    elif event.name == 'r':  # Refresh
                        self.load_container_data()
            except KeyboardInterrupt:
                break
    
    def check_all_updates(self):
        """Check updates for all containers."""
        self.clear_screen()
        self.console.print(self.create_header())
        self.console.print()
        
        with self.console.status("[bold green]Checking for updates...") as status:
            try:
                result = self.tracker.check_for_updates()
                
                if result.get('success', False):
                    total = result['total_containers']
                    available = result['updates_available']
                    
                    self.console.print(f"✅ Update check complete!", style="green")
                    self.console.print(f"📦 Total containers: {total}")
                    self.console.print(f"🆙 Updates available: {available}")
                    
                    if available > 0:
                        self.console.print(f"\n⚠️  {available} container(s) have updates available", style="yellow")
                        
                        # Show which containers have updates
                        for container in result['containers']:
                            if container.get('update_available', False):
                                self.console.print(f"  🆙 {container['container_name']}: {container['image']}", style="yellow")
                    else:
                        self.console.print("✅ All containers are up to date!", style="green")
                        
                else:
                    self.console.print(f"❌ Update check failed: {result.get('error', 'Unknown error')}", style="red")
                    
            except Exception as e:
                self.console.print(f"❌ Error checking updates: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def select_container_for_history(self):
        """Let user select a container to view history."""
        if not self.containers_data:
            self.load_container_data()
        
        if not self.containers_data:
            self.console.print("❌ No containers found", style="red")
            input("\nPress Enter to continue...")
            return
        
        self.selected_index = 0
        
        while True:
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            self.console.print("Select container to view history:", style="bold cyan")
            self.console.print()
            
            # Show container selection
            for i, container in enumerate(self.containers_data):
                style = "bold green" if i == self.selected_index else "white"
                prefix = "► " if i == self.selected_index else "  "
                self.console.print(f"{prefix}{container['container_name']} ({container['image']})", style=style)
            
            self.console.print("\n💡 Press Enter to select, ESC to go back", style="dim")
            
            # Handle input
            try:
                event = keyboard.read_event()
                if event.event_type == keyboard.KEY_DOWN:
                    if event.name == 'up':
                        self.selected_index = (self.selected_index - 1) % len(self.containers_data)
                    elif event.name == 'down':
                        self.selected_index = (self.selected_index + 1) % len(self.containers_data)
                    elif event.name == 'enter':
                        selected_container = self.containers_data[self.selected_index]
                        self.show_container_history(selected_container['container_name'])
                        break
                    elif event.name == 'esc':
                        break
            except KeyboardInterrupt:
                break
    
    def scan_containers(self):
        """Scan containers and update database."""
        self.clear_screen()
        self.console.print(self.create_header())
        self.console.print()
        
        with self.console.status("[bold green]Scanning containers...") as status:
            try:
                result = self.tracker.scan_and_update(include_stopped=True)
                
                if result.get('success', False):
                    self.console.print("✅ Container scan completed!", style="green")
                    self.console.print(f"📦 Containers scanned: {result['containers_scanned']}")
                    self.console.print(f"🔄 Changes detected: {result['changes_detected']}")
                    self.console.print(f"🆕 New containers: {result['new_containers']}")
                    self.console.print(f"🕐 Scan time: {result['scan_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    self.console.print(f"❌ Scan failed: {result.get('error', 'Unknown error')}", style="red")
                    
            except Exception as e:
                self.console.print(f"❌ Error during scan: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def generate_report(self):
        """Generate and display comprehensive report."""
        self.clear_screen()
        self.console.print(self.create_header())
        self.console.print()
        
        with self.console.status("[bold green]Generating report...") as status:
            try:
                result = self.tracker.generate_report()
                
                if result.get('success', False):
                    summary = result['summary']
                    
                    # Summary table
                    summary_table = Table(title="Summary Report", show_header=False)
                    summary_table.add_column("Metric", style="cyan")
                    summary_table.add_column("Value", style="white")
                    
                    summary_table.add_row("Total Containers", str(summary['total_containers']))
                    summary_table.add_row("Running", str(summary['running_containers']))
                    summary_table.add_row("Stopped", str(summary['stopped_containers']))
                    summary_table.add_row("With Changes", str(summary['containers_with_changes']))
                    summary_table.add_row("Projects", str(summary['total_projects']))
                    summary_table.add_row("Recent Changes (7 days)", str(summary['recent_changes_7days']))
                    
                    self.console.print(summary_table)
                    
                    # Recent changes
                    if result['recent_changes']:
                        self.console.print()
                        changes_table = Table(title="Recent Changes", show_header=True)
                        changes_table.add_column("Container", style="cyan")
                        changes_table.add_column("Date", style="yellow")
                        changes_table.add_column("Change", style="green")
                        
                        for change in result['recent_changes'][:10]:
                            changes_table.add_row(
                                change.container_name,
                                change.change_timestamp.strftime('%Y-%m-%d %H:%M'),
                                f"{change.old_digest[:8]}... → {change.new_digest[:8]}..."
                            )
                        
                        self.console.print(changes_table)
                    
                    # Projects
                    if result['projects']:
                        self.console.print()
                        self.console.print(f"📁 Projects: {', '.join(result['projects'])}", style="blue")
                        
                else:
                    self.console.print(f"❌ Report generation failed: {result.get('error', 'Unknown error')}", style="red")
                    
            except Exception as e:
                self.console.print(f"❌ Error generating report: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def show_settings(self):
        """Show settings and configuration options."""
        self.clear_screen()
        self.console.print(self.create_header())
        self.console.print()
        
        settings_info = Panel(
            Text.assemble(
                "⚙️  Settings & Configuration\n\n",
                "Database Location: ", ("~/.dockge-companion/containers.db", "yellow"), "\n",
                "Docker Socket: ", ("unix://var/run/docker.sock", "yellow"), "\n\n",
                "Available Actions:\n",
                "• View database location\n",
                "• Clear database (reset all data)\n",
                "• Export data to JSON\n",
                "• View logs\n\n",
                "Press ESC to go back"
            ),
            title="Settings",
            style="blue"
        )
        
        self.console.print(settings_info)
        input("\nPress Enter to continue...")
    
    def run(self):
        """Run the interactive TUI."""
        try:
            # Check if Docker is available
            if not self.tracker.docker_scanner.is_docker_available():
                self.console.print("❌ Docker is not available or accessible", style="red")
                self.console.print("Please make sure Docker is running and accessible.", style="yellow")
                return
            
            # Load initial data
            self.load_container_data()
            
            # Show welcome message
            self.clear_screen()
            welcome = Panel(
                Text.assemble(
                    "🐳 Welcome to Dockge Companion Interactive Mode!\n\n",
                    "Navigation:\n",
                    "• Use ↑↓ arrow keys to navigate\n",
                    "• Press Enter to select\n",
                    "• Press ESC to go back\n",
                    "• Press 'q' to quit\n\n",
                    "Press any key to continue..."
                ),
                title="Welcome",
                style="green"
            )
            self.console.print(Align.center(welcome))
            
            # Wait for any key
            keyboard.read_event()
            
            # Start main menu loop
            self.handle_main_menu()
            
            # Goodbye message
            self.clear_screen()
            self.console.print("👋 Thank you for using Dockge Companion!", style="green")
            
        except KeyboardInterrupt:
            self.clear_screen()
            self.console.print("👋 Goodbye!", style="green")
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e}", style="red")


def main():
    """Main entry point for the TUI."""
    tui = DockgeCompanionTUI()
    tui.run()


if __name__ == "__main__":
    main()