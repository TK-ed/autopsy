# 🔬 autopsy

> Turn raw logs into incident postmortems — zero setup, fully local.

[![PyPI version](https://badge.fury.io/py/autopsy-cli.svg)](https://badge.fury.io/py/autopsy-cli)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**autopsy** ingests logs from multiple services, correlates them by timestamp, detects anomalies, and outputs a structured incident postmortem — all from your terminal.

No agents. No cloud. No account. Just logs in, postmortem out.

---

## 🎬 Demo

```
$ autopsy --file api.log --file worker.log --file nginx.log

╭─────────────────────────────────────────╮
│ 🔬 autopsy  — incident postmortem generator │
╰─────────────────────────────────────────╯

📂 Reading: api.log       ✓ 16 events  (api)
📂 Reading: worker.log    ✓ 11 events  (worker)
📂 Reading: nginx.log     ✓ 11 events  (nginx)

⏱  Building timeline...
🔍 Running anomaly detection...
   ⚠  9 anomalies detected

╭─────────────── 📊 Summary ───────────────╮
│ Total events   38                        │
│ Errors         15  (39.5%)               │
│ Warnings        5                        │
│ Services       api, nginx, worker        │
│ Window         14:00:00 → 14:10:25       │
╰──────────────────────────────────────────╯

╭──────────────── 🚨 Anomalies ────────────────╮
│ 14:03:00  CRITICAL  error_spike              │
│           Error rate jumped to 93.3%         │
│                                              │
│ 14:03:01  ERROR     cascade                  │
│           worker erroring 14s after api      │
│                                              │
│ 14:03:10  WARNING   silence                  │
│           No logs from nginx for 430s        │
╰──────────────────────────────────────────────╯

✅ Done.
```

---

## ✨ Why autopsy?

Every observability tool assumes you have a budget, a team, and weeks to set up agents.

**autopsy assumes you have a terminal and a log file.**

| | autopsy | Datadog | Incident.io |
|---|---|---|---|
| Setup time | 30 seconds | Days | Weeks |
| Cost | Free | $$$ | $$ |
| Agents required | ❌ | ✅ | ✅ |
| Cloud account | ❌ | ✅ | ✅ |
| Logs leave machine | ❌ Never | ✅ | ✅ |
| Works offline | ✅ | ❌ | ❌ |
| Works in air-gapped envs | ✅ | ❌ | ❌ |

---

## 🚀 Install

```bash
pip install mr-autopsy==0.1.0
```

Requires Python 3.11+

---

## ⚡ Quick Start

```bash
# Analyze a single log file
autopsy --file app.log

# Multiple services at once
autopsy --file api.log --file worker.log --file nginx.log

# Filter to your incident window
autopsy --file api.log --from "2026-08-04 14:00" --to "2026-08-04 16:00"

# Read from a Docker container
autopsy --docker my-api --since 2h

# Pipe from kubectl
kubectl logs my-pod --since=2h | autopsy --stdin --stdin-service api

# Save a Markdown postmortem
autopsy --file api.log --output markdown --save ./postmortem-2026-08-04.md
```

---

## 📋 All Options

```
Options:
  -f, --file TEXT            Log file(s) to analyze
  -s, --service TEXT         Override service name (matches --file positionally)
  -d, --docker TEXT          Docker container name(s)
      --since TEXT           Docker --since value e.g. 2h, 30m
      --stdin                Read from stdin
      --stdin-service TEXT   Service name for stdin input  [default: stdin]
      --from TEXT            Start of time window (YYYY-MM-DD HH:MM:SS)
      --to TEXT              End of time window   (YYYY-MM-DD HH:MM:SS)
  -o, --output TEXT          Output format: terminal | markdown | json
      --save TEXT            Save report to file
      --bucket INTEGER       Bucket size in seconds for rate analysis [default: 60]
      --help                 Show this message and exit.
```

---

## 📁 Supported Log Formats

Format is **auto-detected** — you never need to specify it.

### JSON (pino, winston, structlog, zerolog)
```json
{"time":"2026-08-04T14:03:05Z","level":"error","msg":"DB timeout","service":"api"}
```

### logfmt
```
ts=2026-08-04T14:03:05Z level=error msg="job failed" service=worker
```

### Plaintext (nginx, syslog, any custom format)
```
2026-08-04 14:03:05 ERROR upstream returned 502 Bad Gateway
```

---

## 🚨 Anomaly Detection

autopsy runs three detectors on every analysis:

### 1. Error Spike
Detects when the error rate suddenly jumps above baseline.

```
14:00 ░░░░░░░░  2%   normal
14:01 ░░░░░░░░  3%   normal
14:02 ░░░░░░░░  5%   normal
14:03 ████████ 93%   ← CRITICAL: error spike detected
```

### 2. Cascading Failure
Detects when Service B starts failing shortly after Service A — suggesting an upstream dependency failure.

```
14:03:01  api     → first ERROR
14:03:05  nginx   → first ERROR  (4s later  → cascade detected)
14:03:15  worker  → first ERROR  (14s later → cascade detected)
```

### 3. Service Silence
Detects when a service stops emitting logs unexpectedly.

```
14:03:10  nginx  last log before silence
              ↕  430 seconds — no logs
14:10:20  nginx  logs resume
```

---

## 📄 Output Formats

### Terminal (default)
Rich colored output with summary panel, anomaly table, and top errors.

### Markdown
```bash
autopsy --file api.log --output markdown
```
Outputs a complete postmortem document:
```markdown
# 🔬 Incident Postmortem
> Generated by autopsy v0.1.0

## 📊 Summary
| Window   | 2026-08-04 14:00:00 → 14:10:25 UTC |
| Duration | 10m 25s                             |
| Errors   | 15 (39.5%)                          |

## 🚨 Anomalies Detected
### 1. 🔴 Error spike detected
...

## 🕐 Event Timeline
...

## ✅ Action Items
- [ ] Identify root cause
- [ ] Add alerting for recurrence
```

### JSON
```bash
autopsy --file api.log --output json
```
Machine-readable output for scripting or integrations.

---

## 🏗️ Architecture

```
Ingest → Parse → Correlate → Detect → Report
```

| Layer | Job |
|-------|-----|
| **Ingest** | Read raw lines from files, Docker, or stdin |
| **Parse** | Convert each line into a structured `LogEvent` |
| **Correlate** | Merge all services into one sorted timeline |
| **Detect** | Find error spikes, silences, and cascades |
| **Report** | Render Markdown, JSON, or terminal output |

Every layer has a single input and output type — swap any layer independently without touching the rest.

---

## 🗺️ Roadmap

- [x] **v0.1** — File ingestion, auto-detect format, timeline, anomaly detection, Markdown report
- [ ] **v0.2** — Latency anomaly detection, HTML report output
- [ ] **v0.3** — Custom log format config (`.autopsy.yaml`)
- [ ] **v0.4** — Local LLM root cause summary via Ollama (offline AI, no API key)
- [ ] **v1.0** — Full docs site, 80%+ test coverage, GitHub Actions CI/CD

---

## 🤝 Contributing

Contributions are welcome! Here's how to get started:

```bash
# Clone the repo
git clone https://github.com/yourusername/autopsy
cd autopsy

# Create virtual environment
uv venv
source venv/bin/activate

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v
```

Please open an issue before submitting a large PR — let's discuss the approach first.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## 💬 FAQ

**Does autopsy send my logs anywhere?**
Never. Everything runs locally on your machine. No network calls are made.

**What Python version do I need?**
Python 3.11 or higher.

**Can I use this in CI/CD?**
Yes. Use `--output json` for machine-readable output and `--save` to persist the report as an artifact.

**My log format isn't being detected correctly. What do I do?**
Open an issue with a sample (sanitized) log line and we'll add support. Format detection is a moving target and community samples help a lot.

**Will you add real-time monitoring?**
No. autopsy is intentionally a post-incident tool. Use Prometheus, Grafana, or Datadog for real-time monitoring. Use autopsy after the incident to understand what happened.

---

## 📝 License

MIT © [Tharun](https://github.com/TK-ed)

---

<p align="center">
  Built for the developer who gets paged at 2am with nothing but a terminal.
</p>
