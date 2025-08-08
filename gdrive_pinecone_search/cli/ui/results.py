"""Results display and user interaction components."""

import webbrowser
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text

console = Console()


class SearchResultsDisplay:
    """Handles display and interaction with search results."""
    
    def __init__(self, results: List[Dict[str, Any]], query: str):
        """
        Initialize results display.
        
        Args:
            results: List of search results
            query: Original search query
        """
        self.results = results
        self.query = query
    
    def display_results(self, limit: Optional[int] = None):
        """Display search results with optional limit."""
        if not self.results:
            console.print(f"[yellow]No results found for:[/yellow] [bold cyan]{self.query}[/bold cyan]")
            return
        
        # Apply limit if specified
        display_results = self.results[:limit] if limit else self.results
        
        console.print(f"\n[bold green]Search Results for:[/bold green] [bold cyan]{self.query}[/bold cyan]")
        console.print(f"Found {len(self.results)} results (showing {len(display_results)})\n")
        
        # Display results in a table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="cyan", width=3)
        table.add_column("Score", style="green", width=8)
        table.add_column("File", style="white")
        table.add_column("Type", style="yellow", width=8)
        table.add_column("Modified", style="blue", width=12)
        
        for i, result in enumerate(display_results, 1):
            score = result.get('score', 0)
            metadata = result.get('metadata', {})
            
            # Format score as percentage
            score_pct = f"{score * 100:.1f}%"
            
            # Extract metadata
            file_name = metadata.get('file_name', 'Unknown')
            file_type = metadata.get('file_type', 'unknown')
            modified_time = metadata.get('modified_time', 'Unknown')
            
            # Truncate file name if too long
            if len(file_name) > 40:
                file_name = file_name[:37] + "..."
            
            table.add_row(str(i), score_pct, file_name, file_type, modified_time)
        
        console.print(table)
    
    def show_detailed_result(self, result_index: int):
        """Show detailed information for a specific result."""
        if result_index < 1 or result_index > len(self.results):
            console.print(f"[red]Invalid result number: {result_index}[/red]")
            return
        
        result = self.results[result_index - 1]
        metadata = result.get('metadata', {})
        score = result.get('score', 0)
        
        # Create detailed view
        content = f"""
[bold]File Name:[/bold] {metadata.get('file_name', 'Unknown')}
[bold]File Type:[/bold] {metadata.get('file_type', 'unknown')}
[bold]Score:[/bold] {score * 100:.1f}%
[bold]Modified:[/bold] {metadata.get('modified_time', 'Unknown')}
[bold]Web Link:[/bold] {metadata.get('web_view_link', 'N/A')}

[bold]Content Preview:[/bold]
{metadata.get('content', 'No content available')}
        """.strip()
        
        panel = Panel(content, title=f"Result {result_index} Details", style="blue")
        console.print(panel)
    
    def interactive_selection(self) -> Optional[Dict[str, Any]]:
        """
        Provide interactive selection of results.
        
        Returns:
            Selected result or None if cancelled
        """
        if not self.results:
            return None
        
        while True:
            console.print("\n[bold cyan]Options:[/bold cyan]")
            console.print("  [number] - View detailed result")
            console.print("  [number]o - Open file in browser")
            console.print("  [number]c - Copy file link")
            console.print("  q - Quit")
            
            choice = Prompt.ask("\nEnter your choice", default="q")
            
            if choice.lower() == 'q':
                return None
            
            # Parse choice
            if choice.endswith('o'):  # Open in browser
                try:
                    result_num = int(choice[:-1])
                    if 1 <= result_num <= len(self.results):
                        self._open_file_in_browser(result_num)
                    else:
                        console.print(f"[red]Invalid result number: {result_num}[/red]")
                except ValueError:
                    console.print("[red]Invalid choice format[/red]")
            
            elif choice.endswith('c'):  # Copy link
                try:
                    result_num = int(choice[:-1])
                    if 1 <= result_num <= len(self.results):
                        self._copy_file_link(result_num)
                    else:
                        console.print(f"[red]Invalid result number: {result_num}[/red]")
                except ValueError:
                    console.print("[red]Invalid choice format[/red]")
            
            else:  # View details
                try:
                    result_num = int(choice)
                    if 1 <= result_num <= len(self.results):
                        self.show_detailed_result(result_num)
                    else:
                        console.print(f"[red]Invalid result number: {result_num}[/red]")
                except ValueError:
                    console.print("[red]Invalid choice format[/red]")
    
    def _open_file_in_browser(self, result_index: int):
        """Open the selected file in the default browser."""
        result = self.results[result_index - 1]
        metadata = result.get('metadata', {})
        web_link = metadata.get('web_view_link')
        
        if web_link:
            try:
                webbrowser.open(web_link)
                console.print(f"[green]Opened file in browser:[/green] {metadata.get('file_name', 'Unknown')}")
            except Exception as e:
                console.print(f"[red]Failed to open browser: {e}[/red]")
        else:
            console.print("[red]No web link available for this file[/red]")
    
    def _copy_file_link(self, result_index: int):
        """Copy the file link to clipboard."""
        result = self.results[result_index - 1]
        metadata = result.get('metadata', {})
        web_link = metadata.get('web_view_link')
        
        if web_link:
            try:
                import pyperclip
                pyperclip.copy(web_link)
                console.print(f"[green]Copied link to clipboard:[/green] {metadata.get('file_name', 'Unknown')}")
            except ImportError:
                console.print("[yellow]pyperclip not installed. Link:[/yellow]")
                console.print(web_link)
            except Exception as e:
                console.print(f"[red]Failed to copy to clipboard: {e}[/red]")
        else:
            console.print("[red]No web link available for this file[/red]")


