"""Progress UI components for the CLI."""

import time
from typing import Optional, Callable
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()


class ProgressManager:
    """Manages progress display for long-running operations."""
    
    def __init__(self):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        )
    
    def __enter__(self):
        self.progress.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()
    
    def add_task(self, description: str, total: Optional[int] = None) -> int:
        """Add a new progress task."""
        return self.progress.add_task(description, total=total)
    
    def update(self, task_id: int, advance: int = 1, description: Optional[str] = None):
        """Update a progress task."""
        self.progress.update(task_id, advance=advance, description=description)


def show_status_panel(title: str, content: str, style: str = "blue"):
    """Display a status panel."""
    panel = Panel(content, title=title, style=style)
    console.print(panel)


def show_error_panel(title: str, error: str):
    """Display an error panel."""
    panel = Panel(error, title=title, style="red")
    console.print(panel)


def show_success_panel(title: str, message: str):
    """Display a success panel."""
    panel = Panel(message, title=title, style="green")
    console.print(panel)


def show_info_table(title: str, data: dict):
    """Display information in a table format."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in data.items():
        table.add_row(key, str(value))
    
    console.print(table)


def show_connection_status(status: dict):
    """Display connection status information."""
    table = Table(title="Connection Status", show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan")
    table.add_column("Configured", style="white")
    table.add_column("Connected", style="white")
    table.add_column("Details", style="white")
    
    # Pinecone status
    pinecone_status = status.get('pinecone', {})
    indexes = pinecone_status.get('indexes', {})
    if indexes:
        pinecone_details = f"Dense: {indexes.get('dense', 'N/A')}, Sparse: {indexes.get('sparse', 'N/A')}"
    else:
        pinecone_details = pinecone_status.get('error', 'N/A')
    table.add_row(
        "Pinecone",
        "✓" if pinecone_status.get('connected') else "✗",
        "✓" if pinecone_status.get('connected') else "✗",
        pinecone_details
    )
    
    # Google Drive status
    gdrive_status = status.get('google_drive', {})
    user_info = gdrive_status.get('user_info', {})
    if user_info:
        gdrive_details = f"User: {user_info.get('emailAddress', 'N/A')}"
    else:
        gdrive_details = gdrive_status.get('error', 'N/A')
    table.add_row(
        "Google Drive",
        "✓" if gdrive_status.get('connected') else "✗",
        "✓" if gdrive_status.get('connected') else "✗",
        gdrive_details
    )
    
    console.print(table)


def show_index_stats(stats: dict):
    """Display index statistics."""
    table = Table(title="Index Statistics", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    
    # Extract relevant stats
    dense_vectors = stats.get('dense_vectors', 0)
    sparse_vectors = stats.get('sparse_vectors', 0)
    dense_namespaces = stats.get('dense_namespaces', {})
    sparse_namespaces = stats.get('sparse_namespaces', {})
    
    table.add_row("Dense Vectors", str(dense_vectors))
    table.add_row("Dense Namespaces", str(len(dense_namespaces)))
    table.add_row("Sparse Vectors", str(sparse_vectors))
    table.add_row("Sparse Namespaces", str(len(sparse_namespaces)))
    
    console.print(table)


def show_search_results(results: list, query: str):
    """Display search results."""
    if not results:
        console.print(f"No results found for: [bold cyan]{query}[/bold cyan]")
        return
    
    console.print(f"\n[bold green]Search Results for:[/bold green] [bold cyan]{query}[/bold cyan]")
    console.print(f"Found {len(results)} results\n")
    
    for i, result in enumerate(results, 1):
        score = result.get('score', 0)
        metadata = result.get('metadata', {})
        
        # Format score as percentage
        score_pct = f"{score * 100:.1f}%"
        
        # Extract metadata
        file_name = metadata.get('file_name', 'Unknown')
        file_type = metadata.get('file_type', 'unknown')
        modified_time = metadata.get('modified_time', 'Unknown')
        content = metadata.get('content', '')
        
        # Truncate content for display
        if len(content) > 200:
            content = content[:200] + "..."
        
        # Create result panel
        panel_content = f"""
[bold]{file_name}[/bold] ({file_type}) - Modified {modified_time}
Score: [bold green]{score_pct}[/bold green]

{content}
        """.strip()
        
        panel = Panel(panel_content, title=f"Result {i}", style="blue")
        console.print(panel)
        console.print()  # Add spacing between results


def show_file_processing_progress(current: int, total: int, current_file: str):
    """Show file processing progress."""
    percentage = (current / total * 100) if total > 0 else 0
    console.print(f"Processing: {current}/{total} ({percentage:.1f}%) - {current_file}")


def show_rate_limit_warning(service: str, retry_after: int):
    """Show rate limit warning."""
    warning = f"Rate limit exceeded for {service}. Waiting {retry_after} seconds..."
    panel = Panel(warning, title="Rate Limit Warning", style="yellow")
    console.print(panel)


def show_configuration_summary(config: dict):
    """Show configuration summary."""
    table = Table(title="Configuration Summary", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    # Connection info
    connection = config.get('connection', {})
    table.add_row("Mode", config.get('mode', 'unknown').title())
    table.add_row("Dense Index", connection.get('dense_index_name', 'N/A'))
    table.add_row("Sparse Index", connection.get('sparse_index_name', 'N/A'))

    
    # Settings
    settings = config.get('settings', {})
    table.add_row("Reranking Model", settings.get('reranking_model', 'N/A'))
    table.add_row("Chunk Size", str(settings.get('chunk_size', 'N/A')))
    table.add_row("Chunk Overlap", str(settings.get('chunk_overlap', 'N/A')))
    
    # Owner info
    if config.get('mode') == 'owner':
        owner_config = config.get('owner_config', {})
        table.add_row("Last Refresh", str(owner_config.get('last_refresh_time', 'Never')))
        table.add_row("Files Indexed", str(owner_config.get('total_files_indexed', 0)))
    
    console.print(table) 