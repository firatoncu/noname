"""
Command Line Interface for the n0name trading bot.

This module provides a comprehensive CLI using Typer for managing
the trading bot with modern command-line features.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich import print as rprint

from .main import TradingBotApplication
from .di.container import initialize_container, shutdown_container
from .config.models import Environment
from .exceptions import TradingBotException, ConfigurationException
from .__init__ import __version__

# Create the main CLI app
app = typer.Typer(
    name="n0name",
    help="Advanced algorithmic trading bot with modern architecture",
    add_completion=False,
    rich_markup_mode="rich",
)

# Create console for rich output
console = Console()

# Global state
trading_bot: Optional[TradingBotApplication] = None


@app.command()
def version():
    """Show version information."""
    rprint(f"[bold blue]n0name Trading Bot[/bold blue] v{__version__}")
    rprint("Advanced algorithmic trading platform")


@app.command()
def start(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    environment: Environment = typer.Option(
        Environment.DEVELOPMENT,
        "--env",
        "-e",
        help="Environment to run in",
    ),
    paper_trading: bool = typer.Option(
        True,
        "--paper/--live",
        help="Enable paper trading mode",
    ),
    auto_start: bool = typer.Option(
        False,
        "--auto-start",
        help="Start trading automatically",
    ),
    symbols: Optional[List[str]] = typer.Option(
        None,
        "--symbol",
        "-s",
        help="Trading symbols (can be specified multiple times)",
    ),
    strategy: Optional[str] = typer.Option(
        None,
        "--strategy",
        help="Strategy to use",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """
    Start the trading bot.
    
    This command initializes and starts the trading bot with the specified configuration.
    """
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Initialize container
            task = progress.add_task("Initializing container...", total=None)
            container = initialize_container(
                config_path=str(config) if config else None,
                environment=environment.value
            )
            progress.update(task, description="Container initialized ✓")
            
            # Create application
            task = progress.add_task("Creating application...", total=None)
            global trading_bot
            trading_bot = TradingBotApplication(container)
            progress.update(task, description="Application created ✓")
            
            # Configure application
            if symbols:
                # Override symbols in configuration
                pass  # TODO: Implement configuration override
            
            if strategy:
                # Override strategy in configuration
                pass  # TODO: Implement strategy override
            
            # Start application
            task = progress.add_task("Starting trading bot...", total=None)
            
        # Run the application
        rprint(Panel.fit(
            "[bold green]Trading Bot Started Successfully![/bold green]\n"
            f"Environment: [cyan]{environment.value}[/cyan]\n"
            f"Paper Trading: [yellow]{'Yes' if paper_trading else 'No'}[/yellow]\n"
            f"Auto Start: [yellow]{'Yes' if auto_start else 'No'}[/yellow]",
            title="🚀 n0name Trading Bot",
            border_style="green"
        ))
        
        # Run the bot
        asyncio.run(trading_bot.run())
        
    except KeyboardInterrupt:
        rprint("\n[yellow]Shutting down gracefully...[/yellow]")
        if trading_bot:
            asyncio.run(trading_bot.shutdown())
        shutdown_container()
        
    except TradingBotException as e:
        console.print(f"[red]Trading Bot Error: {e.message}[/red]")
        if verbose:
            console.print(f"[dim]Details: {e}[/dim]")
        raise typer.Exit(1)
        
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)


@app.command()
def stop():
    """Stop the running trading bot."""
    global trading_bot
    
    if not trading_bot:
        rprint("[yellow]No trading bot is currently running[/yellow]")
        return
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Stopping trading bot...", total=None)
            asyncio.run(trading_bot.shutdown())
            shutdown_container()
            progress.update(task, description="Trading bot stopped ✓")
        
        rprint("[green]Trading bot stopped successfully[/green]")
        trading_bot = None
        
    except Exception as e:
        console.print(f"[red]Error stopping trading bot: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show trading bot status."""
    global trading_bot
    
    if not trading_bot:
        rprint("[yellow]No trading bot is currently running[/yellow]")
        return
    
    try:
        # Get status information
        status_info = asyncio.run(trading_bot.get_status())
        
        # Create status table
        table = Table(title="Trading Bot Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        for component, info in status_info.items():
            status = "✓ Running" if info.get("running", False) else "✗ Stopped"
            details = info.get("details", "")
            table.add_row(component, status, details)
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error getting status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config(
    action: str = typer.Argument(help="Action: show, validate, create"),
    config_file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Configuration file path",
    ),
):
    """
    Manage configuration.
    
    Actions:
    - show: Display current configuration
    - validate: Validate configuration file
    - create: Create a new configuration file
    """
    if action == "show":
        _show_config(config_file)
    elif action == "validate":
        _validate_config(config_file)
    elif action == "create":
        _create_config(config_file)
    else:
        rprint(f"[red]Unknown action: {action}[/red]")
        rprint("Available actions: show, validate, create")
        raise typer.Exit(1)


def _show_config(config_file: Optional[Path]):
    """Show current configuration."""
    try:
        from .config.loader import ConfigLoader
        
        loader = ConfigLoader()
        config = loader.load(str(config_file) if config_file else None)
        
        # Display configuration in a nice format
        rprint("[bold]Current Configuration:[/bold]")
        
        # Create configuration table
        table = Table(title="Configuration Settings")
        table.add_column("Section", style="cyan")
        table.add_column("Key", style="yellow")
        table.add_column("Value", style="green")
        
        def add_config_rows(obj, section=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, dict):
                        add_config_rows(value, f"{section}.{key}" if section else key)
                    else:
                        table.add_row(section, key, str(value))
        
        add_config_rows(config.dict())
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        raise typer.Exit(1)


