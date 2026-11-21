---
name: instrument
description: Instrument an application with OpenTelemetry to send traces, logs, and metrics to Monoscope. Use when asked to add observability, set up tracing, configure OpenTelemetry, wire up the OTLP exporter, or get data flowing into Monoscope. Works for Node.js (Express, Fastify, NestJS), Python (FastAPI, Django, Flask), Go (Gin, Echo, Chi, Fiber), Java (Spring Boot), PHP (Laravel, Slim, Symfony), .NET, Ruby, Rust, Flutter, and any OTel-supported language.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch
---

# Monoscope: Instrument with OpenTelemetry

Route the user to the canonical SDK guide, then **prove telemetry actually arrives** — both locally (collector debug exporter) and remotely (Monoscope CLI assertion). Do not skip steps; "looks installed" is not the same as "is emitting."

## Minimum instrumentation coverage (non-negotiable)

A complete integration **must** emit spans for all of the following surfaces. Treat each as a required checklist item — if any is missing for the detected stack, instrument it before declaring the task done.

1. **Incoming HTTP requests** — every server route (framework middleware / handler instrumentation).
2. **Outgoing HTTP requests** — every client call (fetch / axios / requests / httpx / `net/http` / Guzzle / `HttpClient` / OkHttp, etc.). Auto-instrumentation covers this when enabled — verify it is.
3. **SQL queries** — all database drivers in use (pg, mysql2, psycopg, SQLAlchemy, GORM, `database/sql`, JDBC, PDO, ActiveRecord, EF Core, etc.). Spans must include `db.system` and `db.statement`.
4. **Message queues / streaming** — producers and consumers for Kafka, RabbitMQ, SQS, NATS, Redis Streams, Google Pub/Sub, Azure Service Bus, etc. Spans must include `messaging.system` and `messaging.destination.name`.
5. **Background jobs / scheduled tasks** — every worker, cron, scheduler, startup migration/seeder/backfill, database-backed poller, and ad-hoc goroutine/task (see Step 3 detection table). Each run must own its downstream SQL/HTTP spans in the same trace. A job span and unrelated root SQL spans do **not** constitute coverage.

**Always prefer auto-instrumentation over manual spans.** Use the language's official OTel auto-instrumentation path first (`@opentelemetry/auto-instrumentations-node`, `opentelemetry-instrument` for Python, `otel-agent` Java javaagent, `OpenTelemetry.AutoInstrumentation` for .NET, the Go `otel*` middleware/contrib packages, etc.). Only fall back to manual span wrapping when no auto-instrumentation exists for that library — and in that case, follow the canonical doc's language-idiomatic pattern.

## Step 0 — Plan first, then execute

Before touching any file, **always** produce a written plan and a todo list (use `TaskCreate` when the harness provides it; otherwise maintain a written checklist). Do not start installing packages or editing init code until the plan exists. The plan keeps the agent honest about coverage and gives the user a checkpoint to redirect scope.

The todo list **must** include, at minimum, one task per item below — in this order:

1. Detect language, framework, and the libraries in use for each of the five required surfaces (incoming HTTP, outgoing HTTP, SQL, message queues, background jobs).
2. Fetch the canonical Monoscope SDK doc for the detected framework.
3. Install SDK / auto-instrumentation packages and wire up init.
4. Instrument incoming HTTP.
5. Instrument outgoing HTTP.
6. Instrument SQL / database drivers.
7. Instrument message queues / Kafka / streaming.
8. Instrument background jobs / schedulers / workers.
9. **Verify locally** that telemetry actually emits and is connected (Step 4 — collector debug exporter, per-surface and parent/trace-ID assertions).
10. Switch to the remote Monoscope endpoint.
11. **Verify remotely** that telemetry arrives in Monoscope with intact job-to-SQL/HTTP relationships (Step 6 — CLI assertion battery and trace topology).
12. Report the coverage matrix and final pass/fail summary.

