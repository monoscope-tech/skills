---
name: kql-reference
description: Reference for Monoscope's KQL (Kusto Query Language) dialect used in log and trace search queries. Use when writing, explaining, or debugging KQL queries in monoscope — including the monoscope CLI search commands, the Log Explorer UI, and AI query generation. Covers operators, aggregations, time binning, string functions, and visualization types.
allowed-tools: Bash
---

# Monoscope KQL Reference

Monoscope uses a KQL (Kusto Query Language) dialect for filtering and aggregating logs, traces, and spans. This is the same syntax used by `monoscope logs search`, `monoscope events search`, `monoscope traces search`, and the Log Explorer UI.

## Operators

### Comparison
```
==   !=   >   <   >=   <=
```

### Set operations
```
in      !in
```
```
level in ("ERROR", "FATAL")
attributes.http.request.method !in ("GET", "HEAD")
```

### Text search
```
has       — case-insensitive whole-word match
!has      — negated
has_any   — matches any word from a list
has_all   — matches all words from a list
```
```
body has "timeout"
attributes.exception.message has_any ["timeout", "connection", "network"]
```

### String operations
```
contains      !contains      — substring match
startswith    !startswith    — prefix match
endswith      !endswith      — suffix match
matches  =~                  — regex match
```
```
attributes.url.path startswith "/api/"
attributes.user.email endswith "@company.com"
name contains "database"
attributes.user.email matches /.*@corp\.com/
```

### Logical
```
AND   OR   (also lowercase: and, or)
```
Parentheses for grouping:
```
(level == "ERROR" OR duration > 5s) AND resource.service.name != null
```

### Null checks
```
field != null    — field exists and has a value
field == null    — field is absent or null
```

## Duration values

Durations are written as a number followed by a unit. They represent nanoseconds internally.

| Unit | Suffix | Example |
|------|--------|---------|
| Nanoseconds | ns | `100ns` |
| Microseconds | us | `500us` |
| Milliseconds | ms | `200ms` |
| Seconds | s | `5s` |
| Minutes | m | `2m` |
| Hours | h | `1h` |
| Days | d | `7d` |

```
duration > 1s               — spans taking longer than 1 second
duration > 500ms            — slower than 500ms
duration > 5s AND kind == "span"
```

## Aggregations (summarize)

Pipe a filter into a `summarize` clause for aggregation:

```
<filter> | summarize <agg>() by <grouping>
```

### Aggregation functions

| Function | Description |
|---|---|
| `count()` | Total count |
| `countif(expr)` | Count where expr is true |
| `dcount(field)` | Distinct count |
| `sum(field)` | Sum |
| `avg(field)` | Average |
| `min(field)` | Minimum |
| `max(field)` | Maximum |
| `median(field)` | Median |
| `stdev(field)` | Standard deviation |
| `percentile(field, N)` | Nth percentile (e.g., p99 = `percentile(duration, 99)`) |
| `percentiles(field, p1, p2, ...)` | Multiple percentiles at once |
| `range(field)` | max − min (gauges only, never counters) |
| `rate(value)` | Counter increase per second, per series (`metrics` only) |
| `increase(value)` | Counter increase per bin, per series (`metrics` only) |
| `last(value)` | Newest value per bin, per series (`metrics` only) |
| `rateif(value, pred)`, `increaseif(value, pred)`, `lastif(value, pred)` | The same, over only the series `pred` matches (`metrics` only) |

### Examples

```
level == "ERROR" | summarize count() by resource.service.name
| summarize avg(duration) by resource.service.name
| summarize percentile(duration, 99) by bin_auto(timestamp)
| summarize count(), avg(duration) by resource.service.name
```

## Time binning

Use `bin_auto(timestamp)` by default — the system picks the interval automatically based on the selected time range:

```
level == "ERROR" | summarize count() by bin_auto(timestamp)
```

Use `bin(timestamp, interval)` only when the user explicitly specifies an interval:

