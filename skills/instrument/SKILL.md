---
name: instrument
description: Instrument an application with OpenTelemetry to send traces, logs, and metrics to Monoscope. Use when asked to add observability, set up tracing, configure OpenTelemetry, wire up the OTLP exporter, or get data flowing into Monoscope. Works for Node.js, Python, Go, Java, Ruby, Rust, and other OTel-supported languages.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Monoscope: Instrument with OpenTelemetry

Help the user add OpenTelemetry instrumentation to their application so data flows into Monoscope.

## Prerequisites

```bash
export MONOSCOPE_API_KEY=<your-api-key>
export MONOSCOPE_PROJECT=<your-project-uuid>
```

Monoscope accepts standard OTLP over gRPC (port 4317) and HTTP (port 4318). The endpoint is:

```
https://ingest.monoscope.tech
```

For self-hosted instances, use your own domain.

## Step 1 — Detect the project

Before writing any code, read the project to understand the language, framework, and package manager:

```bash
# Identify language / runtime
ls package.json pyproject.toml go.mod Cargo.toml pom.xml build.gradle Gemfile 2>/dev/null
```

Then read the relevant manifest to find the framework (Express, FastAPI, Gin, Spring, etc.).

## Step 2 — Install & configure by language

### Node.js / TypeScript

```bash
npm install @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-grpc \
  @opentelemetry/exporter-logs-otlp-grpc \
  @opentelemetry/exporter-metrics-otlp-grpc
```

Create `instrumentation.js` (or `.ts`) at the project root:

```js
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { OTLPLogExporter } = require('@opentelemetry/exporter-logs-otlp-grpc');
const { OTLPMetricExporter } = require('@opentelemetry/exporter-metrics-otlp-grpc');
const { PeriodicExportingMetricReader } = require('@opentelemetry/sdk-metrics');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter(),
  logRecordProcessor: ..., // see OTel docs for BatchLogRecordProcessor
  metricReader: new PeriodicExportingMetricReader({ exporter: new OTLPMetricExporter() }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

Set env vars (or add to `.env`):

```bash
OTEL_SERVICE_NAME=my-service
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.monoscope.tech
OTEL_EXPORTER_OTLP_HEADERS="x-monoscope-project=$MONOSCOPE_PROJECT,x-api-key=$MONOSCOPE_API_KEY"
```

Load before app entry: `node -r ./instrumentation.js server.js` (or `--import` for ESM).

---

### Python

```bash
pip install opentelemetry-sdk \
  opentelemetry-exporter-otlp \
  opentelemetry-instrumentation-auto
```

```python
# instrumentation.py — import before anything else
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
```

```bash
OTEL_SERVICE_NAME=my-service \
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.monoscope.tech \
OTEL_EXPORTER_OTLP_HEADERS="x-monoscope-project=$MONOSCOPE_PROJECT,x-api-key=$MONOSCOPE_API_KEY" \
opentelemetry-instrument python app.py
```

Auto-instrumentation (`opentelemetry-instrument`) handles Flask, Django, FastAPI, SQLAlchemy, etc. automatically.

---

### Go

```bash
go get go.opentelemetry.io/otel \
  go.opentelemetry.io/otel/sdk \
  go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc \
  go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp
```

```go
// otel.go
func initTracer(ctx context.Context) (func(), error) {
    conn, _ := grpc.DialContext(ctx, "ingest.monoscope.tech:4317", grpc.WithTransportCredentials(credentials.NewClientTLSFromCert(nil, "")))
    exporter, _ := otlptracegrpc.New(ctx, otlptracegrpc.WithGRPCConn(conn))
    tp := trace.NewTracerProvider(trace.WithBatcher(exporter), trace.WithResource(
        resource.NewWithAttributes(semconv.SchemaURL, semconv.ServiceName("my-service")),
    ))
    otel.SetTracerProvider(tp)
    return func() { tp.Shutdown(ctx) }, nil
}
```

Set headers via env: `OTEL_EXPORTER_OTLP_HEADERS`.

Wrap HTTP handlers: `otelhttp.NewHandler(mux, "server")`.

---

### Java (Spring Boot)

```xml
<!-- pom.xml: add the OTel agent, no code changes needed -->
```

Download the Java agent:

```bash
curl -L https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar \
  -o opentelemetry-javaagent.jar
```

Run:

```bash
OTEL_SERVICE_NAME=my-service \
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.monoscope.tech \
OTEL_EXPORTER_OTLP_HEADERS="x-monoscope-project=$MONOSCOPE_PROJECT,x-api-key=$MONOSCOPE_API_KEY" \
java -javaagent:opentelemetry-javaagent.jar -jar app.jar
```

---

### Ruby

```bash
gem install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-all
```

```ruby
# config/initializers/opentelemetry.rb (Rails) or require before app
require 'opentelemetry/sdk'
require 'opentelemetry/exporter/otlp'
require 'opentelemetry/instrumentation/all'

OpenTelemetry::SDK.configure do |c|
  c.service_name = 'my-service'
  c.use_all
end
```

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=https://ingest.monoscope.tech \
OTEL_EXPORTER_OTLP_HEADERS="x-monoscope-project=$MONOSCOPE_PROJECT,x-api-key=$MONOSCOPE_API_KEY"
```

---

### Rust

```toml
# Cargo.toml
[dependencies]
opentelemetry = { version = "0.27", features = ["trace"] }
opentelemetry_sdk = { version = "0.27", features = ["rt-tokio"] }
opentelemetry-otlp = { version = "0.27", features = ["grpc-tonic"] }
```

```rust
let exporter = opentelemetry_otlp::new_exporter().tonic().with_endpoint("https://ingest.monoscope.tech");
let tracer = opentelemetry_otlp::new_pipeline().tracing()
    .with_exporter(exporter)
    .install_batch(opentelemetry_sdk::runtime::Tokio)?;
```

## Step 3 — Verify data is flowing

After starting the instrumented app and generating some traffic, verify with the Monoscope CLI:

```bash
# Should show events within ~30 seconds of startup
monoscope logs search "" --since 5m --limit 5
monoscope traces search "" --since 5m --limit 5

# If empty, check the service name appeared
monoscope services list --since 5m
```

If no data appears after 1–2 minutes:

1. Check `OTEL_EXPORTER_OTLP_ENDPOINT` — must be `https://ingest.monoscope.tech` (no trailing slash, no port for HTTPS)
2. Check `OTEL_EXPORTER_OTLP_HEADERS` includes both `x-monoscope-project` and `x-api-key`
3. Enable OTel debug logging: `OTEL_LOG_LEVEL=debug` to see exporter errors in stdout
4. For gRPC: ensure port 4317 is reachable; for HTTP/protobuf use port 4318 and set `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf`

## Step 4 — Add custom spans and attributes (optional)

Once auto-instrumentation is working, add custom spans for business-critical paths:

```js
// Node.js example
const tracer = trace.getTracer('my-service');
const span = tracer.startSpan('process-payment');
span.setAttributes({ 'payment.amount': 99.99, 'payment.currency': 'USD' });
// ... do work ...
span.end();
```

These attributes become searchable in Monoscope via KQL:
```
attributes.payment.currency == "USD" and severity.text == "error"
```

## Output

After completing instrumentation, confirm:
1. Which packages were installed and where the config lives
2. Which env vars need to be set (and suggest adding them to `.env` / `.env.example`)
3. That `monoscope services list` shows the service
4. Any framework-specific notes (e.g. "wrap your Gin router with `otelgin.Middleware`")
