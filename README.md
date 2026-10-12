# monoscope-skills

Agent skills for the [Monoscope](https://monoscope.tech) observability platform. They teach a coding agent to use the `monoscope` CLI to investigate production incidents, triage issues and alerts, write KQL queries, manage monitors and dashboards, and instrument apps with OpenTelemetry.

The skills follow the open [Agent Skills](https://agentskills.io) format (`skills/<name>/SKILL.md`), so the same files work in Claude Code, Codex, Gemini CLI, Pi, Cursor, OpenCode, and any other agent that reads `SKILL.md`.

## Installation

### Claude Code

```bash
claude plugin marketplace add monoscope-tech/skills
claude plugin install monoscope-skills@monoscope-skills
```

Restart Claude Code. Update with `claude plugin marketplace update && claude plugin update monoscope-skills@monoscope-skills`, or use `/plugin`.

### Codex

```bash
codex plugin marketplace add monoscope-tech/skills
codex plugin add monoscope-skills@monoscope-skills
```

Requires Codex CLI v0.122+ (older releases: `codex marketplace add`). You can also run `/plugins` in Codex to browse and install. Invoke a skill explicitly with `$investigate`, `$triage`, etc.

### Gemini CLI

```bash
gemini extensions install https://github.com/monoscope-tech/skills
```

The extension bundles all five skills (check with `gemini skills list`). Update with `gemini extensions update monoscope-skills`.

### Pi

```bash
pi install git:github.com/monoscope-tech/skills
```

Pi auto-discovers the `skills/` directory. Use `/skill:investigate` etc. to invoke one explicitly.

### Cursor, OpenCode, Cline, Copilot, and others (skills.sh)

```bash
npx skills add monoscope-tech/skills
```

### Manual (any agent)

Copy or symlink the skill folders into a skills directory your agent reads. `~/.agents/skills/` (user) and `.agents/skills/` (repo) are read by Codex, Gemini CLI, and Pi:

```bash
git clone https://github.com/monoscope-tech/skills ~/.monoscope-skills
mkdir -p ~/.agents/skills
ln -s ~/.monoscope-skills/skills/* ~/.agents/skills/
```

For Claude Code use `~/.claude/skills/` instead. Run `git -C ~/.monoscope-skills pull` to update.

## Prerequisites

Install the `monoscope` CLI and authenticate:

```bash
curl monoscope.tech/install.sh | sh
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
| [`manage`](#manage) | Monitors & dashboards as code (create alerts, GitOps apply) |
| [`instrument`](#instrument) | Instrument an app with OpenTelemetry auto-instrumentation |

### `kql-reference`

Complete reference for Monoscope's KQL dialect — operators (`==`, `!=`, `has`, `contains`, `startswith`, `matches`, `in`, `has_any` …), aggregations (`count`, `dcount`, `percentile` …), time binning (`bin_auto`, `bin`), scalar functions, the full telemetry schema, and 15+ example queries.

Consult this whenever writing, reading, or debugging a KQL query.

### `investigate`

Investigate production incidents using the `monoscope` CLI. Walks the agent through discovering active services, searching logs and traces, inspecting trace trees, watching live events, and checking metrics against SLO thresholds.

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

### `manage`

Create and manage alert monitors and dashboards **as code**: YAML files
upserted with `monoscope monitors apply` / `dashboards apply` (idempotent —
keyed by title / file_path), plus the `yaml` dump → edit → apply round-trip.

**Example prompts:**
- "Alert me when checkout errors exceed 10 in 15 minutes"
- "Create a latency dashboard for the payment service"
- "Put our monitors in the repo and apply them from CI"
- "Add a p99 widget to the on-call dashboard"

### `instrument`

Add OpenTelemetry instrumentation to an application so traces, logs, and metrics flow into Monoscope. Detects the language and framework, installs the right Monoscope SDK or OTel packages, writes the SDK init code and middleware wiring, sets the OTLP exporter env vars, and verifies data is flowing with `monoscope services list`.

Supports native Monoscope SDKs (with request/response capture, error reporting, and outgoing-request monitoring) for: **Express**, **Fastify**, **NestJS**, **FastAPI**, **Django**, **Gin**, **Echo**, **Chi**, **Fiber**, **Spring Boot**, **Laravel**. Falls back to standard OTel auto-instrumentation for Ruby, Rust, .NET, Flask, Pyramid, and any other OTel-supported language.

**Example prompts:**
- "Instrument this Express app with Monoscope"
- "Add OpenTelemetry tracing to my FastAPI service"
- "Wire up observability for my Go Gin API"
- "Set up the OTLP exporter for my Spring Boot app"
- "Get my Django app sending data to Monoscope"

## Environment variables

| Variable | Description |
|---|---|
| `MONOSCOPE_API_KEY` | API key — takes precedence over stored token |
| `MONOSCOPE_PROJECT` | Default project UUID |
| `MONOSCOPE_API_URL` | API base URL (default: `https://api.monoscope.tech`). Point at `http://localhost:8080` to drive a self-hosted dev server from these skills. |
| `MONOSCOPE_DEBUG` | Set to `1` to print every outgoing request URL+params to stderr — invaluable when an agent gets a 4xx and needs to inspect what it actually sent. Same as the global `--debug` flag. |
| `MONOSCOPE_FORCE_COLOR` | Set to `1` to keep TTY-style (table) output even when stdout is piped. |

## Output format

Output format is auto-detected from stdout: TTY → table, pipe/redirect → JSON — so agents piping output get JSON automatically. Force a format with the global `--json`, `--yaml`, or `--table` flags (precedence `--json` > `--yaml` > `--table`). `-p/--project PID` overrides the project per-invocation.

## Output shapes (stable across versions)

The skills assume these JSON envelopes — they're pinned by integration tests in
[`test/integration/CLI/CLIE2ESpec.hs`](https://github.com/monoscope-tech/monoscope/blob/master/test/integration/CLI/CLIE2ESpec.hs)
so a regression breaks CI rather than the skill in production.

| Command | Shape |
|---|---|
| `events search`, `logs search`, `traces search`, `events get`, `events context` | `{events: [{id, timestamp, service, summary, trace_id, kind, ...}], count, has_more, cursor}` |
| `services list` | `{services: [{name, events}], count}` (precomputed via the server's facet store — fast even on huge projects) |
| `<resource> list` (`issues`, `monitors`, `dashboards`, `api-keys`, `teams`, `members`, `endpoints`, `log-patterns`) | `{data: [...], pagination: {has_more, total, cursor, page, per_page}}` — use `.data[]` in jq |
| `auth status` (piped or `--json`) | `{authenticated, method, api_url, project}` |
| `facets [FIELD]` | `{<field_path>: [{value, count}, ...]}` |
| `events context --summary` | base envelope plus `traces: [{trace_id, services, span_count, error_count}, ...]` |
| `dashboards render <id>` | `{title, tab, tabs, since, from, to, widgets: [{title, w_type, unit, layout, headers, rows, text_rows, stats, value, error, children}]}` — every widget's query already run server-side |
| `chart <kql>` | same envelope as `metrics query`: `{headers, dataset, data_text, data_float, stats, from, to, error}` |

Commands that draw (`chart`, `dashboards render`, `traces get --tree`,
`logs search`/`tail`) print a terminal rendering only when stdout is a TTY;
piped or under `--json` they emit the envelope above, so an agent can use the
same command a human would.

## Releasing

Codex and Gemini cache installs by version, so after changing a skill bump `version` in `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, and `gemini-extension.json` together. Otherwise `update` will not deliver the change.

## Links

- [Monoscope](https://monoscope.tech) — observability platform
- [CLI reference](https://github.com/monoscope-tech/monoscope/blob/master/docs/cli.md) — full `monoscope` command reference
- [monoscope-tech/monoscope](https://github.com/monoscope-tech/monoscope) — main repo

## License

Apache-2.0