```
| summarize count() by bin(timestamp, 1h)    — "show by hour"
| summarize count() by bin(timestamp, 30s)   — "per 30 seconds"
| summarize count() by bin(timestamp, 5m)    — "in 5 minute buckets"
```

**For categorical grouping (by service, method, status, etc.) — do NOT use `bin()`:**

```
| summarize count() by resource.service.name          ✓ distribution
| summarize count() by bin_auto(timestamp)             ✓ timeseries
| summarize count() by resource.service.name, bin_auto(timestamp)  ✓ both
```

## Scalar functions

```
coalesce(field1, field2, ...)    — first non-null value
strcat(a, b, ...)                — string concatenation
iff(condition, then, else)       — conditional
toint(field)                     — cast to integer
tofloat(field)                   — cast to float
tostring(field)                  — cast to string
tobool(field)                    — cast to boolean
isnull(field)                    — true if null
isnotnull(field)                 — true if not null
isempty(field)                   — true if null or empty string
isnotempty(field)                — true if not null and not empty
```

## Field paths

Fields use dot notation. Array indexing is supported:

```
attributes.http.response.status_code
resource.service.name
context.trace_id
attributes.exception.message
body.message[0].tags
request_body.items[*].id
```

## Core fields (schema reference)

| Field | Type | Notes |
|---|---|---|
| `timestamp` | string | When the event occurred |
| `duration` | duration | Span duration in nanoseconds |
| `level` | string | `TRACE` `DEBUG` `INFO` `WARN` `ERROR` `FATAL` |
| `kind` | string | `logs` `span` `request` |
| `status_code` | string | `OK` `ERROR` `UNSET` |
| `name` | string | Span or operation name |
| `body` | object | Log body content |
| `parent_id` | string | Parent span ID (null for root spans) |
| `context.trace_id` | string | Trace correlation ID |
| `context.span_id` | string | Span ID |
| `resource.service.name` | string | Service name |
| `resource.service.version` | string | Service version |
| `attributes.http.request.method` | string | `GET` `POST` `PUT` `DELETE` … |
| `attributes.http.response.status_code` | number | HTTP status (200, 404, 500 …) |
| `attributes.url.path` | string | URL path |
| `attributes.url.full` | string | Full URL |
| `attributes.exception.type` | string | Exception class name |
| `attributes.exception.message` | string | Exception message |
| `attributes.exception.stacktrace` | string | Stack trace |
| `attributes.error.type` | string | Error type |
| `attributes.db.system.name` | string | `postgresql` `mysql` … |
| `attributes.db.operation.name` | string | `SELECT` `INSERT` … |
| `attributes.db.query.text` | string | Raw query text |
| `attributes.user.id` | string | User ID |
| `attributes.user.email` | string | User email |
| `attributes.session.id` | string | Session ID |
| `severity.text` | string | `TRACE` `DEBUG` `INFO` `WARN` `ERROR` `FATAL` |

Use `monoscope schema` to discover the full field list for your project.

## Example queries

```
# All errors
level == "ERROR"

# HTTP 5xx errors
attributes.http.response.status_code >= 500

# Slow spans
duration > 1s AND kind == "span"

# Errors in a specific service
level == "ERROR" AND resource.service.name == "checkout-api"

# Errors over time (timeseries chart)
level == "ERROR" | summarize count() by bin_auto(timestamp)

# Request count by service (distribution chart)
| summarize count() by resource.service.name

# p99 latency by service
| summarize percentile(duration, 99) by resource.service.name

# Network-related exceptions
attributes.exception.message has_any ["timeout", "connection", "network"]

# Successful POST requests
attributes.http.request.method == "POST" AND attributes.http.response.status_code < 400

# Database queries taking over 200ms
attributes.db.operation.name != null AND duration > 200ms

# Auth service excluding debug noise
resource.service.name startswith "auth" AND level !in ("DEBUG", "TRACE")

# Root spans only (no parent)
kind == "span" AND parent_id == null

# Errors or slow requests from named services
(level == "ERROR" OR duration > 5s) AND resource.service.name != null
```

