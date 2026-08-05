"""
autopsy — CLI entry point
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from autopsy.correlate.timeline import build_timeline, filter_window
from autopsy.correlate.window import bucket_events, error_rate_per_bucket
from autopsy.detect import run_all
from autopsy.ingest.docker_reader import read_docker
from autopsy.ingest.file_reader import read_file
from autopsy.ingest.stdin_reader import read_stdin
from autopsy.report import markdown as md_report
from autopsy.utils.colors import console, level_style

app = typer.Typer(help="🔬 autopsy — turn logs into postmortems")
err = Console(stderr=True)


def _parse_dt(value: str, name: str) -> datetime:
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise typer.BadParameter(f"Cannot parse {name}: '{value}'. Use YYYY-MM-DD HH:MM:SS")


@app.command()
def run(
    files: list[str] | None = typer.Option(None, "--file", "-f", help="Log file(s) to analyze"),
    services: list[str] | None = typer.Option(
        None, "--service", "-s", help="Override service name (matches positionally with --file)"
    ),
    docker: list[str] | None = typer.Option(
        None, "--docker", "-d", help="Docker container name(s)"
    ),
    since: str | None = typer.Option(None, "--since", help="Docker --since value e.g. 2h, 30m"),
    stdin: bool = typer.Option(False, "--stdin", help="Read from stdin"),
    stdin_service: str = typer.Option(
        "stdin", "--stdin-service", help="Service name for stdin input"
    ),
    from_dt: str | None = typer.Option(
        None, "--from", help="Start of time window (YYYY-MM-DD HH:MM:SS)"
    ),
    to_dt: str | None = typer.Option(None, "--to", help="End of time window (YYYY-MM-DD HH:MM:SS)"),
    output: str = typer.Option(
        "terminal", "--output", "-o", help="Output format: terminal | markdown | json"
    ),
    save: str | None = typer.Option(None, "--save", help="Save report to file"),
    bucket_size: int = typer.Option(
        60, "--bucket", help="Bucket size in seconds for rate analysis"
    ),
):
    """
    Analyze logs from files, Docker containers, or stdin and generate a postmortem.

    Examples:\n
      autopsy --file app.log\n
      autopsy --file app.log --file worker.log\n
      autopsy --docker my-api --since 2h\n
      kubectl logs my-pod | autopsy --stdin\n
    """
    console.print(
        Panel.fit(
            "[bold white]🔬 autopsy[/bold white] [dim]— incident postmortem generator[/dim]",
            border_style="cyan",
        )
    )

    # ── Collect events ────────────────────────────────────────────────────
    streams = []
    all_services = []

    if not files and not docker and not stdin:
        console.print("[red]Error:[/red] Provide at least one of --file, --docker, or --stdin")
        raise typer.Exit(1)

    if files:
        for i, f in enumerate(files):
            svc = services[i] if services and i < len(services) else None
            console.print(f"[dim]📂 Reading:[/dim] {f}")
            try:
                events = list(read_file(f, service=svc))
                streams.append(events)
                detected_svcs = list({e.service for e in events})
                all_services.extend(detected_svcs)
                console.print(
                    f"   [green]✓[/green] {len(events):,} events "
                    f"([service]{', '.join(detected_svcs)}[/service])"
                )
            except FileNotFoundError as e:
                console.print(f"   [red]✗[/red] {e}")

    if docker:
        for container in docker:
            console.print(f"[dim]🐳 Docker:[/dim] {container}")
            try:
                events = list(read_docker(container, since=since))
                streams.append(events)
                detected_svcs = list({e.service for e in events})
                all_services.extend(detected_svcs)
                console.print(f"   [green]✓[/green] {len(events):,} events")
            except RuntimeError as e:
                console.print(f"   [red]✗[/red] {e}")

    if stdin:
        console.print("[dim]⌨️  Reading stdin...[/dim]")
        events = list(read_stdin(service=stdin_service))
        streams.append(events)
        all_services.append(stdin_service)
        console.print(f"   [green]✓[/green] {len(events):,} events")

    if not streams:
        console.print("[red]No events collected. Exiting.[/red]")
        raise typer.Exit(1)

    # ── Build timeline ────────────────────────────────────────────────────
    console.print("\n[dim]⏱  Building timeline...[/dim]")
    timeline = build_timeline(streams)

    if from_dt or to_dt:
        f_dt = _parse_dt(from_dt, "--from") if from_dt else None
        t_dt = _parse_dt(to_dt, "--to") if to_dt else None
        timeline = filter_window(timeline, f_dt, t_dt)
        console.print(f"   [dim]Window filter applied: {len(timeline):,} events remain[/dim]")

    # ── Detect anomalies ─────────────────────────────────────────────────
    console.print("[dim]🔍 Running anomaly detection...[/dim]")
    buckets = bucket_events(timeline, bucket_seconds=bucket_size)
    rates = error_rate_per_bucket(buckets)
    unique_svcs = list({e.service for e in timeline})
    anomalies = run_all(timeline, rates, unique_svcs)
    console.print(f"   [anomaly]⚠  {len(anomalies)} anomalies detected[/anomaly]")

    # ── Terminal output ───────────────────────────────────────────────────
    if output in ("terminal", "markdown", "json"):
        _print_terminal_summary(timeline, anomalies, unique_svcs)

    # ── Generate report ───────────────────────────────────────────────────
    report_text = None
    if output == "markdown" or save:
        report_text = md_report.generate(timeline, anomalies, unique_svcs)

    if output == "markdown":
        console.print("\n" + report_text)

    if output == "json":
        import json

        data = {
            "generated_at": datetime.now(UTC).isoformat(),
            "event_count": len(timeline),
            "services": unique_svcs,
            "anomalies": [
                {**a, "timestamp": a["timestamp"].isoformat() if a.get("timestamp") else None}
                for a in anomalies
            ],
        }
        console.print(json.dumps(data, indent=2))

    if save:
        if report_text is None:
            report_text = md_report.generate(timeline, anomalies, unique_svcs)
        Path(save).write_text(report_text)
        console.print(f"\n[success]💾 Report saved to:[/success] {save}")

    console.print("\n[success]✅ Done.[/success]")


def _print_terminal_summary(timeline, anomalies, services):
    """Rich terminal summary: stats + anomalies + top errors."""

    total = len(timeline)
    errors = sum(1 for e in timeline if e.level in {"ERROR", "CRITICAL", "FATAL"})
    warns = sum(1 for e in timeline if e.level in {"WARN", "WARNING"})
    ts = [e for e in timeline if e.timestamp]
    start = ts[0].timestamp if ts else None
    end = ts[-1].timestamp if ts else None

    # Stats panel
    stats = Table.grid(padding=(0, 2))
    stats.add_column(style="dim")
    stats.add_column()
    stats.add_row("Total events", f"[bold]{total:,}[/bold]")
    stats.add_row("Errors", f"[red]{errors:,}[/red]")
    stats.add_row("Warnings", f"[yellow]{warns:,}[/yellow]")
    stats.add_row("Services", f"[magenta]{', '.join(sorted(services))}[/magenta]")
    if start and end:
        stats.add_row(
            "Window", f"[cyan]{start.strftime('%H:%M:%S')} → {end.strftime('%H:%M:%S')}[/cyan]"
        )

    console.print(Panel(stats, title="[bold]📊 Summary[/bold]", border_style="cyan"))

    # Anomalies table
    if anomalies:
        tbl = Table(box=box.ROUNDED, show_header=True, header_style="bold")
        tbl.add_column("Time", style="dim cyan", width=10)
        tbl.add_column("Severity", width=10)
        tbl.add_column("Type", width=16)
        tbl.add_column("Detail")
        for a in anomalies:
            sev = a["severity"]
            style = {"CRITICAL": "red", "ERROR": "orange3", "WARNING": "yellow"}.get(sev, "white")
            ts_s = a["timestamp"].strftime("%H:%M:%S") if a.get("timestamp") else "?"
            tbl.add_row(ts_s, f"[{style}]{sev}[/{style}]", a["type"], a["detail"])
        console.print(Panel(tbl, title="[bold]🚨 Anomalies[/bold]", border_style="yellow"))

    # Top errors
    error_events = [e for e in timeline if e.level in {"ERROR", "CRITICAL", "FATAL"}][:20]
    if error_events:
        tbl2 = Table(box=box.SIMPLE, show_header=True, header_style="bold")
        tbl2.add_column("Time", style="dim cyan", width=10)
        tbl2.add_column("Service", style="magenta", width=14)
        tbl2.add_column("Level", width=10)
        tbl2.add_column("Message")
        for e in error_events:
            ts_s = e.timestamp.strftime("%H:%M:%S") if e.timestamp else "?"
            style = level_style(e.level)
            tbl2.add_row(ts_s, e.service, f"[{style}]{e.level}[/{style}]", e.message[:100])
        console.print(Panel(tbl2, title="[bold]🔴 Top Errors[/bold]", border_style="red"))


if __name__ == "__main__":
    app()
