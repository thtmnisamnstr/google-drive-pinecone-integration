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
    
    def __init__(self):
        """Initialize results display."""
        pass
    
    def show_results(self, query: str, results: List[Dict[str, Any]], interactive: bool = False):
        """
        Display search results with hybrid search and reranking information.
        
        Args:
            query: Original search query
            results: List of search results
            interactive: Whether to enable interactive selection
        """
        if not results:
            console.print(f"[yellow]No results found for:[/yellow] [bold cyan]{query}[/bold cyan]")
            return
        
        console.print(f"\n[bold green]Hybrid Search Results for:[/bold green] [bold cyan]{query}[/bold cyan]")
        console.print(f"[dim]Results reranked using Pinecone's hosted reranking model[/dim]")
        console.print(f"Found {len(results)} results\n")
        
        # Display results in a grid format
        table = Table(show_header=False, show_edge=False, show_lines=False, box=None, padding=(0, 1))
        table.add_column("Score", style="green", width=10, justify="right")
        table.add_column("Content", style="white", width=80)
        
        for i, result in enumerate(results, 1):
            # Get score and metadata
            score = result.get('score', 0)
            metadata = result.get('metadata', {})
            
            # Extract metadata
            file_name = metadata.get('file_name', 'Unknown')
            web_link = metadata.get('web_view_link', 'N/A')
            
            # Get content from the text field
            content = metadata.get('text', 'No content available')
            
            # Truncate content to 150 characters
            if len(content) > 150:
                content = content[:147] + "..."
            
            # Format score
            score_str = f"{score:.3f}"
            
            # Create content cell with file name/link on first line, content on second line
            content_cell = f"[bold]{file_name}[/bold] [blue]{web_link}[/blue]\n[dim]{content}[/dim]"
            
            table.add_row(score_str, content_cell)
        
        console.print(table)
        
        if interactive:
            self._interactive_selection(results)
    
    def _interactive_selection(self, results: List[Dict[str, Any]]):
        """Provide interactive selection of results."""
        while True:
            console.print("\n[bold]Interactive Options:[/bold]")
            console.print("• Enter a result number to view details")
            console.print("• Enter 'o' + number to open file in browser")
            console.print("• Enter 'q' to quit")
            
            choice = Prompt.ask("\n[bold cyan]Enter your choice[/bold cyan]")
            
            if choice.lower() == 'q':
                break
            
            if choice.lower().startswith('o'):
                # Open file in browser
                try:
                    result_num = int(choice[1:])
                    if 1 <= result_num <= len(results):
                        result = results[result_num - 1]
                        web_link = result.get('metadata', {}).get('web_view_link')
                        if web_link:
                            console.print(f"[green]Opening file in browser...[/green]")
                            webbrowser.open(web_link)
                        else:
                            console.print("[red]No web link available for this file[/red]")
                    else:
                        console.print(f"[red]Invalid result number: {result_num}[/red]")
                except ValueError:
                    console.print("[red]Invalid format. Use 'o' + number (e.g., 'o1')[/red]")
            
            else:
                # Show detailed result
                try:
                    result_num = int(choice)
                    if 1 <= result_num <= len(results):
                        self._show_detailed_result(results[result_num - 1], result_num)
                    else:
                        console.print(f"[red]Invalid result number: {result_num}[/red]")
                except ValueError:
                    console.print("[red]Invalid choice. Please enter a number or 'q' to quit[/red]")
    
    def _show_detailed_result(self, result: Dict[str, Any], result_index: int):
        """Show detailed information for a specific result."""
        metadata = result.get('metadata', {})
        reranked_score = result.get('score', 0)
        dense_score = result.get('dense_score', 0)
        sparse_score = result.get('sparse_score', 0)
        
        # Create detailed view
        content = f"""
[bold]File Name:[/bold] {metadata.get('file_name', 'Unknown')}
[bold]File Type:[/bold] {metadata.get('file_type', 'unknown')}
[bold]Reranked Score:[/bold] {reranked_score:.3f}
[bold]Dense Score:[/bold] {dense_score:.3f}
[bold]Sparse Score:[/bold] {sparse_score:.3f}
[bold]Modified:[/bold] {metadata.get('modified_time', 'Unknown')}
[bold]Web Link:[/bold] {metadata.get('web_view_link', 'N/A')}

[bold]Content Preview:[/bold]
{metadata.get('text', 'No content available')}
        """.strip()
        
        panel = Panel(content, title=f"Result {result_index} Details", style="blue")
        console.print(panel)


