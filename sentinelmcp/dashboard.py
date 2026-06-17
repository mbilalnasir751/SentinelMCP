import httpx
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich import box

SENTINEL_URL = "http://127.0.0.1:8000"

def build_table(logs: list) -> Table:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Time",          style="dim", width=20)
    table.add_column("Endpoint",      width=30)
    table.add_column("Secrets found", justify="center", style="red")
    table.add_column("Blocked",       justify="center")

    for log in logs[:15]:
        blocked_style = "red" if log["blocked"] == "true" else "green"
        table.add_row(
            log["timestamp"][:19],
            log["endpoint"],
            str(log["secrets_found"]),
            f"[{blocked_style}]{log['blocked']}[/{blocked_style}]",
        )
    return table

def run_dashboard():
    console = Console()
    console.print(Panel(
        "[bold purple]SentinelMCP Live Dashboard[/bold purple]",
        subtitle="Ctrl+C to exit"
    ))

    with Live(console=console, refresh_per_second=1) as live:
        while True:
            try:
                resp = httpx.get(
                    f"{SENTINEL_URL}/_sentinel/logs", timeout=3
                )
                logs = resp.json()
                live.update(build_table(logs))
            except Exception:
                live.update(
                    "[red]Waiting for SentinelMCP to start...[/red]"
                )
            time.sleep(2)

if __name__ == "__main__":
    run_dashboard()