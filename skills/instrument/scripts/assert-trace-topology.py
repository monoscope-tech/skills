#!/usr/bin/env python3
"""Assert job ownership of downstream spans; never print payloads or resource keys."""
import argparse
import base64
import json
import re
import sys


def identity(value):
    value = str(value or "").strip()
    if re.fullmatch(r"[0-9a-fA-F]{16}|[0-9a-fA-F]{32}", value):
        value = value.lower()
    elif value:
        try:
            decoded = base64.b64decode(value, validate=True)
            if len(decoded) in (8, 16):
                value = decoded.hex()
        except ValueError:
            pass
    return "" if not value or set(value) == {"0"} else value


def flatten(value, prefix=""):
    result = {}
    if isinstance(value, list):  # OTLP KeyValue array
        for item in value:
            if isinstance(item, dict) and "key" in item:
                result[item["key"]] = item.get("value")
    elif isinstance(value, dict):
        for key, item in value.items():
            path = prefix + key
            if isinstance(item, dict):
                result.update(flatten(item, path + "."))
            else:
                result[path] = item
    return result


def normalize(span, scope=""):
    context = span.get("context") or {}
    return {
        "name": span.get("name", span.get("span_name", "")),
        "trace_id": identity(span.get("trace_id", span.get("traceId", context.get("trace_id")))),
        "span_id": identity(span.get("span_id", span.get("spanId", context.get("span_id")))),
        "parent_id": identity(span.get("parent_id", span.get("parentSpanId", span.get("parent_span_id")))),
        "kind": {2: "server", 3: "client", 4: "producer", 5: "consumer"}.get(span.get("kind"), str(span.get("kind", "")).lower()),
        "scope": span.get("scope", scope),
        "attributes": flatten(span.get("attributes", {})),
    }


def json_spans(value, scope=""):
    if isinstance(value, list):
        return [span for item in value for span in json_spans(item, scope)]
    if not isinstance(value, dict):
        return []
    if "traceId" in value or "trace_id" in value or ("context" in value and "name" in value):
        return [normalize(value, scope)] + json_spans(value.get("children", []), scope)
    scope = (value.get("scope") or {}).get("name", scope) if isinstance(value.get("scope"), dict) else scope
    result = []
    for key in ("resourceSpans", "scopeSpans", "spans", "events", "children"):
        if key in value:
            result.extend(json_spans(value[key], scope))
    return result


def debug_spans(text):
    result, current, scope = [], None, ""
    fields = {"Trace ID": "trace_id", "ID": "span_id", "Parent ID": "parent_id", "Name": "name", "Kind": "kind", "Span Kind": "kind"}
    for line in text.splitlines():
        if re.search(r"(?:ResourceSpans|ScopeSpans|Span|ResourceMetrics|ScopeMetrics|ResourceLogs|ScopeLogs|LogRecord) #\d+", line):
            if current is not None:
                result.append(normalize(current))
            current = {"scope": scope, "attributes": {}} if line.startswith("Span #") else None
        match = re.match(r"^InstrumentationScope\s+(\S+)", line)
        if match:
            scope = match.group(1)
        if current is None:
            continue
        match = re.match(r"^\s*(Trace ID|Parent ID|ID|Name|Span Kind|Kind)\s*:\s*(.*)$", line)
        if match:
            current[fields[match.group(1)]] = match.group(2).strip()
        match = re.match(r"^\s*->\s+(\S+):\s+", line)
        if match:
            current["attributes"][match.group(1)] = True
    if current is not None:
        result.append(normalize(current))
    return result


def validate(spans, jobs=(), allow_roots=(), require_sql=False):
    errors, index, owned_sql = [], {}, set()
    for span in spans:
        key = (span["trace_id"], span["span_id"])
        if not all(key):
            errors.append("span missing trace/span identity: " + span["name"])
        if key in index:
            errors.append("duplicate span identity: " + span["name"])
        index[key] = span
    seen_jobs = {span["name"] for span in spans}
    for job in jobs:
        if job not in seen_jobs:
            errors.append("missing job: " + job)
    downstream_count = 0
    for span in spans:
        sql = "otelsql" in span["scope"] or any(key.startswith("db.") for key in span["attributes"])
        http = span["kind"] == "client" and any(key.startswith("http.") for key in span["attributes"])
        if not (sql or http):
            continue
        downstream_count += 1
        parent, visited, boundary = span["parent_id"], set(), False
        if not parent:
            errors.append("orphan downstream span: " + span["name"])
        while parent:
            key = (span["trace_id"], parent)
            if key in visited:
                errors.append("cyclic parent chain: " + span["name"])
                break
            visited.add(key)
            ancestor = index.get(key)
            if ancestor is None:
                errors.append("missing or cross-trace parent: " + span["name"])
                break
            if ancestor["name"] in jobs or ancestor["name"] in allow_roots or ancestor["kind"] in ("server", "consumer"):
                boundary = True
            if sql and ancestor["name"] in jobs:
                owned_sql.add(ancestor["name"])
            parent = ancestor["parent_id"]
        if span["parent_id"] and not boundary:
            errors.append("downstream span has no job/server/explicit fixture ancestor: " + span["name"])
    if not downstream_count:
        errors.append("no downstream spans captured")
    if require_sql:
        errors.extend("job has no SQL descendant: " + job for job in jobs if job not in owned_sql)
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="collector debug log or complete span JSON; - for stdin")
    parser.add_argument("--job", action="append", default=[])
    parser.add_argument("--allow-root", action="append", default=[], help="explicit fixture ancestor name; never allows root SQL")
    parser.add_argument("--require-sql", action="store_true")
    args = parser.parse_args()
    text = sys.stdin.read() if args.file == "-" else open(args.file, encoding="utf-8").read()
    spans = json_spans(json.loads(text)) if text.lstrip().startswith(("{", "[")) else debug_spans(text)
    errors = validate(spans, args.job, args.allow_root, args.require_sql)
    for error in errors[:20]:
        print("FAIL " + error)
    print(f"{'FAIL' if errors else 'PASS'} topology: {len(spans)} spans, {len(args.job)} expected jobs, {len(errors)} violations")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
