---
name: instrument
description: Instrument an application with OpenTelemetry to send traces, logs, and metrics to Monoscope. Use when asked to add observability, set up tracing, configure OpenTelemetry, wire up the OTLP exporter, or get data flowing into Monoscope. Works for Node.js (Express, Fastify, NestJS), Python (FastAPI, Django, Flask), Go (Gin, Echo, Chi, Fiber), Java (Spring Boot), PHP (Laravel, Slim, Symfony), .NET, Ruby, Rust, and any OTel-supported language.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# Monoscope: Instrument with OpenTelemetry

Help the user add OpenTelemetry instrumentation to their application so data flows into Monoscope.

## Prerequisites

Ensure the user has a Monoscope account, a project created, and an API key. The API key is found in the dashboard under **API Keys** (bottom-left). They'll also need the project UUID from the project URL.

## OTLP Endpoints

```
gRPC:          http://otelcol.monoscope.tech:4317
HTTP/protobuf: http://otelcol.monoscope.tech:4318
```

For self-hosted instances, replace `otelcol.monoscope.tech` with your own domain.

## Core Environment Variables

These apply to every language and framework:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
OTEL_SERVICE_NAME="my-service"
OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
```

> The API key is passed via `OTEL_RESOURCE_ATTRIBUTES`, not as an HTTP header.

## Step 1 — Detect the project

Read the project to identify the language, framework, and package manager:

```bash
ls package.json pyproject.toml go.mod Cargo.toml pom.xml build.gradle Gemfile composer.json *.csproj 2>/dev/null
```

Then read the manifest to identify the framework (Express, FastAPI, Gin, Spring Boot, Laravel, etc.). Choose the path below that matches.

---

## Step 2 — Install & configure by language

### Node.js — Express

Monoscope has a native SDK that wraps OTel with request/response capture and error reporting.

```bash
npm install --save @monoscopetech/express @opentelemetry/api @opentelemetry/auto-instrumentations-node
```

Add to the top of your entry file (before other imports):

```js
import 'dotenv/config';
import '@opentelemetry/auto-instrumentations-node/register';
import Monoscope from '@monoscopetech/express';

const monoscope = Monoscope.NewClient({
  serviceName: 'my-service',
  debug: false,
  // captureRequestBody: true,
  // captureResponseBody: true,
  // redactHeaders: ['Authorization'],
  // redactResponseBody: ['$.password'],
});

// After app = express():
app.use(monoscope.expressMiddleware);
app.use(monoscope.errorMiddleware); // place after routes to capture errors
```

Set env vars:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
OTEL_SERVICE_NAME="my-service"
OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
```

**Monitoring outgoing Axios requests:**

```js
// Global (all axios calls):
Monoscope.NewClient({ monitorAxios: axiosInstance });

// Per-request:
import { observeAxios } from '@monoscopetech/express';
const res = await observeAxios({ urlWildcard: '/api/v1/:id' })(axiosInstance.get('/api/v1/123'));
```

**Reporting errors manually:**

```js
import { reportError } from '@monoscopetech/express';
try { /* ... */ } catch (err) { reportError(req, err); throw err; }
```

---

### Node.js — Fastify

```bash
npm install --save @monoscopetech/fastify @opentelemetry/api @opentelemetry/auto-instrumentations-node
```

```js
import 'dotenv/config';
import '@opentelemetry/auto-instrumentations-node/register';
import Monoscope from '@monoscopetech/fastify';

const monoscopeClient = Monoscope.NewClient({ serviceName: 'my-service' });
monoscopeClient.initializeHooks(fastify); // pass your fastify instance
```

Same env vars as Express. Axios monitoring and `reportError` work identically.

---

### Node.js — NestJS

With the default Express adapter:

```bash
npm install --save @monoscopetech/express @opentelemetry/api @opentelemetry/auto-instrumentations-node
```

In `main.ts`:

