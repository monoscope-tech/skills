---
name: investigate
description: Investigate production incidents and debug issues using the monoscope CLI. Use when asked to look into an error, find logs, search traces, check metrics, debug a service, investigate an anomaly, or understand what happened during an incident. Requires MONOSCOPE_API_KEY and MONOSCOPE_PROJECT environment variables. For KQL query syntax, see the kql-reference skill.
allowed-tools: Bash
---

# Monoscope: Investigate

Use the `monoscope` CLI to investigate production issues — searching logs, inspecting traces, checking metrics, and correlating events across services.

## Prerequisites

```bash
export MONOSCOPE_API_KEY=<your-api-key>
export MONOSCOPE_PROJECT=<your-project-uuid>
# Optional: point at a self-hosted/dev server for testing
export MONOSCOPE_API_URL=http://localhost:8080
```

Verify with: `monoscope auth status` (in agent mode this returns
`{authenticated, method, api_url, project}` JSON — `monoscope --agent auth status | jq -r .authenticated`).

Set `MONOSCOPE_AGENT_MODE=1` (or run with `--agent`) to force JSON output and disable
interactive prompts. The runtime auto-detects this when `CI` or `CLAUDE_CODE` is
set — invocations from this skill already get JSON.

## The full pipeline (TL;DR)

Every CLI command emits a stable JSON envelope, so you can chain discovery →
search → triage without manual munging. Follow this shape unless the user's
question requires a different ordering:

```bash
# 1. Discover. Facets are precomputed top-N values per field — cheaper than
#    running `summarize count() by ...` and tells you which equality checks
#    will actually match data.
SVC=$(monoscope facets resource.service.name --top 1 \
        | jq -r '.["resource.service.name"][0].value')

# 2. Search. Use --first --id-only when you only need the first event id to
#    chain into another command.
ID=$(monoscope logs search 'severity.text=="error"' \
        --service "$SVC" --first --id-only)

# 3. Context. Pull the surrounding window with --summary for a per-trace
#    breakdown — answers "which other services were affected at the same time?".
monoscope events context --window 5m --summary \
  --at "$(monoscope events get "$ID" | jq -r .timestamp)" \
  | jq '.traces | sort_by(-.error_count) | .[0:3]'

# 4. Triage. Acknowledge open issues you've now formed a hypothesis about.
monoscope issues list --service "$SVC" --status open \
  | jq -r '.data[].id' | head -3 \
  | xargs -I {} monoscope issues ack {}
```

### Output envelopes (memorise these)

| Command | Shape |
|---|---|
| `facets [FIELD]` | `{<field_path>: [{value, count}, ...]}` |
| `events search` (and `logs`/`traces`) | `{events: [...], count, has_more, cursor}` |
| `events context --summary` | `{events, count, traces: [{trace_id, services, span_count, error_count}]}` |
| `issues list`, `monitors list`, ... | `{data: [...], pagination: {has_more, total, cursor, page, per_page}}` |
| `auth status` (agent mode) | `{authenticated, method, api_url, project}` |

Use `.events[]` for event-shaped responses and `.data[]` for everything else —
**not** `.items[]` (legacy shape; the CLI normalises it to `.data`).

## Instructions

### 1. Orient — discover active services and schema

Before searching, understand what's running and what fields are available:

```bash
# See which services reported activity recently
monoscope services list --since 24h

# Discover available telemetry fields for this project. The full schema is
# large — narrow with --search and --limit so you don't dump 600 fields into
# context.
monoscope schema --search service --limit 20
monoscope schema --search http
monoscope schema -o json | jq '.fields | keys[]' | head -50

# Discover what *values* exist for those fields (precomputed, fast).
# Far cheaper than running `summarize count() by ...` yourself — and
# answers "what services / severities / status codes does this project
# actually have?" in one round-trip.
monoscope facets                                      # all faceted fields
monoscope facets resource.service.name --top 10       # top services
monoscope facets attributes.http.response.status_code  # which 4xx/5xx?
```

Note: `.fields` is an **object** keyed by field name, not an array — use
`jq '.fields | keys[]'` (not `.fields[]`).

Use `facets` *before* writing a KQL query — it tells you which equality
checks will actually match data. If `severity.text` only ever has `"INFO"`
and `"ERROR"` in this project, don't waste a query on `=="DEBUG"`.

### 2. Search logs

Use KQL queries. The query argument is positional. KQL uses `==`/`!=` (not
Lucene `:`); `--service` and `--level` are shorthands that expand to
`resource.service.name=="X"` and `severity.text=="Y"`:

