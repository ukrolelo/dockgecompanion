"""Simple Interactive Terminal User Interface for Dockge Companion (no root required)."""

import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional, Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    from rich.prompt import Prompt, Confirm, IntPrompt
except ImportError:
    print("❌ Required packages not installed. Please install:")
    print("   pip install rich")
    sys.exit(1)

from .tracker import ContainerTracker
from .database import DatabaseManager
from .docker_scanner import DockerScanner
from .models import ContainerInfo


class SimpleDockgeCompanionTUI:
    """Simple Interactive Terminal User Interface for Dockge Companion."""
    
    def __init__(self):
        self.console = Console()
        self.tracker = ContainerTracker()
        self.containers_data = []
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def create_header(self) -> Panel:
        """Create the application header."""
        header_text = Text("🐳 Dockge Companion - Interactive Mode", style="bold blue")
        subtitle = Text("Navigate with numbers, Enter to select, 'q' to quit", style="dim")
        header_content = Align.center(Text.assemble(header_text, "\n", subtitle))
        return Panel(header_content, style="blue")
    
    def show_main_menu(self) -> str:
        """Show main menu and get user selection."""
        self.clear_screen()
        self.console.print(self.create_header())
        self.console.print()
        
        menu_table = Table(show_header=False, box=None, padding=(0, 2))
        menu_table.add_column("Option", style="cyan", no_wrap=True)
        menu_table.add_column("Description", style="white")
        
        menu_items = [
            ("1", "📊 View Container Status"),
            ("2", "🔍 Check for Updates"), 
            ("3", "📋 Container History"),
            ("4", "🔄 Scan Containers"),
            ("5", "📈 Generate Report"),
            ("6", "⚙️  Settings"),
            ("q", "❌ Exit")
        ]
        
        for option, description in menu_items:
            menu_table.add_row(f"[bold green]{option}[/bold green]", description)
        
        self.console.print(Align.center(menu_table))
        self.console.print()
        
        choice = Prompt.ask("Select option", choices=[item[0] for item in menu_items], default="1")
        return choice
    
    def load_container_data(self):
        """Load container data with update information."""
        try:
            with self.console.status("[bold green]Loading container data..."):
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
    
    def show_container_status(self):
        """Show container status with update information."""
        self.load_container_data()
        
        while True:
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            if not self.containers_data:
                self.console.print("❌ No containers found", style="red")
                input("\nPress Enter to continue...")
                return
            
            # Create container status table
            table = Table(title="Container Status", show_header=True, header_style="bold magenta")
            table.add_column("#", style="cyan", width=3)
            table.add_column("Container", style="cyan")
            table.add_column("Image", style="yellow")
            table.add_column("Status", justify="center")
            table.add_column("Current", style="dim")
            table.add_column("Available", style="dim")
            table.add_column("Updates", justify="center")
            
            for i, container in enumerate(self.containers_data, 1):
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
                    str(i),
                    container.get('container_name', 'unknown'),
                    container.get('image', 'unknown'),
                    status,
                    current_version,
                    remote_version,
                    Text(update_status, style=update_style)
                )
            
            self.console.print(table)
            self.console.print()
            
            # Menu options
            self.console.print("Options:", style="bold cyan")
            self.console.print("• Enter container number to manage")
            self.console.print("• 'r' to refresh")
            self.console.print("• 'b' to go back")
            self.console.print()
            
            choice = Prompt.ask("Select option", default="b")
            
            if choice.lower() == 'b':
                return
            elif choice.lower() == 'r':
                continue
            elif choice.isdigit():
                container_num = int(choice)
                if 1 <= container_num <= len(self.containers_data):
                    selected_container = self.containers_data[container_num - 1]
                    self.handle_container_actions(selected_container['container_name'])
                else:
                    self.console.print("❌ Invalid container number", style="red")
                    input("Press Enter to continue...")
            else:
                self.console.print("❌ Invalid option", style="red")
                input("Press Enter to continue...")
    
    def handle_container_actions(self, container_name: str):
        """Handle actions for a specific container."""
        while True:
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            self.console.print(f"Managing Container: [bold cyan]{container_name}[/bold cyan]")
            self.console.print()
            
            actions_table = Table(show_header=False, box=None, padding=(0, 2))
            actions_table.add_column("Option", style="cyan", no_wrap=True)
            actions_table.add_column("Action", style="white")
            
            actions = [
                ("1", "📋 View History"),
                ("2", "💾 Backup Current Version"),
                ("3", "🔄 Show Rollback Options"),
                ("4", "🔍 Check Updates"),
                ("b", "⬅️  Back to Container List")
            ]
            
            for option, action in actions:
                actions_table.add_row(f"[bold green]{option}[/bold green]", action)
            
            self.console.print(Align.center(actions_table))
            self.console.print()
            
            choice = Prompt.ask("Select action", choices=[action[0] for action in actions], default="b")
            
            if choice == "1":
                self.show_container_history(container_name)
            elif choice == "2":
                self.backup_current_version(container_name)
            elif choice == "3":
                self.show_rollback_options(container_name)
            elif choice == "4":
                self.check_single_container_updates(container_name)
            elif choice.lower() == "b":
                return
    
    def show_container_history(self, container_name: str):
        """Show detailed history for a container."""
        try:
            with self.console.status(f"[bold green]Loading history for {container_name}..."):
                result = self.tracker.get_container_history(container_name)
            
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            if not result.get('success', False):
                self.console.print(f"❌ Error: {result.get('error', 'Unknown error')}", style="red")
                input("\nPress Enter to continue...")
                return
            
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
                history_table.add_column("#", style="cyan", width=3)
                history_table.add_column("Date", style="cyan")
                history_table.add_column("Time", style="cyan")
                history_table.add_column("From", style="red")
                history_table.add_column("To", style="green")
                
                for i, change in enumerate(changes, 1):
                    history_table.add_row(
                        str(i),
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
            with self.console.status(f"[bold green]Backing up current version of {container_name}..."):
                result = self.tracker.scan_and_update()
            
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            if result.get('success', False):
                self.console.print(f"✅ Current version of {container_name} backed up to database!", style="green")
                self.console.print(f"📦 Containers scanned: {result['containers_scanned']}")
                self.console.print(f"🔄 Changes detected: {result['changes_detected']}")
                self.console.print(f"🕐 Backup time: {result['scan_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                self.console.print(f"❌ Failed to backup: {result.get('error', 'Unknown error')}", style="red")
                
        except Exception as e:
            self.console.print(f"❌ Error backing up version: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def show_rollback_options(self, container_name: str):
        """Show rollback options for a container."""
        try:
            with self.console.status(f"[bold green]Loading rollback options for {container_name}..."):
                result = self.tracker.get_container_history(container_name)
            
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            if not result.get('success', False):
                self.console.print(f"❌ Error: {result.get('error', 'Unknown error')}", style="red")
                input("\nPress Enter to continue...")
                return
            
            changes = result.get('digest_changes', [])
            if not changes:
                self.console.print("ℹ️  No previous versions available for rollback.", style="yellow")
                input("\nPress Enter to continue...")
                return
            
            # Show rollback options
            rollback_table = Table(title=f"Rollback Options for: {container_name}", show_header=True)
            rollback_table.add_column("#", style="cyan", width=3)
            rollback_table.add_column("Date", style="cyan")
            rollback_table.add_column("Time", style="cyan")
            rollback_table.add_column("Digest", style="yellow")
            
            for i, change in enumerate(changes[:10], 1):  # Show last 10 changes
                rollback_table.add_row(
                    str(i),
                    change.change_timestamp.strftime('%Y-%m-%d'),
                    change.change_timestamp.strftime('%H:%M:%S'),
                    change.old_digest
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
                    "4. Run: ", ("python dockge_companion.py scan", "cyan"), " to record the change\n\n",
                    "💡 You can copy the full digest from the table above"
                ),
                title="Rollback Instructions",
                style="blue"
            )
            
            self.console.print(instructions)
            
            # Option to copy digest
            if Confirm.ask("\nWould you like to see the full digest for a specific version?"):
                try:
                    version_num = IntPrompt.ask("Enter version number", default=1)
                    if 1 <= version_num <= len(changes):
                        selected_change = changes[version_num - 1]
                        self.console.print(f"\n📋 Full digest for version {version_num}:")
                        self.console.print(f"[bold yellow]{selected_change.old_digest}[/bold yellow]")
                        self.console.print(f"\n💡 Use this in your docker-compose.yml as:")
                        self.console.print(f"[bold green]image: your-image@{selected_change.old_digest}[/bold green]")
                    else:
                        self.console.print("❌ Invalid version number", style="red")
                except Exception:
                    self.console.print("❌ Invalid input", style="red")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            self.console.print(f"❌ Error showing rollback options: {e}", style="red")
            input("\nPress Enter to continue...")
    
    def check_single_container_updates(self, container_name: str):
        """Check updates for a single container."""
        try:
            with self.console.status(f"[bold green]Checking updates for {container_name}..."):
                update_result = self.tracker.check_for_updates()
            
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            if update_result.get('success', False):
                for update_info in update_result.get('containers', []):
                    if update_info['container_name'] == container_name:
                        self.console.print(f"🔍 Update Check Results for: [bold cyan]{container_name}[/bold cyan]")
                        self.console.print()
                        
                        info_table = Table(show_header=False)
                        info_table.add_column("Property", style="cyan")
                        info_table.add_column("Value", style="white")
                        
                        info_table.add_row("Image", update_info['image'])
                        info_table.add_row("Current Digest", update_info['current_digest'])
                        info_table.add_row("Remote Digest", update_info['remote_digest'] or 'N/A')
                        
                        if update_info.get('update_available', False):
                            info_table.add_row("Status", Text("🆙 Update Available", style="bold yellow"))
                            self.console.print(info_table)
                            self.console.print()
                            self.console.print("🆙 An update is available for this container!", style="bold yellow")
                        elif update_info.get('error'):
                            info_table.add_row("Status", Text(f"❌ Error: {update_info['error']}", style="red"))
                            self.console.print(info_table)
                        else:
                            info_table.add_row("Status", Text("✅ Up to date", style="green"))
                            self.console.print(info_table)
                            self.console.print()
                            self.console.print("✅ This container is up to date!", style="green")
                        
                        break
                else:
                    self.console.print(f"❌ Container {container_name} not found in update results", style="red")
            else:
                self.console.print(f"❌ Failed to check updates: {update_result.get('error', 'Unknown error')}", style="red")
                
        except Exception as e:
            self.console.print(f"❌ Error checking updates: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def check_all_updates(self):
        """Check updates for all containers."""
        try:
            with self.console.status("[bold green]Checking for updates..."):
                result = self.tracker.check_for_updates()
            
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            if result.get('success', False):
                total = result['total_containers']
                available = result['updates_available']
                
                self.console.print(f"✅ Update check complete!", style="green")
                self.console.print(f"📦 Total containers: {total}")
                self.console.print(f"🆙 Updates available: {available}")
                self.console.print()
                
                if available > 0:
                    self.console.print(f"⚠️  {available} container(s) have updates available:", style="yellow")
                    self.console.print()
                    
                    # Show which containers have updates
                    update_table = Table(show_header=True)
                    update_table.add_column("Container", style="cyan")
                    update_table.add_column("Image", style="yellow")
                    update_table.add_column("Status", style="green")
                    
                    for container in result['containers']:
                        if container.get('update_available', False):
                            update_table.add_row(
                                container['container_name'],
                                container['image'],
                                "🆙 Update Available"
                            )
                    
                    self.console.print(update_table)
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
        
        while True:
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            self.console.print("Select container to view history:", style="bold cyan")
            self.console.print()
            
            # Show container selection
            container_table = Table(show_header=False, box=None, padding=(0, 2))
            container_table.add_column("Option", style="cyan", no_wrap=True)
            container_table.add_column("Container", style="white")
            container_table.add_column("Image", style="yellow")
            
            for i, container in enumerate(self.containers_data, 1):
                container_table.add_row(
                    f"[bold green]{i}[/bold green]",
                    container['container_name'],
                    container['image']
                )
            
            container_table.add_row(f"[bold green]b[/bold green]", "⬅️  Back to main menu", "")
            
            self.console.print(Align.center(container_table))
            self.console.print()
            
            choices = [str(i) for i in range(1, len(self.containers_data) + 1)] + ['b']
            choice = Prompt.ask("Select container", choices=choices, default="b")
            
            if choice.lower() == 'b':
                return
            elif choice.isdigit():
                container_num = int(choice)
                if 1 <= container_num <= len(self.containers_data):
                    selected_container = self.containers_data[container_num - 1]
                    self.show_container_history(selected_container['container_name'])
                    return
    
    def scan_containers(self):
        """Scan containers and update database."""
        try:
            with self.console.status("[bold green]Scanning containers..."):
                result = self.tracker.scan_and_update(include_stopped=True)
            
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
            if result.get('success', False):
                self.console.print("✅ Container scan completed!", style="green")
                self.console.print(f"📦 Containers scanned: {result['containers_scanned']}")

                # Show scanned container names
                if result.get('scanned_container_names'):
                    container_list = ", ".join(result['scanned_container_names'])
                    self.console.print(f"📋 Scanned: {container_list}")

                self.console.print(f"🔄 Changes detected: {result['changes_detected']}")
                if result.get('changed_container_names'):
                    changed_list = ", ".join(result['changed_container_names'])
                    self.console.print(f"🔄 Changed: {changed_list}", style="yellow")

                self.console.print(f"🆕 New containers: {result['new_containers']}")
                if result.get('new_container_names'):
                    new_list = ", ".join(result['new_container_names'])
                    self.console.print(f"🆕 New: {new_list}", style="green")

                self.console.print(f"🕐 Scan time: {result['scan_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                self.console.print(f"❌ Scan failed: {result.get('error', 'Unknown error')}", style="red")
                
        except Exception as e:
            self.console.print(f"❌ Error during scan: {e}", style="red")
        
        input("\nPress Enter to continue...")
    
    def generate_report(self):
        """Generate and display comprehensive report."""
        try:
            with self.console.status("[bold green]Generating report..."):
                result = self.tracker.generate_report()
            
            self.clear_screen()
            self.console.print(self.create_header())
            self.console.print()
            
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
                "This is a read-only view for now."
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
            
            # Show welcome message
            self.clear_screen()
            welcome = Panel(
                Text.assemble(
                    "🐳 Welcome to Dockge Companion Interactive Mode!\n\n",
                    "This interface allows you to:\n",
                    "• View container status with update information\n",
                    "• Check for available updates\n",
                    "• View container history and changes\n",
                    "• Backup current versions\n",
                    "• Get rollback instructions\n\n",
                    "Navigation:\n",
                    "• Use numbers to select options\n",
                    "• Type 'q' to quit\n",
                    "• Type 'b' to go back\n\n",
                    "Press Enter to continue..."
                ),
                title="Welcome",
                style="green"
            )
            self.console.print(Align.center(welcome))
            input()
            
            # Main menu loop
            while True:
                choice = self.show_main_menu()
                
                if choice == "1":
                    self.show_container_status()
                elif choice == "2":
                    self.check_all_updates()
                elif choice == "3":
                    self.select_container_for_history()
                elif choice == "4":
                    self.scan_containers()
                elif choice == "5":
                    self.generate_report()
                elif choice == "6":
                    self.show_settings()
                elif choice.lower() == "q":
                    break
            
            # Goodbye message
            self.clear_screen()
            self.console.print("👋 Thank you for using Dockge Companion!", style="green")
            
        except KeyboardInterrupt:
            self.clear_screen()
            self.console.print("👋 Goodbye!", style="green")
        except Exception as e:
            self.console.print(f"❌ Unexpected error: {e}", style="red")


def main():
    """Main entry point for the simple TUI."""
    tui = SimpleDockgeCompanionTUI()
    tui.run()


if __name__ == "__main__":
    main()