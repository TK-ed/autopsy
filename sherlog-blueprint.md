# 🔬 sherlog — CLI Postmortem Builder
> *Feed it logs. Get a timeline. Ship the postmortem.*

---

## 🧠 What It Does (One-liner)
`sherlog` ingests raw logs from multiple services, correlates them by timestamp, detects anomalies, and outputs a structured incident postmortem — all from your terminal.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    sherlog CLI                       │
│                                                     │
│  ┌──────────┐   ┌──────────┐   ┌─────────────────┐ │
│  │  Ingest  │ → │  Parse   │ → │    Correlate    │ │
│  │  Layer   │   │  Layer   │   │    Engine       │ │
│  └──────────┘   └──────────┘   └────────┬────────┘ │
│                                          │          │
│                               ┌──────────▼────────┐ │
│                               │  Anomaly Detector  │ │
│                               └──────────┬────────┘ │
│                                          │          │
│                               ┌──────────▼────────┐ │
│                               │  Report Generator  │ │
│                               │  (Markdown/JSON)   │ │
│                               └───────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Layers Explained

| Layer | Responsibility |
|-------|---------------|
| **Ingest** | Read from files, stdin, Docker logs, journald |
| **Parse** | Normalize timestamps, log levels, service names |
| **Correlate** | Merge multi-service logs into a unified timeline |
| **Anomaly Detector** | Find error spikes, cascading failures, silences |
| **Report Generator** | Output structured postmortem in Markdown/JSON/HTML |

---

## 📁 Folder Structure

```
sherlog/
├── sherlog/
│   ├── __init__.py
│   ├── cli.py                  # Entry point (Click/Typer)
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── file_reader.py      # Read from log files
│   │   ├── stdin_reader.py     # Pipe logs via stdin
│   │   ├── docker_reader.py    # docker logs integration
│   │   └── journald_reader.py  # systemd journald support
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract parser class
│   │   ├── auto_detect.py      # Auto-detect log format
│   │   ├── json_parser.py      # JSON structured logs
│   │   ├── logfmt_parser.py    # key=value logfmt
│   │   ├── nginx_parser.py     # Nginx access/error logs
│   │   ├── syslog_parser.py    # Syslog format
│   │   └── plaintext_parser.py # Generic regex fallback
│   ├── correlate/
│   │   ├── __init__.py
│   │   ├── timeline.py         # Merge & sort events
│   │   └── window.py           # Time-window grouping
│   ├── detect/
│   │   ├── __init__.py
│   │   ├── error_spike.py      # Spike in error rate
│   │   ├── silence.py          # Service goes quiet
│   │   ├── cascade.py          # Cascading failure pattern
│   │   └── latency.py          # Latency anomalies
│   ├── report/
│   │   ├── __init__.py
│   │   ├── markdown.py         # Markdown postmortem
│   │   ├── json_report.py      # Machine-readable output
│   │   └── html_report.py      # Browser-viewable report
│   └── utils/
│       ├── __init__.py
│       ├── timestamp.py        # Timestamp normalization
│       └── colors.py           # Terminal colors (rich)
├── tests/
│   ├── fixtures/               # Sample log files
│   ├── test_parsers.py
│   ├── test_correlate.py
│   └── test_detect.py
├── docs/
│   ├── getting-started.md
│   └── formats-supported.md
├── pyproject.toml
├── README.md
└── DECISIONS.md                # Architecture decisions log
```

---