Mark each todo complete as it finishes — never batch. If a surface genuinely doesn't apply (e.g. no SQL driver in use), keep the todo but resolve it as "none in use — confirmed with user" rather than silently dropping it. The two verification steps (9 and 11) are **mandatory** — the task is not done until both pass.

## Prerequisites

Monoscope account, project created, API key copied from **API Keys** in the dashboard. The API key travels via `OTEL_RESOURCE_ATTRIBUTES="x-api-key=…"`, **not** an HTTP header. OTLP endpoint: `https://otel.monoscopehq.com` (port 443, gRPC or HTTP/protobuf).

## Step 1 — Detect the stack

```bash
ls package.json pyproject.toml requirements.txt go.mod Cargo.toml pom.xml build.gradle Gemfile composer.json *.csproj 2>/dev/null
```

Read the manifest, pick the framework, then map to the canonical doc URL:

| Detection | Doc URL |
|---|---|
| `package.json` + `express` | https://monoscopehq.com/docs/sdks/nodejs/expressjs |
| `package.json` + `fastify` | https://monoscopehq.com/docs/sdks/nodejs/fastifyjs |
| `package.json` + `@nestjs/core` | https://monoscopehq.com/docs/sdks/nodejs/nestjs |
| `package.json` + `next` | https://monoscopehq.com/docs/sdks/nodejs/nextjs |
| `package.json` + `@adonisjs/core` | https://monoscopehq.com/docs/sdks/nodejs/adonisjs |
| `requirements.txt`/`pyproject.toml` + `fastapi` | https://monoscopehq.com/docs/sdks/python/fastapi |
| Python + `django` | https://monoscopehq.com/docs/sdks/python/django |
| Python + `flask` | https://monoscopehq.com/docs/sdks/python/flask |
| Python + `pyramid` | https://monoscopehq.com/docs/sdks/python/pyramid |
| `go.mod` + `gin-gonic/gin` | https://monoscopehq.com/docs/sdks/golang/gin |
| `go.mod` + `labstack/echo` | https://monoscopehq.com/docs/sdks/golang/echo |
| `go.mod` + `go-chi/chi` | https://monoscopehq.com/docs/sdks/golang/chi |
| `go.mod` + `gofiber/fiber` | https://monoscopehq.com/docs/sdks/golang/fiber |
| `go.mod` + `gorilla/mux` | https://monoscopehq.com/docs/sdks/golang/gorillamux |
| `go.mod` (plain `net/http`) | https://monoscopehq.com/docs/sdks/golang/native |
| `composer.json` + `laravel/framework` | https://monoscopehq.com/docs/sdks/php/laravel |
| `composer.json` + `slim/slim` | https://monoscopehq.com/docs/sdks/php/slim |
| `composer.json` + `symfony/framework-bundle` | https://monoscopehq.com/docs/sdks/php/symfony |
| `pom.xml`/`build.gradle` + Spring Boot | https://monoscopehq.com/docs/sdks/java/springboot |
| `*.csproj` + ASP.NET Core | https://monoscopehq.com/docs/sdks/dotnet/dotnetcore |
| `mix.exs` + Phoenix | https://monoscopehq.com/docs/sdks/elixir/phoenix |
| `pubspec.yaml` + `flutter:` SDK | https://monoscopehq.com/docs/sdks/flutter |
| anything else (Rust, Ruby, Scala, Swift, …) | https://monoscopehq.com/docs/sdks/opentelemetry |

## Step 2 — Apply the canonical guide