## Important constraints

- **Do not invent field names.** Only use fields from the schema. Use `monoscope schema` to discover available fields.
- **Do not filter by timestamp in KQL.** Time range is controlled separately via `--since`, `--from`, `--to` flags on the CLI, or the time picker in the UI.
- **`has` is for word search**, `contains` is for substring. `has "error"` won't match `"errors"` but `contains "error"` will.
- **Duration fields** (`duration`) compare in nanoseconds but accept human-readable suffixes (`1s`, `200ms`).

## Metrics queries

`monoscope metrics query EXPRESSION` and `metrics chart EXPRESSION` accept
**this same KQL dialect** — a filter piped into `summarize`. There is no
separate metrics language and no predefined metric names like `error_rate`.

- `summarize` with **no** `by` clause → a single scalar; this is the shape
  `--assert` evaluates (`--assert "> 0"`, exit code gates CI).
- `summarize ... by bin_auto(timestamp)` → a timeseries (what `chart` plots).
- `summarize ... by <field>` → a per-category distribution.
- `by bin_auto(timestamp), a, b` → one series per (a, b) combination, labelled `a / b`.

### Counters and gauges on the `metrics` source

Raw OpenTelemetry/Prometheus metrics live in the `metrics` source (start the
query with `metrics |`, or pass `--source metrics`). Every point belongs to a
**series**: a metric name plus one exact set of attributes (`series_id`).

| Metric kind | Use | Never |
|---|---|---|
| Counter (cumulative or delta: `*_total`, requests, bytes sent, rows ingested) | `rate(value)` per second, `rate(value) * 60` per minute, `increase(value)` per bin | `sum(value)`, `range(value)`, `avg(value)` |
| Gauge (memory in use, queue depth, connections, buffer size) | `last(value)` (current level), `avg(value)`, `max(value)` | `rate()`, `increase()` |

`rate()`/`increase()` take each series' increase from its previous point (also
from before the time range, so a bin with one point is still right), treat a
drop as a counter reset (restart), and add the series together per `by` group.
`range(value)` per bin is 0 when a bin holds one point and wrong across a
restart. `last()` sums the newest point of each series in the group; group `by`
the series' attributes to see one line per series.

```bash
# Rows ingested per second
monoscope chart 'metrics | where metric_name == "timefusion.mem_buffer.rows_ingested_total" | summarize rate(value) by bin_auto(timestamp)' --source metrics
# Two counters as two lines
monoscope chart 'metrics | where metric_name in ("timefusion.mem_buffer.rows_ingested_total", "timefusion.mem_buffer.rows_flushed_total") | summarize rate(value) by bin_auto(timestamp), metric_name' --source metrics
# One line per (project, table)
monoscope chart 'metrics | where metric_name == "timefusion.ingest.rows" | summarize rate(value) by bin_auto(timestamp), attributes.project_id, attributes.table_name' --source metrics
# Total increase over the window (scalar, works with --assert)
monoscope metrics query 'metrics | where metric_name == "jobs.failed" | summarize increase(value)' --since 1h --assert "< 10"
# A gauge's current value
monoscope chart 'metrics | where metric_name == "timefusion.mem_buffer.estimated_bytes" | summarize last(value) by bin_auto(timestamp)' --source metrics
```

**Ratios.** `rateif(value, pred)`, `increaseif(value, pred)` and
`lastif(value, pred)` add up only the series that `pred` matches. Each series
still takes its increase from its own points, so two of them can divide each
other. Write `pred` on series columns (`metric_name`, `attributes.*`,
`resource.*`), never on `value` or `timestamp`, and keep the `where` wide enough
to read every series the aggregates use. Divide in one expression, or name the
aggregates and divide in an `extend` after the `summarize` (the computed column
is the charted series). A division by 0 gives 0.

