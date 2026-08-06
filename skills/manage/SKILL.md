---
name: manage
description: Create and manage alert monitors and dashboards as code using the monoscope CLI. Use when asked to set up an alert ("alert me when..."), create or edit a dashboard, add a widget, or keep monitors/dashboards in version control (GitOps). Requires MONOSCOPE_API_KEY and MONOSCOPE_PROJECT environment variables. For KQL query syntax, see the kql-reference skill.
allowed-tools: Bash, Read, Write, Edit
---

# Monoscope: Manage monitors & dashboards as code

Both resources follow the same as-code loop — **YAML is the user-facing
format** (JSON is accepted but YAML is preferred):

```bash
monoscope <resource> yaml <id> > thing.yaml   # dump the applyable shape
$EDITOR thing.yaml                            # edit
monoscope <resource> apply thing.yaml         # upsert (idempotent)
```

`apply` accepts a file or a directory of `.yaml`/`.yml`/`.json` files and is
**idempotent**: monitors upsert by `title`, dashboards by `file_path`.
Re-applying an unchanged dump is a no-op — safe to run from CI on every push.

## Prerequisites

```bash
export MONOSCOPE_API_KEY=<your-api-key>
export MONOSCOPE_PROJECT=<your-project-uuid>
```

## Monitors (alerts)

When the user says "alert me when X", write a monitor YAML and apply it.
The `query` is KQL (see kql-reference); the monitor fires when the query's
scalar value crosses `alert_threshold` (`trigger_less_than: true` inverts).

```yaml
# alert.yaml — minimal required fields
title: High error rate on checkout
query: 'resource.service.name == "checkout" and severity.text == "ERROR"'
alert_threshold: 10        # events per time window
trigger_less_than: false
check_interval_mins: 5
time_window_mins: 15
emails: []                 # notification targets
slack_channels: []
teams: []
```

Optional fields (all omittable): `severity` (`error` default), `subject`,
`message`, `warning_threshold`, `threshold_sustained_for_mins`,
`notify_after_mins`, `stop_after_count`, `email_all`, `visualization_type`,
`alert_recovery_threshold`, `warning_recovery_threshold`, `active`.

```bash
monoscope monitors apply alert.yaml      # create or update (keyed by title)
monoscope monitors apply monitors/       # apply a whole directory
monoscope monitors yaml <id>             # dump in exactly this shape
monoscope monitors list
monoscope monitors mute <id> --for 30    # triage ops — see the triage skill
monoscope monitors delete <id>
```

`monitors yaml` emits the applyable input shape (not the full API row), so
dump → apply round-trips cleanly.

## Dashboards

```yaml
# dash.yaml — create a dashboard shell, then manage widgets
title: Checkout overview
file_path: dashboards/checkout.yaml   # the apply natural key — always set it
```

```bash
monoscope dashboards create dash.yaml
monoscope dashboards yaml <id> > dash.yaml   # full dump incl. widget schema
monoscope dashboards apply dash.yaml         # upsert by file_path
monoscope dashboards widget upsert <id> widget.yaml
monoscope dashboards duplicate <id>
monoscope dashboards star <id>
monoscope dashboards delete <id>
```

The dashboard `schema` (widgets, layout) is large — prefer round-tripping the
`yaml` dump over writing it from scratch. Each widget's `query` is KQL.

**Verify a dashboard by rendering it, not by re-reading the YAML.**
`dashboards render` runs every widget's query server-side and returns the
results, which is the only way to find out that a widget you just wrote returns
nothing or fails:

```bash
# Anything broken after an apply
monoscope dashboards render <id> --since 1h \
  | jq -r '.widgets[] | select(.error) | "BROKEN \(.title): \(.error)"'

# Anything silently empty (query is valid but matches nothing)
monoscope dashboards render <id> --since 1h \
  | jq -r '.widgets[] | select((.rows | length) == 0 and (.text_rows | length) == 0) | .title'

# On a terminal, the same command draws the dashboard — useful to eyeball layout
monoscope dashboards render <id> --since 6h
```

## Guidelines

- Always set an explicit natural key: `title` for monitors, `file_path` for
  dashboards. Files without one create a new resource on each apply.
- Keep the YAML files in the user's repo (e.g. `observability/monitors/`) and
  apply from CI — that's the point of the as-code flow.
- Before creating a monitor, sanity-check the query returns data:
  `monoscope metrics query '<query> | summarize count()' --since 1h`
- Verify after apply: `monoscope monitors list` should show exactly one entry
  per title; duplicates mean the title drifted.