```ts
import 'dotenv/config';
import '@opentelemetry/auto-instrumentations-node/register';
import Monoscope from '@monoscopetech/express';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  const monoscope = Monoscope.NewClient({ serviceName: 'my-service' });
  app.use(monoscope.expressMiddleware);
  app.use(monoscope.errorMiddleware);
  await app.listen(3000);
}
```

With the Fastify adapter, follow the Fastify guide above instead.

---

### Python — FastAPI

```bash
pip install monoscope-fastapi opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
```

```python
# main.py
from monoscope_fastapi import Monoscope
from fastapi import FastAPI

app = FastAPI()
monoscope = Monoscope(
    service_name="my-service",
    # capture_request_body=True,
    # capture_response_body=True,
    # redact_headers=["Authorization"],
    # redact_response_body=["$.password"],
)
app.middleware("http")(monoscope.middleware)
```

Set env vars and run:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true

opentelemetry-instrument uvicorn main:app --host 0.0.0.0 --port 8000
# or: opentelemetry-instrument gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Reporting errors / monitoring outgoing requests:**

```python
from monoscope_fastapi import report_error, observe_request

# In exception handler:
report_error(request, exc)

# Wrapping httpx for outgoing request monitoring:
async with observe_request(request) as client:
    resp = await client.get("https://api.example.com/data")
```

---

### Python — Django

```bash
pip install monoscope-django opentelemetry-distro opentelemetry-exporter-otlp
opentelemetry-bootstrap -a install
```

In `settings.py`:

```python
MIDDLEWARE = [
    'monoscope_django.MonoscopeMiddleware',
    # ... other middleware
]

# Optional config via settings:
MONOSCOPE_CAPTURE_REQUEST_BODY = True
MONOSCOPE_CAPTURE_RESPONSE_BODY = True
MONOSCOPE_REDACT_HEADERS = ["Authorization"]
MONOSCOPE_REDACT_REQUEST_BODY = ["$.password"]
MONOSCOPE_REDACT_RESPONSE_BODY = ["$.password"]
```

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
export DJANGO_SETTINGS_MODULE="myapp.settings"

opentelemetry-instrument python3 manage.py runserver --noreload
# or: opentelemetry-instrument gunicorn myapp.wsgi
```

---

### Python — Flask / Pyramid / Generic

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-distro
opentelemetry-bootstrap -a install
```

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

opentelemetry-instrument python app.py
```

Auto-instrumentation handles Flask, SQLAlchemy, requests, etc. automatically.

---

### Go — Gin

```bash
go get github.com/monoscope-tech/monoscope-go/gin
```

```go
import (
    monoscope "github.com/monoscope-tech/monoscope-go/gin"
)

func main() {
    // Call once at startup before creating the router:
    monoscope.ConfigureOpenTelemetry()

    router := gin.New()
    router.Use(monoscope.Middleware(monoscope.Config{
        ServiceName:         "my-service",
        // CaptureRequestBody:  true,
        // CaptureResponseBody: true,
        // RedactHeaders:       []string{"Authorization"},
        // RedactResponseBody:  []string{"$.password"},
    }))
    // ...
}
```

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
```

**Reporting errors / monitoring outgoing requests:**

```go
// Error reporting:
monoscope.ReportError(c.Request.Context(), err)

// Outgoing HTTP monitoring:
client := monoscope.HTTPClient(monoscope.WithRedactHeaders([]string{"Authorization"}))
resp, err := client.Get("https://api.example.com/data")
```

---

### Go — Echo / Chi / Fiber / Gorilla Mux / Native

Same env vars as Gin. Replace the import path:

```bash
go get github.com/monoscope-tech/monoscope-go/echo   # Echo
go get github.com/monoscope-tech/monoscope-go/chi    # Chi
go get github.com/monoscope-tech/monoscope-go/fiber  # Fiber
go get github.com/monoscope-tech/monoscope-go/mux    # Gorilla Mux
go get github.com/monoscope-tech/monoscope-go        # Native net/http
```

