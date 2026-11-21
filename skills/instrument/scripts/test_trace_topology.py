import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location("topology", pathlib.Path(__file__).with_name("assert-trace-topology.py"))
topology = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topology)


def span(name, identity, parent="", trace="a" * 32, kind="consumer", sql=False):
    return topology.normalize({"name": name, "span_id": identity * 16, "trace_id": trace,
                               "parent_id": parent * 16, "kind": kind,
                               "attributes": {"db.system": "postgresql"} if sql else {}})


class TopologyTests(unittest.TestCase):
    def test_nested_job_sql(self):
        spans = [span("run", "1"), span("item", "2", "1"), span("sql", "3", "2", kind="client", sql=True)]
        self.assertEqual([], topology.validate(spans, ["run", "item"], require_sql=True))

    def test_job_exists_but_sql_is_orphan(self):
        errors = topology.validate([span("run", "1"), span("sql", "2", kind="client", sql=True)], ["run"], require_sql=True)
        self.assertTrue(any("orphan" in error for error in errors))
        self.assertTrue(any("no SQL descendant" in error for error in errors))

    def test_cross_trace_parent(self):
        spans = [span("run", "1"), span("sql", "2", "1", trace="b" * 32, kind="client", sql=True)]
        self.assertTrue(any("cross-trace" in error for error in topology.validate(spans, ["run"])))

    def test_missing_intermediate_span(self):
        spans = [span("run", "1"), span("sql", "3", "2", kind="client", sql=True)]
        self.assertTrue(topology.validate(spans, ["run"]))

    def test_fixture_does_not_satisfy_job_sql(self):
        spans = [span("fixture", "1", kind="internal"), span("run", "2", "1"), span("sql", "3", "1", kind="client", sql=True)]
        self.assertTrue(topology.validate(spans, ["run"], ["fixture"], require_sql=True))

    def test_cycle(self):
        spans = [span("run", "1", "2"), span("sql", "2", "1", kind="client", sql=True)]
        self.assertTrue(any("cyclic" in error for error in topology.validate(spans, ["run"])))

    def test_empty_capture_fails(self):
        self.assertTrue(topology.validate([], ["run"]))

    def test_monoscopes_nested_attributes_and_context(self):
        value = {"name": "sql", "kind": "client", "context": {"trace_id": "a" * 32, "span_id": "2" * 16},
                 "parent_id": "1" * 16, "attributes": {"db": {"system": {"name": "postgresql"}, "query": {"text": "SELECT 1"}}}}
        spans = [span("run", "1")] + topology.json_spans(value)
        self.assertEqual([], topology.validate(spans, ["run"], require_sql=True))

    def test_collector_debug_parser(self):
        text = """ScopeSpans #0
InstrumentationScope app
Span #0
    Trace ID       : aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    Parent ID      :
    ID             : 1111111111111111
    Name           : run
    Kind           : Consumer
ScopeSpans #1
InstrumentationScope github.com/XSAM/otelsql 0.44.0
Span #0
    Trace ID       : aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    Parent ID      : 1111111111111111
    ID             : 2222222222222222
    Name           : sql.conn.query
    Kind           : Client
     -> db.system: Str(postgresql)
"""
        self.assertEqual([], topology.validate(topology.debug_spans(text), ["run"], require_sql=True))

    def test_otlp_json_and_zero_parent(self):
        value = {"resourceSpans": [{"scopeSpans": [{"scope": {"name": "app"}, "spans": [
            {"name": "run", "traceId": "a" * 32, "spanId": "1" * 16, "parentSpanId": "0" * 16, "kind": 5},
            {"name": "sql", "traceId": "a" * 32, "spanId": "2" * 16, "parentSpanId": "1" * 16, "kind": 3,
             "attributes": [{"key": "db.statement", "value": {"stringValue": "SELECT 1"}}]},
        ]}]}]}
        self.assertEqual([], topology.validate(topology.json_spans(value), ["run"], require_sql=True))

    def test_http_client_must_have_job_parent(self):
        client = span("HTTP POST", "2", kind="client")
        client["attributes"] = {"http.request.method": "POST"}
        self.assertTrue(topology.validate([span("run", "1"), client], ["run"]))
        client["parent_id"] = "1" * 16
        self.assertEqual([], topology.validate([span("run", "1"), client], ["run"]))

    def test_debug_metrics_and_logs_cannot_overwrite_span_identity(self):
        text = """ScopeSpans #0
InstrumentationScope github.com/XSAM/otelsql
Span #0
    Trace ID       : aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    Parent ID      : 1111111111111111
    ID             : 2222222222222222
    Name           : sql.conn.query
    Kind           : Client
ResourceMetrics #0
    Name           : metric.name
ResourceLogs #0
LogRecord #0
Trace ID: 00000000000000000000000000000000
"""
        parsed = topology.debug_spans(text)
        self.assertEqual(1, len(parsed))
        self.assertEqual("sql.conn.query", parsed[0]["name"])
        self.assertEqual("a" * 32, parsed[0]["trace_id"])


if __name__ == "__main__":
    unittest.main()