def _validate_config(config_file: Optional[Path]):
    """Validate configuration file."""
    try:
        from .config.validator import ConfigValidator
        
        validator = ConfigValidator()
        result = validator.validate_file(str(config_file) if config_file else None)
        
        if result.is_valid:
            rprint("[green]✓ Configuration is valid[/green]")
        else:
            rprint("[red]✗ Configuration validation failed[/red]")
            for error in result.errors:
                rprint(f"  [red]• {error}[/red]")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]Error validating configuration: {e}[/red]")
        raise typer.Exit(1)


def _create_config(config_file: Optional[Path]):
    """Create a new configuration file."""
    try:
        if config_file and config_file.exists():
            if not Confirm.ask(f"Configuration file {config_file} already exists. Overwrite?"):
                rprint("[yellow]Configuration creation cancelled[/yellow]")
                return
        
        # Interactive configuration creation
        rprint("[bold]Creating new configuration...[/bold]")
        
        # Basic settings
        environment = Prompt.ask(
            "Environment",
            choices=["development", "testing", "production"],
            default="development"
        )
        
        paper_trading = Confirm.ask("Enable paper trading?", default=True)
        
        # Exchange settings
        api_key = Prompt.ask("Binance API Key", password=True)
        api_secret = Prompt.ask("Binance API Secret", password=True)
        
        # Trading settings
        symbols = Prompt.ask("Trading symbols (comma-separated)", default="BTCUSDT,ETHUSDT")
        strategy_type = Prompt.ask(
            "Strategy type",
            choices=["bollinger_rsi", "macd_fibonacci"],
            default="bollinger_rsi"
        )
        
        # Create configuration dictionary
        config_data = {
            "environment": environment,
            "trading": {
                "paper_trading": paper_trading,
                "symbols": [s.strip().upper() for s in symbols.split(",")],
                "strategy": {
                    "name": f"{strategy_type}_strategy",
                    "type": strategy_type,
                    "parameters": {}
                }
            },
            "exchange": {
                "type": "binance",
                "api_key": api_key,
                "api_secret": api_secret,
                "testnet": paper_trading
            }
        }
        
        # Write configuration file
        import yaml
        
        output_file = config_file or Path("config.yml")
        with open(output_file, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)
        
        rprint(f"[green]✓ Configuration created: {output_file}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error creating configuration: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def strategies():
    """List available trading strategies."""
    try:
        from .strategies.factory import StrategyFactory
        
        factory = StrategyFactory()
        available_strategies = factory.get_available_strategies()
        
        if not available_strategies:
            rprint("[yellow]No strategies available[/yellow]")
            return
        
        # Create strategies table
        table = Table(title="Available Trading Strategies")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="yellow")
        table.add_column("Description", style="dim")
        
        for strategy_type in available_strategies:
            try:
                info = factory.get_strategy_info(strategy_type)
                table.add_row(
                    strategy_type.value,
                    info.get("class_name", "Unknown"),
                    info.get("docstring", "No description available")[:50] + "..."
                )
            except Exception:
                table.add_row(strategy_type.value, "Unknown", "Error loading info")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error listing strategies: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def backtest(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
    start_date: str = typer.Option(
        ...,
        "--start",
        help="Start date (YYYY-MM-DD)",
    ),
    end_date: str = typer.Option(
        ...,
        "--end",
        help="End date (YYYY-MM-DD)",
    ),
    symbols: Optional[List[str]] = typer.Option(
        None,
        "--symbol",
        "-s",
        help="Trading symbols",
    ),
    strategy: Optional[str] = typer.Option(
        None,
        "--strategy",
        help="Strategy to backtest",
    ),
    initial_capital: float = typer.Option(
        10000.0,
        "--capital",
        help="Initial capital",
    ),
):
    """
    Run backtesting on historical data.
    
    This command runs a backtest of the specified strategy on historical data
    for the given date range and symbols.
    """
    try:
        rprint("[bold]Starting backtest...[/bold]")
        
        # TODO: Implement backtesting functionality
        rprint("[yellow]Backtesting functionality not yet implemented[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error running backtest: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def logs(
    lines: int = typer.Option(
        50,
        "--lines",
        "-n",
        help="Number of lines to show",
    ),
    follow: bool = typer.Option(
        False,
        "--follow",
        "-f",
        help="Follow log output",
    ),
    level: Optional[str] = typer.Option(
        None,
        "--level",
        help="Filter by log level",
    ),
):
    """Show trading bot logs."""
    try:
        # TODO: Implement log viewing functionality
        rprint("[yellow]Log viewing functionality not yet implemented[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error showing logs: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def dashboard():
    """Open the web dashboard."""
    try:
        import webbrowser
        
        # Default dashboard URL
        dashboard_url = "http://localhost:3000"
        
        rprint(f"[cyan]Opening dashboard: {dashboard_url}[/cyan]")
        webbrowser.open(dashboard_url)
        
    except Exception as e:
        console.print(f"[red]Error opening dashboard: {e}[/red]")
        raise typer.Exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main() 