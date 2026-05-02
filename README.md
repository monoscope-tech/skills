# monoscope-skills

Claude Code skills for the [Monoscope](https://monoscope.tech) observability platform. Gives Claude the knowledge to use the `monoscope` CLI to investigate production incidents, triage issues and alerts, write KQL queries, and manage your observability resources.

## Installation

### Claude Code

```bash
claude plugin marketplace add monoscope-tech/skills
claude plugin install monoscope-skills@monoscope-skills
```

Restart Claude Code after installation. Skills activate automatically when relevant.

**Update:**

```bash
claude plugin marketplace update
claude plugin update monoscope-skills@monoscope-skills
```

Or run `/plugin` to open the plugin manager.

### Skills Package (skills.sh)

For agents supporting the [skills.sh](https://skills.sh) ecosystem:

```bash
npx skills add monoscope-tech/skills
```

Works with Claude Code, Cursor, Cline, GitHub Copilot, and other compatible agents.

## Prerequisites

Install the `monoscope` CLI and authenticate:

```bash
curl -fsSL https://monoscope.tech/install.sh | bash
monoscope auth login
```

Set your default project (or pass `MONOSCOPE_PROJECT` per-session):

```bash
monoscope config set project <your-project-uuid>
```

## Available Skills

| Skill | Description |
|---|---|
| [`kql-reference`](#kql-reference) | Full KQL query language reference |
| [`investigate`](#investigate) | Investigate production incidents |
| [`triage`](#triage) | On-call sweep: issues, alerts, log patterns |

### `kql-reference`

Complete reference for Monoscope's KQL dialect — operators (`==`, `!=`, `has`, `contains`, `startswith`, `matches`, `in`, `has_any` …), aggregations (`count`, `dcount`, `percentile` …), time binning (`bin_auto`, `bin`), scalar functions, the full telemetry schema, and 15+ example queries.

Consult this whenever writing, reading, or debugging a KQL query.

### `investigate`

Investigate production incidents using the `monoscope` CLI. Walks Claude through discovering active services, searching logs and traces, inspecting trace trees, watching live events, and checking metrics against SLO thresholds.

**Example prompts:**
- "Investigate the 500 errors in the payment service over the last hour"
- "Find logs related to the timeout we saw at 10:34 UTC"
- "Check the error rate for checkout-api and show me what's failing"
- "What happened to the auth service between 14:00 and 14:30?"

### `triage`

On-call sweep: review open issues, acknowledge noisy log patterns, mute or resolve flapping monitors, and bulk-action alert queues.

**Example prompts:**
- "Triage all open issues for the payment service"
- "Do an on-call sweep and clear the alert queue"
- "Mute the noisy database connection monitor for 30 minutes"
- "Bulk acknowledge the runtime exception issues from last night"

## Environment variables

| Variable | Description |
|---|---|
| `MONOSCOPE_API_KEY` | API key — takes precedence over stored token |
| `MONOSCOPE_PROJECT` | Default project UUID |
| `MONOSCOPE_API_URL` | API base URL (default: `https://api.monoscope.tech`). Point at `http://localhost:8080` to drive a self-hosted dev server from these skills. |
| `MONOSCOPE_AGENT_MODE` | Set to `1` to force JSON output and disable interactive prompts. Auto-detected when `CI` or `CLAUDE_CODE` is set, so skills launched from Claude Code already get JSON. |
| `MONOSCOPE_DEBUG` | Set to `1` to print every outgoing request URL+params to stderr — invaluable when an agent gets a 4xx and needs to inspect what it actually sent. |

## Output shapes (stable across versions)

The skills assume these JSON envelopes — they're pinned by integration tests in
[`test/integration/CLI/CLIE2ESpec.hs`](https://github.com/monoscope-tech/monoscope/blob/master/test/integration/CLI/CLIE2ESpec.hs)
so a regression breaks CI rather than the skill in production.

| Command | Shape |
|---|---|
| `events search`, `logs search`, `traces search`, `events get`, `events context` | `{events: [{id, timestamp, service, summary, trace_id, kind, ...}], count, has_more, cursor}` |
| `services list` | `{services: [{name, events, last_seen}], count}` |
| `<resource> list` (`issues`, `monitors`, `dashboards`, `api-keys`, `teams`, `members`, `endpoints`, `log-patterns`) | `{data: [...], pagination: {has_more, total, cursor, page, per_page}}` — use `.data[]` in jq |
| `--agent auth status` | `{authenticated, method, api_url, project}` |
| `events context --summary` | base envelope plus `traces: [{trace_id, services, span_count, error_count}, ...]` |

## Links

- [Monoscope](https://monoscope.tech) — observability platform
- [CLI reference](https://github.com/monoscope-tech/monoscope/blob/master/docs/cli.md) — full `monoscope` command reference
- [monoscope-tech/monoscope](https://github.com/monoscope-tech/monoscope) — main repo

## License

Apache-2.0