```bash
# Recent errors across all services
monoscope logs search 'severity.text=="error"' --since 1h
# or equivalently:
monoscope logs search "" --since 1h --level error

# Errors in a specific service
monoscope logs search 'body has "payment failed"' --service checkout-api --since 2h

# Time-bounded window
monoscope logs search 'body has "timeout"' --from 2026-04-15T10:00:00Z --to 2026-04-15T11:00:00Z

# Limit results and pipe to jq. The agent-mode envelope is stable:
#   {events: [{id, timestamp, service, summary, ...}], count, has_more, cursor}
monoscope logs search 'attributes.exception.type != null' --since 30m --limit 50 \
  | jq '.events[] | {id, service: .["resource.service.name"], summary}'

# Pagination: feed cursor back in
CURSOR=$(monoscope logs search "" --since 1h --limit 100 | jq -r .cursor)
monoscope logs search "" --since 1h --limit 100 --cursor "$CURSOR"
```

**Pipeline shortcut** — when you only need one event id to chain into another
command, use `--first --id-only`:

```bash
ID=$(monoscope logs search 'severity.text=="error"' --since 30m --first --id-only)
monoscope events get "$ID"
```

### 3. Inspect a specific trace

If you have a trace ID or event ID from a log entry:

```bash
# Get the full trace tree (spans in hierarchy)
monoscope traces get <trace-id> --tree

# Get a single event
monoscope events get <event-id>
```

### 4. Get temporal context

Understand what was happening around a specific moment:

```bash
# All events within 5 minutes of a timestamp
monoscope events context --at 2026-04-15T10:34:22Z --service checkout-api --window 5m

# Wider window across all services
monoscope events context --at 2026-04-15T10:34:22Z --window 15m

# **Best for triage**: --summary adds a per-trace breakdown
# {events: [...], traces: [{trace_id, services, span_count, error_count}, ...]}
monoscope events context --at 2026-04-15T10:34:22Z --window 10m --summary \
  | jq '.traces | sort_by(-.error_count) | .[0:5]'
```

### 5. Live tail (if the issue is ongoing)

```bash
# Stream all events for a service
monoscope logs tail --service payment-api

# Filter to errors only
monoscope logs tail --service payment-api --level error

# Client-side pattern filter
monoscope logs tail --grep "connection refused"
```

### 6. Check metrics

```bash
# Error rate in the last hour
monoscope metrics query "error_rate" --since 1h

# Latency by service
monoscope metrics query "avg(http.server.duration) by resource.service.name" --since 1h

# Check against an SLO threshold
monoscope metrics query "error_rate" --since 30m --assert "< 0.01"

# Sparkline chart of request rate
monoscope metrics chart "request_rate" --since 2h
```

### 7. Check for related issues

The CLI normalises every list response to `{data: [...], pagination: {...}}`,
so use `.data[]` (not `.items[]`) when piping to jq:

```bash
# Open issues for the service
monoscope issues list --status open --service checkout-api \
  | jq '.data[] | {id, title, severity, service}'

# Pagination metadata is in `.pagination`
monoscope issues list --status open | jq '.pagination'

# Get full details on a specific issue
monoscope issues get <issue-id>
```

### 8. Inspect outgoing requests when debugging

`--debug` (or `MONOSCOPE_DEBUG=1`) prints every outgoing request to stderr — useful
when a 4xx surprises you:

```bash
monoscope --debug events search 'severity.text=="error"' --since 1h --limit 1 2>&1 | head
```

Server-side validation errors (KQL parse errors, bad params) are surfaced
verbatim from the response body — including line/column markers — so a 400
will tell you what to fix.

## Output

After investigation, produce a structured summary:

1. **What was searched** — time range, services, queries used
2. **What was found** — key log lines, error patterns, affected trace IDs
3. **Metrics state** — error rate, latency, any SLO breaches
4. **Likely cause** — hypothesis based on evidence
5. **Recommended action** — fix, escalate, or monitor

## Guidelines

- Always start with a time-bounded search (`--since`) rather than open-ended queries
- Use `monoscope schema` to find the right field names before constructing KQL filters
- Use `-o json | jq` when you need to extract specific fields for further processing
- When a trace ID appears in logs, always follow up with `--tree` to see the full span hierarchy
- If the issue is ongoing, `events tail` gives a live view; use `--grep` to reduce noise
- Check metrics alongside logs — a spike in error rate often pinpoints the blast radius
- Output table format is default on TTY; use `-o json` for programmatic processing