Setup pattern is identical: `monoscope.ConfigureOpenTelemetry()` then `router.Use(monoscope.Middleware(...))`.

---

### Java — Spring Boot

Add the Monoscope SDK to `pom.xml`:

```xml
<dependency>
  <groupId>io.monoscope.springboot</groupId>
  <artifactId>monoscope-springboot</artifactId>
  <version>2.0.9</version>
</dependency>
```

Download the OTel Java agent:

```bash
curl -L -O https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/latest/download/opentelemetry-javaagent.jar
```

Annotate the main class:

```java
import io.monoscope.springboot.annotations.EnableMonoscope;

@SpringBootApplication
@EnableMonoscope
public class DemoApplication { ... }
```

Configure in `src/main/resources/application.properties`:

```properties
monoscope.captureRequestBody=true
monoscope.captureResponseBody=true
monoscope.serviceName=my-service
# monoscope.redactHeaders=Authorization,X-Api-Key
# monoscope.redactRequestBody=$.password,$.creditCardNumber
# monoscope.redactResponseBody=$.password,$.creditCardNumber
```

Set env vars and run:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"

java -javaagent:./opentelemetry-javaagent.jar -jar target/app.jar
# or via Maven:
mvn spring-boot:run -Dspring-boot.run.jvmArguments="-javaagent:./opentelemetry-javaagent.jar"
```

---

### PHP — Laravel

Install the OTel PHP extension first:

```bash
pecl install opentelemetry
# Add to php.ini: extension=opentelemetry.so
```

```bash
composer require open-telemetry/sdk open-telemetry/exporter-otlp monoscope/laravel
```

Register the middleware in `app/Http/Kernel.php`:

```php
protected $middlewareGroups = [
    'api' => [
        \Monoscope\Http\Middleware\Monoscope::class,
    ],
];
```

Set env vars (note: HTTP/protobuf for PHP):

```bash
export OTEL_PHP_AUTOLOAD_ENABLED=true
export OTEL_SERVICE_NAME="my-service"
export OTEL_TRACES_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4318"
export OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
export OTEL_PROPAGATORS=baggage,tracecontext
# Optional:
# MONOSCOPE_CAPTURE_REQUEST_BODY=true
# MONOSCOPE_REDACT_HEADERS=Authorization,X-Api-Key
# MONOSCOPE_REDACT_REQUEST_BODY=$.password
```

---

### Ruby

```bash
gem install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation-all
```

```ruby
# config/initializers/opentelemetry.rb (Rails) or require at app startup
require 'opentelemetry/sdk'
require 'opentelemetry/exporter/otlp'
require 'opentelemetry/instrumentation/all'

OpenTelemetry::SDK.configure do |c|
  c.service_name = 'my-service'
  c.use_all
end
```

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otelcol.monoscope.tech:4317"
export OTEL_SERVICE_NAME="my-service"
export OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
export OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
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
let exporter = opentelemetry_otlp::new_exporter()
    .tonic()
    .with_endpoint("http://otelcol.monoscope.tech:4317");
let tracer = opentelemetry_otlp::new_pipeline()
    .tracing()
    .with_exporter(exporter)
    .install_batch(opentelemetry_sdk::runtime::Tokio)?;
```

Pass the API key via `OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"`.

---

### .NET / C#

```bash
dotnet add package OpenTelemetry
dotnet add package OpenTelemetry.Exporter.OpenTelemetryProtocol
dotnet add package OpenTelemetry.Extensions.Hosting
dotnet add package OpenTelemetry.Instrumentation.AspNetCore
```

```csharp
builder.Services.AddOpenTelemetry()
    .WithTracing(b => b
        .AddAspNetCoreInstrumentation()
        .AddOtlpExporter(o => {
            o.Endpoint = new Uri("http://otelcol.monoscope.tech:4317");
            o.Protocol = OtlpExportProtocol.Grpc;
        }));
```