def display_file_processing_summary(processed_files: int, total_files: int, 
                                  processed_chunks: int, errors: List[str]):
    """Display a summary of file processing results."""
    table = Table(title="Processing Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    table.add_row("Files Processed", f"{processed_files}/{total_files}")
    table.add_row("Chunks Created", str(processed_chunks))
    table.add_row("Success Rate", f"{(processed_files/total_files*100):.1f}%" if total_files > 0 else "0%")
    
    console.print(table)
    
    if errors:
        console.print(f"\n[red]Errors ({len(errors)}):[/red]")
        for error in errors[:5]:  # Show first 5 errors
            console.print(f"  • {error}")
        
        if len(errors) > 5:
            console.print(f"  ... and {len(errors) - 5} more errors")


def display_indexing_progress(current_file: str, current_index: int, total_files: int, 
                            current_chunks: int, total_chunks: int):
    """Display real-time indexing progress."""
    file_progress = (current_index / total_files * 100) if total_files > 0 else 0
    chunk_progress = (current_chunks / total_chunks * 100) if total_chunks > 0 else 0
    
    console.print(f"File {current_index}/{total_files} ({file_progress:.1f}%) - {current_file}")
    console.print(f"Chunks: {current_chunks}/{total_chunks} ({chunk_progress:.1f}%)")


def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user to confirm an action."""
    return Confirm.ask(message, default=default)


def prompt_for_selection(options: List[str], prompt: str = "Select an option") -> Optional[int]:
    """Prompt user to select from a list of options."""
    console.print(f"\n[bold cyan]{prompt}:[/bold cyan]")
    
    for i, option in enumerate(options, 1):
        console.print(f"  {i}. {option}")
    
    try:
        choice = Prompt.ask("Enter your choice", choices=[str(i) for i in range(1, len(options) + 1)])
        return int(choice)
    except (ValueError, KeyboardInterrupt):
        return None


def display_help_text():
    """Display help text for the CLI."""
    help_content = """
[bold]Google Drive to Pinecone CLI[/bold]

This tool allows you to index Google Drive documents into Pinecone for semantic search.

[bold]Commands:[/bold]
  connect    - Connect to an existing Pinecone index
  index      - Index Google Drive files (owner mode only)
  refresh    - Refresh index with updated files (owner mode only)
  search     - Search indexed content
  status     - Show current configuration and status

[bold]Modes:[/bold]
  Owner Mode     - Full access to Google Drive and Pinecone
  Connected Mode - Read-only access to existing Pinecone index

[bold]Examples:[/bold]
      gdrive-pinecone-search connect my-index
    gdrive-pinecone-search index --file-types docs,sheets
    gdrive-pinecone-search search "quarterly planning"
    gdrive-pinecone-search status --verbose

    For more information, visit: https://github.com/your-repo/gdrive-pinecone-search
    """.strip()
    
    panel = Panel(help_content, title="Help", style="blue")
    console.print(panel) 