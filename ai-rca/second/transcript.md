# Independent investigation transcript

Investigator: GitHub Copilot
Model: GitHub Copilot
Data source: assigned Lab 4 snapshot served read-only by Prometheus 3.15.0 at http://localhost:19090.

## Question

The recorded checkout page began at 2026-10-12T07:09:19Z. Inspect the incident window and compare symptoms with the healthy baseline at 2026-10-12T07:00:45Z. Which service-level claims are supported?

## Investigation

The comparison instant is 2026-10-12T07:11:45Z, after the fault has been active for more than five minutes. I evaluated each expression as an instant query at both the incident instant and the baseline instant.

### Hypothesis H1

Product-catalog server-side GetProduct failures increased sharply during the incident and explain a material share of checkout failures.

Query:

```promql
sum(rate(traces_span_metrics_calls_total{service_name="product-catalog", span_kind="SPAN_KIND_SERVER", status_code="STATUS_CODE_ERROR"}[5m])) > 0.05
```

Result: at 07:11:45Z the query returned 0.09583333333333333 calls/s. At 07:00:45Z it returned no series.

### Hypothesis H2

Ad server p99 latency rose from baseline to 796 ms during the fault, consistent with a latency fault affecting the ad service.

Query:

```promql
histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="ad", span_kind="SPAN_KIND_SERVER"}[5m]))) > 500
```

Result: at 07:11:45Z the query returned 796 ms. At 07:00:45Z it returned no series.

### Hypothesis H3

Recommendation server p99 latency also rose above 7 ms during the incident, indicating a second service-level latency symptom.

Query:

```promql
histogram_quantile(0.99, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="recommendation", span_kind="SPAN_KIND_SERVER"}[5m]))) > 7
```

Result: at 07:11:45Z the query returned 7.260000000000003 ms. At 07:00:45Z it returned no series.

### Hypothesis H4

Payment server errors caused the checkout incident.

Query:

```promql
sum(rate(traces_span_metrics_calls_total{service_name="payment", span_kind="SPAN_KIND_SERVER", status_code="STATUS_CODE_ERROR"}[5m])) > 0
```

Result: the query returned no series at 07:11:45Z and at the healthy baseline. The snapshot instead shows product-catalog server errors and elevated ad and recommendation latency.

## Conclusion

The snapshot supports the first three symptom hypotheses and contradicts the payment-error claim. These PromQL checks establish service symptoms, not the sealed feature-flag identities; flag attribution remains an inference from the fault pool and its documented service impact map.
