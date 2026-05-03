# Monoscope Skills

This plugin provides agent skills for working with the Monoscope observability platform via the `monoscope` CLI.

## Available Skills

### `kql-reference`

Full reference for Monoscope's KQL dialect — operators, aggregations, time binning, string functions, scalar functions, schema fields, and example queries. Consult this before writing any KQL query. This skill is the source of truth for query syntax.

**Triggers:** any time you need to write, read, or explain a KQL query in monoscope

---

### `investigate`

Use when debugging a production incident, searching logs, inspecting traces, or checking metrics. Teaches the agent to orient with `services list`, search with `logs search` / `traces get --tree`, monitor live with `events tail`, and check SLOs with `metrics query --assert`.

**Triggers:** "investigate the error in...", "look into why...", "find logs for...", "what happened at...", "check the error rate for..."

### `triage`

Use for on-call sweeps: reviewing open issues, silencing noisy log patterns, muting flapping monitors, and bulk-actioning alert queues.

**Triggers:** "triage open issues", "do an on-call sweep", "acknowledge the alerts", "silence the noisy monitors", "clear the issue queue"

### `instrument`

Instrument an application with OpenTelemetry so traces, logs, and metrics flow into Monoscope. Detects the language and framework, installs the appropriate Monoscope SDK or OTel packages, writes the SDK init/middleware code, configures OTLP exporter env vars, and verifies data is flowing with the CLI.

Native Monoscope SDKs (richer: request/response capture, error reporting, outgoing request monitoring) are available for: Express, Fastify, NestJS, FastAPI, Django, Gin, Echo, Chi, Fiber, Spring Boot, Laravel. Standard OTel auto-instrumentation is used for Ruby, Rust, .NET, Flask, and other languages.

Key Monoscope-specific details this skill knows:
- Endpoint: `http://otelcol.monoscope.tech:4317` (gRPC) or `:4318` (HTTP/protobuf)
- Auth via `OTEL_RESOURCE_ATTRIBUTES="x-api-key={API_KEY}"` — not headers
- Native SDK packages: `@monoscopetech/express`, `monoscope-fastapi`, `github.com/monoscope-tech/monoscope-go/gin`, `io.monoscope.springboot:monoscope-springboot`, `monoscope/laravel`
- Redaction: JSONPath expressions for request/response body fields

**Triggers:** "instrument my app", "add OpenTelemetry", "set up tracing", "wire up observability", "get data into Monoscope", "configure the OTLP exporter", "add the monoscope SDK"

## Prerequisites

All skills require:

```bash
export MONOSCOPE_API_KEY=<your-api-key>
export MONOSCOPE_PROJECT=<your-project-uuid>
```

The agent will remind you if these are missing. You can also set them permanently:

```bash
monoscope config set api_key <your-api-key>
monoscope config set project <your-project-uuid>
```

## Installing the CLI

```bash
curl monoscope.tech/install.sh | sh
monoscope auth login
```
