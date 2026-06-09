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
5. **Background jobs / scheduled tasks** — every worker, cron, or scheduler (see Step 3 detection table).

**Always prefer auto-instrumentation over manual spans.** Use the language's official OTel auto-instrumentation path first (`@opentelemetry/auto-instrumentations-node`, `opentelemetry-instrument` for Python, `otel-agent` Java javaagent, `OpenTelemetry.AutoInstrumentation` for .NET, the Go `otel*` middleware/contrib packages, etc.). Only fall back to manual span wrapping when no auto-instrumentation exists for that library — and in that case, follow the canonical doc's language-idiomatic pattern.

## Step 0 — Plan first, then execute

Before touching any file, **always** produce a written plan and a todo list (use the `TaskCreate` tool). Do not start installing packages or editing init code until the plan exists. The plan keeps the agent honest about coverage and gives the user a checkpoint to redirect scope.

The todo list **must** include, at minimum, one task per item below — in this order:

1. Detect language, framework, and the libraries in use for each of the five required surfaces (incoming HTTP, outgoing HTTP, SQL, message queues, background jobs).
2. Fetch the canonical Monoscope SDK doc for the detected framework.
3. Install SDK / auto-instrumentation packages and wire up init.
4. Instrument incoming HTTP.
5. Instrument outgoing HTTP.
6. Instrument SQL / database drivers.
7. Instrument message queues / Kafka / streaming.
8. Instrument background jobs / schedulers / workers.
9. **Verify locally** that telemetry actually emits (Step 4 — collector debug exporter, per-surface assertions).
10. Switch to the remote Monoscope endpoint.
11. **Verify remotely** that telemetry arrives in Monoscope (Step 6 — CLI assertion battery).
12. Report the coverage matrix and final pass/fail summary.

Mark each todo complete as it finishes — never batch. If a surface genuinely doesn't apply (e.g. no SQL driver in use), keep the todo but resolve it as "none in use — confirmed with user" rather than silently dropping it. The two verification steps (9 and 11) are **mandatory** — the task is not done until both pass.

## Prerequisites

Monoscope account, project created, API key copied from **API Keys** in the dashboard. The API key travels via `OTEL_RESOURCE_ATTRIBUTES="x-api-key=…"`, **not** an HTTP header. OTLP endpoint: `http://otelcol.monoscope.tech:4317` (gRPC) or `:4318` (HTTP/protobuf).

## Step 1 — Detect the stack

```bash
ls package.json pyproject.toml requirements.txt go.mod Cargo.toml pom.xml build.gradle Gemfile composer.json *.csproj 2>/dev/null
```

Read the manifest, pick the framework, then map to the canonical doc URL:

| Detection | Doc URL |
|---|---|
| `package.json` + `express` | https://monoscope.tech/docs/sdks/nodejs/expressjs |
| `package.json` + `fastify` | https://monoscope.tech/docs/sdks/nodejs/fastifyjs |
| `package.json` + `@nestjs/core` | https://monoscope.tech/docs/sdks/nodejs/nestjs |
| `package.json` + `next` | https://monoscope.tech/docs/sdks/nodejs/nextjs |
| `package.json` + `@adonisjs/core` | https://monoscope.tech/docs/sdks/nodejs/adonisjs |
| `requirements.txt`/`pyproject.toml` + `fastapi` | https://monoscope.tech/docs/sdks/python/fastapi |
| Python + `django` | https://monoscope.tech/docs/sdks/python/django |
| Python + `flask` | https://monoscope.tech/docs/sdks/python/flask |
| Python + `pyramid` | https://monoscope.tech/docs/sdks/python/pyramid |
| `go.mod` + `gin-gonic/gin` | https://monoscope.tech/docs/sdks/golang/gin |
| `go.mod` + `labstack/echo` | https://monoscope.tech/docs/sdks/golang/echo |
| `go.mod` + `go-chi/chi` | https://monoscope.tech/docs/sdks/golang/chi |
| `go.mod` + `gofiber/fiber` | https://monoscope.tech/docs/sdks/golang/fiber |
| `go.mod` + `gorilla/mux` | https://monoscope.tech/docs/sdks/golang/gorillamux |
| `go.mod` (plain `net/http`) | https://monoscope.tech/docs/sdks/golang/native |
| `composer.json` + `laravel/framework` | https://monoscope.tech/docs/sdks/php/laravel |
| `composer.json` + `slim/slim` | https://monoscope.tech/docs/sdks/php/slim |
| `composer.json` + `symfony/framework-bundle` | https://monoscope.tech/docs/sdks/php/symfony |
| `pom.xml`/`build.gradle` + Spring Boot | https://monoscope.tech/docs/sdks/java/springboot |
| `*.csproj` + ASP.NET Core | https://monoscope.tech/docs/sdks/dotnet/dotnetcore |
| `mix.exs` + Phoenix | https://monoscope.tech/docs/sdks/elixir/phoenix |
| `pubspec.yaml` + `flutter:` SDK | https://monoscope.tech/docs/sdks/flutter |
| anything else (Rust, Ruby, Scala, Swift, …) | https://monoscope.tech/docs/sdks/opentelemetry |