Fetch the URL above (your web-fetch tool, or `curl -sL`). Extract: install command, middleware/wrapper code, env-var block. Apply them to the user's entry file. If the fetch fails (offline, redirect), fall back to these universal env vars and the OTel auto-instrumentation path for the language:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT="https://otel.monoscopehq.com"
OTEL_SERVICE_NAME="my-service"
OTEL_RESOURCE_ATTRIBUTES="x-api-key=YOUR_API_KEY"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"   # use http/protobuf for PHP (same endpoint)
```

## Step 3 — Cover the required surfaces (HTTP-out, SQL, queues, jobs)

HTTP server middleware only covers inbound requests. The four other required surfaces (outgoing HTTP, SQL, messaging, background jobs) must each be wired up explicitly — usually by enabling the right auto-instrumentation package, occasionally by wrapping a handler by hand.

**Detect** what is in use (grep manifests + source). For each row found, enable the matching auto-instrumentation; only fall back to manual spans when none exists.

| Surface | Detect | Preferred auto-instrumentation |
|---|---|---|
| **Outgoing HTTP** | `axios`, `node-fetch`, `got`, `undici`; `requests`, `httpx`, `aiohttp`, `urllib3`; Go `net/http` client, `resty`; `Guzzle`, `Symfony\HttpClient`; `HttpClient`, `OkHttp`, `RestTemplate`, `WebClient` | Node: `@opentelemetry/instrumentation-http` + `-undici`/`-fetch`. Python: `opentelemetry-instrumentation-requests` / `-httpx` / `-urllib3` / `-aiohttp-client`. Go: `otelhttp.NewTransport`. Java: javaagent (covers HttpClient/OkHttp/Apache). .NET: `OpenTelemetry.Instrumentation.Http`. PHP: Guzzle middleware from the OTel contrib. |
| **SQL / DB** | `pg`, `mysql2`, `mongodb`, `prisma`; `psycopg`, `asyncpg`, `sqlalchemy`, `django.db`; `database/sql`, `gorm.io/gorm`, `jackc/pgx`; JDBC drivers; `pdo`, `eloquent`; `ActiveRecord`; `EntityFrameworkCore` | Node: `@opentelemetry/instrumentation-pg` / `-mysql2` / `-mongodb` / `-prisma`. Python: `opentelemetry-instrumentation-psycopg2` / `-sqlalchemy` / `-django` / `-asyncpg`. Go: `otelsql.Register` or `otelgorm`. Java: javaagent covers JDBC. .NET: `OpenTelemetry.Instrumentation.SqlClient` / `EntityFrameworkCore`. PHP: PDO auto-instr. Ruby: `opentelemetry-instrumentation-active_record`. |
| **Message queues / streaming** | `kafkajs`, `confluent-kafka`, `amqplib`, `bullmq`, `@aws-sdk/client-sqs`, `nats`, `ioredis` streams; `confluent-kafka`, `pika`, `kombu`, `aio-pika`; `segmentio/kafka-go`, `Shopify/sarama`, `streadway/amqp`; Spring `@KafkaListener` / `@RabbitListener` / `@JmsListener`; .NET `Confluent.Kafka`, `MassTransit`; Symfony Messenger; Sidekiq + Karafka | Node: `@opentelemetry/instrumentation-kafkajs` / `-amqplib` / `-aws-sdk` (SQS/SNS). Python: `opentelemetry-instrumentation-kafka-python` / `-pika` / `-confluent-kafka` / `-aio-pika` / `-celery`. Go: `otelkafka` / `otelsarama` / `otelamqp`. Java: javaagent covers Kafka/RabbitMQ/JMS. .NET: `OpenTelemetry.Instrumentation.ConfluentKafka`. Manually add `messaging.system` + `messaging.destination.name` on any consumer the auto-instr doesn't reach. |
| **Background jobs / schedulers** | Node: `bullmq`, `bull`, `agenda`, `bee-queue`, `node-cron`; `**/workers/**`, `**/jobs/**`. Python: `celery`, `rq`, `dramatiq`, `apscheduler`, `huey`; `manage.py` custom commands. Go: `robfig/cron`, `hibiken/asynq`, `RichardKnop/machinery`; binaries under `cmd/` other than the web server. PHP: `artisan queue:work`, `App\Console\Kernel` schedule, Symfony Messenger handlers. Java: `@Scheduled`, `@KafkaListener`, `@JmsListener`, `@RabbitListener`. .NET: `IHostedService`, `BackgroundService`. Elixir: Oban workers, Broadway pipelines, GenServer pollers. Ruby: Sidekiq workers, ActiveJob, `whenever` cron. | Use the dedicated package where one exists (`opentelemetry-instrumentation-celery`, `opentelemetry-instrumentation-sidekiq`, BullMQ via `@opentelemetry/instrumentation-bullmq`, `otelasynq`). Otherwise wrap each job handler with `tracer.startSpan(job_name, { kind: CONSUMER })` and set `messaging.system` / `messaging.destination.name`. CLIs need an explicit tracer shutdown before `process.exit` or the BatchSpanProcessor will drop spans. |

For each row above where the framework's canonical doc (Step 2) calls out a specific recipe, follow that recipe — it's tuned to the framework's startup order and middleware chain.

If after grepping you cannot find any usage of a given surface, state that explicitly ("no SQL driver in use", "no message queue libraries imported") so the user can correct you. Do **not** silently skip a surface.

### Job boundaries and context propagation (required)

Do not restrict discovery to queue libraries or `workers/` directories. Inspect startup/init code, migrations, seeders, one-time tasks, reconciliation/backfills, retry/error bookkeeping, polling loops, timer callbacks, and anonymous `go`/thread/task launches. A PostgreSQL table used as a work queue is a job system even with no broker dependency.

For each run:

1. Start its span **before** fetching/validating/preloading work. Put item spans underneath that run span. Include retries, failures, and status/error updates. Do not wrap only the external send while leaving routing/lookup queries as root spans.
2. Pass the span's context through **every** nested service/repository/client call. Audit helpers for `context.Background()`/`context.TODO()`, `WithContext`/session overrides, new timeout contexts, and context-less interfaces. A context-bearing ORM handle does not help if a repository subsequently overwrites it with a root context. Use context-aware APIs or compatible context-aware adapters; do not mutate shared clients or use global goroutine context storage.
3. In Go, use `db.WithContext(ctx)`, `http.NewRequestWithContext(ctx, ...)`, `context.WithTimeout(ctx, ...)`, and pass `ctx` into goroutines. If detached work must outlive an HTTP request, `context.WithoutCancel(ctx)` preserves trace values; give the detached operation its own bounded lifetime. Never replace it with `context.Background()` just to avoid cancellation. Other languages must preserve the active OTel context across async/thread boundaries using their idiomatic APIs.
4. Keep the job span open through completion of its launched work. For an API that returns immediately after dispatch, hand off span completion to the worker/wait group rather than ending it in the dispatcher's defer. Do not silently change concurrency or business semantics just to make a trace look grouped.
5. Scope startup migrations/seeders under named startup spans and propagate that context to raw SQL too. Inspect framework-generated connection checks: for example, GORM's automatic `Ping()` has no caller context; use `PingContext(ctx)` with automatic ping disabled if this emits orphan connection spans. Keep long-lived DB/client handles independent of a completed startup span.
6. Ensure framework context adapters forward trace values (for example Gin code passing `*gin.Context` to repositories requires request-context forwarding or explicit `c.Request.Context()`). Record real job errors, not unconditional success.

Also inspect sampling and bounded BatchSpanProcessor queues. A migration/seeding burst can fill a non-blocking queue and drop a later-ending parent even though earlier SQL spans arrived. In-memory recorders observe spans **before export** and cannot detect this loss. Exercise realistic bursts, verify exported parents/children, and tune queue size/export throughput within the application's memory/latency budget (for example `OTEL_BSP_MAX_QUEUE_SIZE`). Do not disable sampling or enable blocking export globally without considering production impact.

Span kind should match the work: use CONSUMER for queued/database-polled items and INTERNAL for non-messaging startup/scheduled work where appropriate. Do not invent a broker solely to populate messaging attributes.

## Step 4 — Local emit verification (collector with debug exporter)

Run a local OTel collector, point the app at it, trigger spans, and inspect the collector stdout. Span-count greps are only the first check; parent/trace-ID assertions are mandatory. This catches disconnected instrumentation before production.

**4a. Stand up the collector.** Write `otel-collector-debug.yaml`:

```yaml
receivers:
  otlp:
    protocols: { grpc: { endpoint: 0.0.0.0:4317 }, http: { endpoint: 0.0.0.0:4318 } }
exporters:
  debug: { verbosity: detailed }
service:
  pipelines:
    traces:  { receivers: [otlp], exporters: [debug] }
    metrics: { receivers: [otlp], exporters: [debug] }
    logs:    { receivers: [otlp], exporters: [debug] }
```

If `docker info >/dev/null 2>&1` succeeds:

```bash
docker run --rm -p 4317:4317 -p 4318:4318 \
  -v "$(pwd)/otel-collector-debug.yaml:/etc/otelcol-contrib/config.yaml" \
  otel/opentelemetry-collector-contrib:latest 2>&1 | tee /tmp/otelcol.log
```

Otherwise download the `otelcol-contrib` binary for the user's OS/arch from `https://github.com/open-telemetry/opentelemetry-collector-releases/releases/latest`, extract, and run `./otelcol-contrib --config otel-collector-debug.yaml 2>&1 | tee /tmp/otelcol.log`. Run in the background.

**4b. Boot the app at the local collector.** Override `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317` for this run (keep production env untouched). Start the app in the background; capture the PID for cleanup.

> **Mobile / Flutter caveat:** physical devices and iOS simulators can't reach `localhost`. Use the host's LAN IP (`ipconfig getifaddr en0` on macOS) instead, e.g. `http://192.168.1.42:4317`. Android emulators map host loopback to `10.0.2.2`. Configure the collector to bind on `0.0.0.0` (the YAML above already does).

**4c. Discover entry points and trigger spans.** Don't just `curl /` — enumerate concrete things to invoke.

- **HTTP routes:**
  - FastAPI / Spring Boot Actuator: `curl localhost:<port>/openapi.json` or `/actuator/mappings`.
  - Express/Fastify/Nest: scan `app.get/post/...` calls or controller decorators.
  - Django: `python manage.py show_urls` (django-extensions) or grep `urls.py`.
  - Gin/Echo/Chi: grep `r.GET(` / `r.POST(` etc.
  - Laravel: `php artisan route:list --json`.
  - Rails: `bundle exec rails routes --json`.
  - Fallback: ask the user for one known route.

  Hit at least 3 routes (capped at 10), GET directly, POST/PUT/PATCH with `Content-Type: application/json` and `{}` (or a body inferred from the OpenAPI schema). Skip auth-gated routes unless the user provides a token.

- **Background jobs:** invoke each enumerated worker once.
  - BullMQ/Bull/Agenda → write `trigger-job.js` that imports the queue and calls `queue.add('test-trigger', {})`.
  - Celery → `python -c "from app.tasks import t; t.delay()"` or `celery -A <app> call <task>`.
  - Sidekiq/ActiveJob → `bundle exec rails runner "MyJob.perform_later"`.
  - Go cron/asynq → one-shot binary that calls the handler directly.
  - Spring `@Scheduled` → temporarily lower fixedRate, or call the bean via a debug endpoint.
  - Laravel queue → `php artisan tinker` to dispatch, then `php artisan queue:work --once`.
  - .NET `BackgroundService` → call the registered service from a one-shot console invocation.
  - Last resort: instruct the user to run their job manually.

  Exercise non-empty workloads, nested repository lookups, and failure/retry paths where safely possible. An empty poll proves only the polling query, not item processing. Use disposable data and mocked external providers; ask before starting code that migrates/deletes/reseeds data or sends live payments/emails/webhooks. Label test fixture setup, polling, and teardown with explicit fixture spans (or disable instrumentation only for the probe client). Do not mistake probe-generated SQL/HTTP for application coverage, and do not hide application orphan queries by filtering them out.

  Capture each trigger's exit code / response status. Non-2xx / non-zero means the trigger itself failed — surface and stop; don't blame instrumentation.

**4d. Assert existence, then topology.** Flush the BatchSpanProcessor before inspecting `/tmp/otelcol.log` (one-shot tests/CLIs should explicitly shut down providers):

```bash
grep -c "service.name: Str(<svc>)" /tmp/otelcol.log         # ≥1
grep -c "Span Kind     : Server" /tmp/otelcol.log           # ≥1 per HTTP route hit
# For each triggered job name:
grep -c "Name           : <job-name>" /tmp/otelcol.log      # ≥1
```

For each triggered job, inspect `Trace ID`, `ID`, and `Parent ID` on the run, item, SQL, and HTTP spans. Build an index keyed by **(trace ID, span ID)** and walk downstream parent chains:

- Every expected job that executed SQL/HTTP has at least one such descendant, not merely a span elsewhere with the same name.
- Descendants share the run's trace ID, and each non-root parent resolves within the captured trace. Nested item spans are allowed; SQL need not be an immediate child of the run.
- Fail on missing run spans, SQL/HTTP roots belonging to a job, cross-trace parent IDs, missing intermediate spans, or cycles. Scan startup and error paths too. Explain genuinely independent infrastructure/fixture activity separately; do not blanket-whitelist root SQL.
- Check a bounded run window and capture complete traces, not only a limited search result. In-memory SDK span recorders can enforce these invariants as regression tests, but also prove those relationships survive the collector/export pipeline.

The bundled checker accepts collector debug logs, OTLP JSON, or normalized full span JSON:

```bash
python3 scripts/assert-trace-topology.py /tmp/otelcol.log \
  --job payment.process --job payment.send --require-sql \
  --allow-root telemetry.fixture
```

`--allow-root` names an explicit **ancestor span**, not a whitelist for orphan SQL. Run `python3 -m unittest discover -s scripts -p 'test_*.py'` from this skill directory to test the checker. Treat a disconnected-span failure exactly like a missing-span failure: fix context propagation and rerun before switching to remote.

Report exactly which expected spans are missing. If any are missing, **stop**; the most common causes are: SDK init imported after the framework, wrong env-var name, or BatchSpanProcessor not flushing before the app exits (CLIs need an explicit shutdown). Fix and re-run before going to remote. Kill the background app + collector when done.

## Step 5 — Switch to remote

Set `OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.monoscopehq.com` and confirm `OTEL_RESOURCE_ATTRIBUTES` contains `x-api-key=…`. Restart the app. Re-trigger the same routes and jobs from Step 4c so we validate the same surface remotely.

## Step 6 — Remote assertion via Monoscope CLI

After ingestion, discover this deployment's field names with `monoscope --json schema --search kind --limit 20` and `--search span --limit 20`. Consult `kql-reference`; do not invent fields or confuse a query parse error with missing telemetry. Current deployments use `kind == "server"` / `"consumer"` and `span_name`. Request JSON explicitly and grade each assertion independently with `jq -e`:

```bash
SVC="<service-name>"

# A. Service registered
monoscope --json services list --since 5m | jq -e --arg s "$SVC" '.services[] | select(.name == $s)' >/dev/null \
  && echo "✓ A service registered" || echo "✗ A service MISSING"

# B. ≥1 server-kind span
monoscope --json traces search "resource.service.name == \"$SVC\" and kind == \"server\"" --since 5m --limit 1 \
  | jq -e '.events | length > 0' >/dev/null \
  && echo "✓ B server span" || echo "✗ B no server span"

# C. Each triggered route
for route in "${TRIGGERED_ROUTES[@]}"; do
  monoscope --json traces search "resource.service.name == \"$SVC\" and attributes.http.route == \"$route\"" --since 5m --limit 1 \
    | jq -e '.events | length > 0' >/dev/null \
    && echo "✓ C $route" || echo "✗ C MISSING $route"
done

# D. Each triggered background job
for job in "${TRIGGERED_JOBS[@]}"; do
  monoscope --json traces search "resource.service.name == \"$SVC\" and span_name == \"$job\"" --since 5m --limit 1 \
    | jq -e '.events | length > 0' >/dev/null \
    && echo "✓ D $job" || echo "✗ D MISSING $job"
done

# E. Logs flowing
monoscope --json logs search "resource.service.name == \"$SVC\"" --since 5m --limit 1 \
  | jq -e '.events | length > 0' >/dev/null \
  && echo "✓ E logs flowing" || echo "✗ E no logs"
```

**F. Job-to-downstream topology (mandatory).** Existence assertions A–E are not sufficient. For each triggered run, verify downstream SQL/HTTP parent chains and same-trace IDs using the same local invariants. Search summaries may omit raw attributes/span identities; use `monoscope --json traces get <event-id> --at <timestamp>` for full event detail. Inspect the actual output shape before treating `--tree` as a complete trace: some CLI versions output only one event under `--json`. Detect truncation/pagination and fetch missing spans before asserting; do not infer grouping from timestamps or service names.

For large traces, an exhaustive `summarize count() by context.trace_id, parent_id` over downstream SQL/HTTP can prove all parent edges without fetching thousands of payloads: fetch full details for each job and every referenced intermediate parent, walk their same-trace chains, and verify aggregate result limits and counts against the known complete capture. If a referenced parent is itself a downstream span, fetch that intermediate span too. A limit-1 direct-child query proves only one representative edge, not coverage of all nested work. Query independently for unexpected root SQL within the verified run window and investigate any hits.

Prefer UTC timestamps ending in `Z` for `--from`/`--to`/`--at` and verify the returned timestamps/effective query window. Some CLI versions mishandle `+00:00` offsets or unsupported relative durations and silently fall back to a default range, returning old orphan queries. Do not label historical telemetry as a failure of the new run, nor accept an empty result from the wrong range as success.

The server may normalize legacy `db.system`/`db.statement` to `attributes.db.system.name`/`attributes.db.query.text`. Discover schema and read full event detail before concluding attributes were lost. Keep secrets/resource API keys out of printed trace dumps.

Print a final summary. If anything is `✗`, name the likely cause (auth filter dropping requests, sampling, redaction stripping `http.route`, API key wrong, network egress blocked) and stop. Don't claim success when assertions fail.

**No app code yet?** Smoke-test the pipeline alone with the CLI's built-in `telemetrygen` (the OTLP endpoint is derived from the configured API URL / `MONOSCOPE_API_URL`):

```bash
monoscope telemetrygen --kind trace --rate 5 --count 25 --service smoke-test
monoscope traces search '' --since 2m --limit 5
```

## Step 7 — Optional: redaction & custom spans

Both are documented per-language on the same canonical doc page from Step 1 — point the user there rather than restating. Universal hint: native SDKs accept `redactHeaders` / `redactRequestBody` / `redactResponseBody` (JSONPath), and any OTel SDK exposes `tracer.startSpan(...)` for custom spans.

## Output

Report:
1. Detected language/framework + canonical doc URL fetched.
2. Packages installed (auto-instrumentation preferred) and where init lives.
3. Coverage matrix for the five required surfaces — for each: **incoming HTTP**, **outgoing HTTP**, **SQL**, **message queues / Kafka**, **background jobs** — state the library detected, the auto-instrumentation enabled (or "manual span wrap"), or "none in use — confirm".
4. Local collector verify result (per-route, per-job, and same-trace parent-chain pass/fail; orphan/missing-parent counts).
5. Remote CLI assertion battery output, including job-to-SQL/HTTP topology and any unverified/truncated traces.
6. Env vars set; suggest committing them to `.env.example`.