def display_file_processing_summary(processed_files: int, total_files: int, processed_chunks: int, errors: List[str], skipped_files: int = 0):
    """Display a summary of file processing results."""
    console.print(f"\n[bold green]Processing Summary[/bold green]")
    console.print(f"• Files processed: {processed_files}/{total_files}")
    if skipped_files > 0:
        console.print(f"• Files skipped: {skipped_files}")
    console.print(f"• Chunks created: {processed_chunks}")
    
    if errors:
        console.print(f"\n[bold red]Errors and Skips ({len(errors)}):[/bold red]")
        for error in errors[:10]:  # Show first 10 errors/skips
            console.print(f"  • {error}")
        if len(errors) > 10:
            console.print(f"  • ... and {len(errors) - 10} more errors/skips")


def display_indexing_progress(current_file: str, current_index: int, total_files: int, 
                            current_chunks: int):
    """Display real-time indexing progress."""
    file_progress = (current_index / total_files * 100) if total_files > 0 else 0
    
    console.print(f"File {current_index}/{total_files} ({file_progress:.1f}%) - {current_file}")
    console.print(f"Chunks processed: {current_chunks}")


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
    """Display help information for the CLI."""
    console.print("\n[bold cyan]Google Drive + Pinecone Hybrid Search CLI[/bold cyan]")
    console.print("=" * 60)
    
    console.print("\n[bold]Commands:[/bold]")
    console.print("  [green]owner setup[/green]      Configure owner mode with hybrid search")
    console.print("  [green]owner index[/green]      Index Google Drive documents")
    console.print("  [green]owner refresh[/green]    Refresh/update existing index")
    console.print("  [green]connect[/green]          Connect to existing Pinecone indexes")
    console.print("  [green]search[/green]           Search indexed documents with reranking")
    console.print("  [green]status[/green]           Show current configuration and status")
    
    console.print("\n[bold]Search Options:[/bold]")
    console.print("  [yellow]--limit[/yellow]        Number of results (default: 10, max: 100)")
    console.print("  [yellow]--file-types[/yellow]   Filter by type (docs,sheets,slides)")
    console.print("  [yellow]--interactive[/yellow]  Enable interactive result selection")
    
    console.print("\n[bold]Environment Variables:[/bold]")
    console.print("  [blue]PINECONE_API_KEY[/blue]           Your Pinecone API key")
    console.print("  [blue]PINECONE_DENSE_INDEX_NAME[/blue]   Dense index name")
    console.print("  [blue]PINECONE_SPARSE_INDEX_NAME[/blue]  Sparse index name")
    console.print("  [blue]GDRIVE_CREDENTIALS_JSON[/blue]     Google Drive credentials path")
    console.print("  [blue]RERANKING_MODEL[/blue]             Reranking model")
    console.print("  [blue]CHUNK_SIZE[/blue]                  Text chunk size in tokens")
    console.print("  [blue]CHUNK_OVERLAP[/blue]               Chunk overlap in tokens")
    
    console.print("\n[bold]Operation Modes:[/bold]")
    console.print("  • [green]Owner Mode[/green]: Full access (index + search) - requires Google Drive credentials")
    console.print("  • [green]Connected Mode[/green]: Read-only search - requires only Pinecone API key")
    
    console.print("\n[bold]Hybrid Search Features:[/bold]")
    console.print("  • [green]Dense embeddings[/green] for semantic understanding")
    console.print("  • [green]Sparse embeddings[/green] for exact keyword matching")
    console.print("  • [green]Intelligent reranking[/green] using hosted model")
    
    console.print("\n[bold]Examples:[/bold]")
    console.print("  [dim]gdrive-pinecone-search owner setup --credentials creds.json --api-key sk-...[/dim]")
    console.print("  [dim]gdrive-pinecone-search owner index --file-types docs,sheets[/dim]")
    console.print("  [dim]gdrive-pinecone-search search \"quarterly planning\"[/dim]")
    console.print("  [dim]gdrive-pinecone-search search \"budget\" --file-types docs,sheets[/dim]")
    console.print("  [dim]gdrive-pinecone-search search \"meeting notes\" --interactive[/dim]")
    
    console.print("\n[bold]For more information:[/bold]")
    console.print("  [blue]https://docs.pinecone.io/guides/search/hybrid-search[/blue]") 