## 🛠️ Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| **Language** | Python 3.11+ | Rich ecosystem for log parsing |
| **CLI Framework** | [Typer](https://typer.tiangolo.com/) | Beautiful CLI with type hints |
| **Terminal UI** | [Rich](https://github.com/Textualize/rich) | Tables, progress, colors |
| **Timestamp parsing** | `python-dateutil` + `arrow` | Handles any format |
| **Log parsing** | Custom + regex | Flexible, no heavy deps |
| **Testing** | `pytest` + `pytest-cov` | Standard |
| **Packaging** | `pyproject.toml` (hatchling) | Modern Python packaging |
| **CI/CD** | GitHub Actions | Auto test + publish to PyPI |

---

## 🚀 Usage (What the CLI Looks Like)

```bash
# Single log file
sherlog --file app.log

# Multiple services
sherlog --file app.log --file nginx.log --file redis.log

# From Docker containers
sherlog --docker my-api --docker my-worker --since 2h

# Pipe from stdin
kubectl logs my-pod --since=2h | sherlog --stdin --service api

# Set time window (incident window)
sherlog --file app.log --from "2026-08-04 14:00" --to "2026-08-04 16:00"

# Output formats
sherlog --file app.log --output markdown   # default
sherlog --file app.log --output json
sherlog --file app.log --output html

# Save report
sherlog --file app.log --save ./postmortem-2026-08-04.md
```

---

## 📄 Sample Output

```markdown
# 🔬 Incident Postmortem
**Generated by sherlog v0.1.0**
**Window:** 2026-08-04 14:00:00 → 2026-08-04 15:47:23
**Services analyzed:** api, worker, nginx

---

## 📊 Summary

| Metric | Value |
|--------|-------|
| Total events | 14,823 |
| Errors | 1,247 (8.4%) |
| Warnings | 892 |
| Services affected | 3 |
| Incident duration | 1h 47m |

---

## 🕐 Timeline

| Time | Service | Severity | Event |
|------|---------|----------|-------|
| 14:03:12 | nginx | WARN | Latency spike: p99 > 2000ms |
| 14:07:44 | api | ERROR | DB connection pool exhausted |
| 14:07:51 | worker | ERROR | Job queue not responding |
| 14:08:02 | api | CRITICAL | 500 error rate: 94% |
| 14:09:15 | worker | WARN | Retrying failed jobs (attempt 1/3) |
| 14:23:00 | api | INFO | DB connections recovering |
| 15:47:23 | all | INFO | Error rate normalized |

---

## 🚨 Anomalies Detected

### 1. Error Spike — api (14:07:44)
- Error rate jumped from **0.3% → 94%** in 23 seconds
- Likely trigger: DB connection pool exhausted

### 2. Cascading Failure — worker (14:07:51)
- Worker failures began **7 seconds** after api errors
- Pattern: upstream dependency failure

### 3. Service Silence — nginx (14:08:10 → 14:10:32)
- No logs emitted for **2m 22s**
- Possible cause: process restart or connection drop

---

## 🔍 Root Cause (Suggested)
Database connection pool exhaustion triggered cascading failures
across api and worker services. nginx experienced a brief outage
likely due to upstream unavailability.

---

## ✅ Action Items
- [ ] Investigate DB pool configuration
- [ ] Add circuit breakers between api → worker
- [ ] Set up alerting for connection pool metrics
- [ ] Review nginx upstream timeout settings
```

---

## 🗺️ Roadmap

### v0.1.0 — MVP (Week 1–2) 🎯
- [ ] File ingestion (single + multi file)
- [ ] Auto-detect log format (JSON, logfmt, plain)
- [ ] Timestamp normalization
- [ ] Basic timeline builder
- [ ] Markdown report output
- [ ] `pip install sherlog-cli` works

### v0.2.0 — Detection (Week 3–4)
- [ ] Error spike detection
- [ ] Service silence detection
- [ ] Cascading failure pattern
- [ ] Rich terminal output (colored timeline)

### v0.3.0 — Integrations (Week 5–6)
- [ ] Docker logs (`--docker <container>`)
- [ ] stdin piping (kubectl, journalctl)
- [ ] JSON + HTML output formats
- [ ] `--save` to file

### v0.4.0 — Intelligence (Week 7–8)
- [ ] Local LLM root cause summary (Ollama)
- [ ] Latency anomaly detection
- [ ] Custom log format config (`.sherlog.yaml`)

### v1.0.0 — Production Ready
- [ ] GitHub Actions for CI/CD + PyPI publish
- [ ] Full test coverage (>80%)
- [ ] Docs site (MkDocs)
- [ ] VS Code extension (optional)

---

## 🚀 Launch Plan

### Week 1–2: Build MVP
- Build the core: ingest → parse → timeline → markdown output
- Test with real log samples
- Write a killer README with a demo GIF

### Week 3: Polish & Package
- `pip install sherlog-cli` working
- GitHub Actions CI passing
- 100% working on macOS + Linux

### Week 4: Launch
- **Hacker News**: `Show HN: sherlog – CLI that turns raw logs into postmortems`
- **Reddit**: r/devops, r/Python, r/sysadmin
- **Dev.to**: Blog post — "I built a CLI that writes postmortems from logs"
- **X/Twitter**: Demo GIF thread

### Week 5+: Build in Public
- Respond to every GitHub issue within 24h
- Ship a new feature every week
- Tweet progress with #buildinpublic

---

## 📣 README Structure (For GitHub Stars)

```
1. One-line description + badges (PyPI, stars, license)
2. Demo GIF (most important — record it with asciinema)
3. Install: pip install sherlog-cli
4. Quick start: 3 commands
5. Features list
6. Supported log formats
7. Full CLI reference
8. Roadmap
9. Contributing guide
```

---

## 🧠 DECISIONS.md (Seed It From Day 1)

Document every choice:
- "Why Typer over Click" 
- "Why python-dateutil over manual regex for timestamps"
- "Why we auto-detect format instead of requiring --format flag"

This single file will impress every senior engineer who looks at your repo.

---