Set env vars:

```bash
OTEL_SERVICE_NAME="my-service"
OTEL_RESOURCE_ATTRIBUTES="x-api-key={YOUR_API_KEY}"
```

---

## Step 3 — Verify data is flowing

**Quick smoke test with telemetrygen** (before deploying your app):

```bash
# Install telemetrygen
go install github.com/open-telemetry/opentelemetry-collector-contrib/cmd/telemetrygen@latest

# Send test traces
telemetrygen traces \
  --otlp-endpoint otelcol.monoscope.tech:4317 \
  --otlp-header "x-api-key={YOUR_API_KEY}" \
  --duration 5s
```

**Verify with the CLI after generating real traffic:**

```bash
# Should show events within ~30 seconds of startup
monoscope services list --since 5m
monoscope logs search "" --since 5m --limit 5
monoscope traces search "" --since 5m --limit 5
```

**Troubleshooting if no data appears after 1–2 minutes:**

1. Check `OTEL_EXPORTER_OTLP_ENDPOINT` — must be `http://otelcol.monoscope.tech:4317` (gRPC) or `:4318` (HTTP). No trailing slash.
2. Check `OTEL_RESOURCE_ATTRIBUTES` includes `x-api-key={YOUR_API_KEY}` — this is how auth works, not via headers.
3. Check `OTEL_EXPORTER_OTLP_PROTOCOL` is set (`grpc` for most, `http/protobuf` for PHP).
4. Enable OTel debug logging: `OTEL_LOG_LEVEL=debug` — exporter errors appear on stdout.
5. For Node.js: ensure `@opentelemetry/auto-instrumentations-node/register` is imported before the framework code.
6. For Python: use `opentelemetry-instrument` to launch the app, not plain `python`.

---

## Step 4 — Redacting sensitive data (optional)

All native SDKs support field-level redaction using JSONPath. Configure before going to production:

```bash
# Node.js env vars (or pass as config options to NewClient):
MONOSCOPE_REDACT_HEADERS="Authorization,X-Api-Key"
MONOSCOPE_REDACT_REQUEST_BODY="$.password,$.creditCardNumber"
MONOSCOPE_REDACT_RESPONSE_BODY="$.password,$.creditCardNumber"

# Python (Django):
MONOSCOPE_REDACT_HEADERS="Authorization"
MONOSCOPE_REDACT_REQUEST_BODY="$.password"
```

Redacted fields are zeroed out on your servers before leaving — they never reach Monoscope.

---

## Step 5 — Add custom spans and attributes (optional)

Once auto-instrumentation is working, add custom spans for business-critical paths:

```js
// Node.js
import { trace } from '@opentelemetry/api';
const tracer = trace.getTracer('my-service');
const span = tracer.startActiveSpan('process-payment', (span) => {
  span.setAttributes({ 'payment.amount': 99.99, 'payment.currency': 'USD' });
  // ... do work ...
  span.end();
});
```

```python
# Python
from opentelemetry import trace
tracer = trace.get_tracer("my-service")
with tracer.start_as_current_span("process-payment") as span:
    span.set_attribute("payment.amount", 99.99)
```

```go
// Go
tracer := otel.Tracer("my-service")
ctx, span := tracer.Start(ctx, "process-payment")
span.SetAttributes(attribute.Float64("payment.amount", 99.99))
defer span.End()
```

These attributes are searchable in Monoscope via KQL:

```
attributes.payment.currency == "USD" and severity.text == "error"
```

---

## Output

After completing instrumentation, confirm:

1. Which packages were installed and where the config lives
2. Which env vars need to be set (suggest adding them to `.env` / `.env.example`)
3. That `monoscope services list --since 5m` shows the service name
4. Any framework-specific notes (middleware registration, agent flags, etc.)
5. Which sensitive fields are configured for redaction (if any)
