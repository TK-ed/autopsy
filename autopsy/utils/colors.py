"""Terminal color helpers using rich."""
from rich.console import Console
from rich.theme import Theme

THEME = Theme({
    "critical": "bold red",
    "error":    "red",
    "warning":  "yellow",
    "info":     "cyan",
    "debug":    "dim white",
    "success":  "bold green",
    "ts":       "dim cyan",
    "service":  "bold magenta",
    "anomaly":  "bold yellow",
    "header":   "bold white",
})

console = Console(theme=THEME)

LEVEL_COLORS = {
    "CRITICAL": "critical",
    "ERROR":    "error",
    "WARN":     "warning",
    "WARNING":  "warning",
    "INFO":     "info",
    "DEBUG":    "debug",
}

def level_style(level: str) -> str:
    return LEVEL_COLORS.get(level.upper(), "info")