## Step 2 — Apply the canonical guide

`WebFetch` the URL above. Extract: install command, middleware/wrapper code, env-var block. Apply them to the user's entry file. If WebFetch fails (offline, redirect), fall back to these universal env vars and the OTel auto-instrumentation path for the language:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
OTEL_SERVICE_NAME="my-service"
OTEL_RESOURCE_ATTRIBUTES="x-api-key=YOUR_API_KEY"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"   # use http/protobuf + :4318 for PHP
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

## Step 4 — Local emit verification (collector with debug exporter)

Run a local OTel collector, point the app at it, trigger spans, and grep the collector stdout. This catches misconfiguration before production.

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

  Capture each trigger's exit code / response status. Non-2xx / non-zero means the trigger itself failed — surface and stop; don't blame instrumentation.

**4d. Assert.** Wait 2–3s for the BatchSpanProcessor to flush, then grep `/tmp/otelcol.log`:

```bash
grep -c "service.name: Str(<svc>)" /tmp/otelcol.log         # ≥1
grep -c "Span Kind     : Server" /tmp/otelcol.log           # ≥1 per HTTP route hit
# For each triggered job name:
grep -c "Name           : <job-name>" /tmp/otelcol.log      # ≥1
```

Report exactly which expected spans are missing. If any are missing, **stop**; the most common causes are: SDK init imported after the framework, wrong env-var name, or BatchSpanProcessor not flushing before the app exits (CLIs need an explicit shutdown). Fix and re-run before going to remote. Kill the background app + collector when done.

## Step 5 — Switch to remote

Set `OTEL_EXPORTER_OTLP_ENDPOINT=http://otelcol.monoscope.tech:4317` and confirm `OTEL_RESOURCE_ATTRIBUTES` contains `x-api-key=…`. Restart the app. Re-trigger the same routes and jobs from Step 4c so we validate the same surface remotely.

## Step 6 — Remote assertion via Monoscope CLI

After ~30s of ingestion, run the assertion battery and grade each independently with `jq -e`:

```bash
SVC="<service-name>"

# A. Service registered
monoscope services list --since 5m | jq -e --arg s "$SVC" '.data[] | select(.service_name == $s)' >/dev/null \
  && echo "✓ A service registered" || echo "✗ A service MISSING"

# B. ≥1 server-kind span
monoscope traces search "resource.service.name == \"$SVC\" and span.kind == \"Server\"" --since 5m --limit 1 \
  | jq -e '.events | length > 0' >/dev/null \
  && echo "✓ B server span" || echo "✗ B no server span"

# C. Each triggered route
for route in "${TRIGGERED_ROUTES[@]}"; do
  monoscope traces search "resource.service.name == \"$SVC\" and attributes.http.route == \"$route\"" --since 5m --limit 1 \
    | jq -e '.events | length > 0' >/dev/null \
    && echo "✓ C $route" || echo "✗ C MISSING $route"
done

# D. Each triggered background job
for job in "${TRIGGERED_JOBS[@]}"; do
  monoscope traces search "resource.service.name == \"$SVC\" and span.name has \"$job\"" --since 5m --limit 1 \
    | jq -e '.events | length > 0' >/dev/null \
    && echo "✓ D $job" || echo "✗ D MISSING $job"
done

# E. Logs flowing
monoscope logs search "resource.service.name == \"$SVC\"" --since 5m --limit 1 \
  | jq -e '.events | length > 0' >/dev/null \
  && echo "✓ E logs flowing" || echo "✗ E no logs"
```

Print a final summary. If anything is `✗`, name the likely cause (auth filter dropping requests, sampling, redaction stripping `http.route`, API key wrong, network egress blocked) and stop. Don't claim success when assertions fail.

**No app code yet?** Smoke-test the pipeline alone with `telemetrygen`:

```bash
go install github.com/open-telemetry/opentelemetry-collector-contrib/cmd/telemetrygen@latest
telemetrygen traces --otlp-endpoint otelcol.monoscope.tech:4317 \
  --otlp-header "x-api-key=YOUR_API_KEY" --duration 5s
monoscope traces search '' --since 2m --limit 5
```

## Step 7 — Optional: redaction & custom spans

Both are documented per-language on the same canonical doc page from Step 1 — point the user there rather than restating. Universal hint: native SDKs accept `redactHeaders` / `redactRequestBody` / `redactResponseBody` (JSONPath), and any OTel SDK exposes `tracer.startSpan(...)` for custom spans.

## Output

Report:
1. Detected language/framework + canonical doc URL fetched.
2. Packages installed (auto-instrumentation preferred) and where init lives.
3. Coverage matrix for the five required surfaces — for each: **incoming HTTP**, **outgoing HTTP**, **SQL**, **message queues / Kafka**, **background jobs** — state the library detected, the auto-instrumentation enabled (or "manual span wrap"), or "none in use — confirm".
4. Local collector verify result (per-route, per-job pass/fail).
5. Remote CLI assertion battery output.
6. Env vars set; suggest committing them to `.env.example`.