```bash
# Rollup hit rate in percent
monoscope chart 'metrics | where metric_name in ("timefusion.rollup.hits", "timefusion.rollup.misses") | summarize hits = rateif(value, metric_name == "timefusion.rollup.hits"), total = rate(value) by bin_auto(timestamp) | extend hit_pct = 100.0 * hits / total' --source metrics
# Memory peak as a percent of the limit (two gauges)
monoscope chart 'metrics | where metric_name in ("timefusion.memory.charged_peak_bytes", "timefusion.memory.limit_bytes") | summarize 100.0 * lastif(value, metric_name == "timefusion.memory.charged_peak_bytes") / lastif(value, metric_name == "timefusion.memory.limit_bytes") by bin_auto(timestamp)' --source metrics
# Share of one attribute value
monoscope chart 'metrics | where metric_name == "timefusion.rollup.hits" | summarize 100.0 * rateif(value, attributes.mode == "hybrid") / rate(value) by bin_auto(timestamp)' --source metrics
```

A monitor alerts on the largest of all aggregates, so write a ratio monitor as
the only aggregate (the one-expression form).

Dashboard `timeseries_stat` tiles reduce the bins to one number with
`summarize_by`: `sum` for `increase()`, `mean`/`max` for `rate()`, `last` for
`last()` gauges. Do not combine `rate()` with `summarize_by: rate` (it divides
by the window again).

```bash
monoscope metrics query 'severity.text == "ERROR" | summarize count()' --since 1h --assert "< 100"

# `chart` draws the result. On a terminal that is a real plot; piped, it is the
# same JSON `metrics query` returns, so it is safe to use either way.
monoscope chart '| summarize count() by bin_auto(timestamp)' --since 2h
monoscope chart '| summarize count() by resource.service.name' --type bar
monoscope chart '| summarize p95(duration)' --type stat --since 24h
```

The shape of the result decides the chart: a leading `bin_auto(timestamp)`
column plots as a line, `by <field>` as bars, a bare `summarize` as a single
number. `--type line|bar|stat|table` overrides the guess.

## CLI usage

The `monoscope` CLI accepts KQL as the positional `QUERY` argument and adds
two convenience shorthands that compose with the query via `and`:

| Flag | Expands to |
|---|---|
| `--service <name>` | `resource.service.name == "<name>"` |
| `--level <level>` | `severity.text == "<level>"` |
| `--kind log\|trace\|span` | sets the wire `source` (`trace` is a CLI alias for `span`) |

```bash
# Basic search
monoscope logs search 'level == "ERROR"' --since 1h

# Shorthand equivalent
monoscope logs search "" --since 1h --level error

# Service shorthand composes with the positional query
monoscope logs search 'duration > 1s' --service payment-api

# Aggregation query
monoscope logs search 'level == "ERROR" | summarize count() by resource.service.name'

# Schema discovery — the CLI exposes --search/--limit so agents don't load the
# full schema (~600 fields) into context unnecessarily.
monoscope schema --search service --limit 20
monoscope schema --json | jq '.fields | keys[]'

# Value discovery — what services/levels/methods *actually exist*?
# Faster than running summarize: facets are precomputed per project.
monoscope facets resource.service.name --top 10
monoscope facets severity.text
monoscope facets   # all faceted fields at once

# Pagination chain
monoscope events search "" --since 1h --limit 100 --first --id-only
# → bare event id, suitable as the next argument to `events get`
```

**Wire-level rule — KQL uses `==` and `!=`.** The CLI used to emit Lucene-style
`field:value`, which the server rejected with HTTP 400. If you see
`error: HTTP 400` from a query that "looks right", check the operator.

**Errors are forwarded.** The server's KQL parser includes line/column markers
on parse errors and the CLI surfaces those directly — you don't need to pry
into stderr for a hint.
