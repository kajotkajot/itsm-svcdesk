---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: { fraction: 0.01, minutes: 432 }
    latency:
      objective: 0.95
      threshold_seconds: 0.14
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.14"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: { fraction: 0.05, minutes: 2160 }
  alerts:
    - {
        alert: KbSearchErrorsBurnFast,
        sli: availability,
        burn_rate: 14.4,
        long_window: 1h,
        short_window: 5m,
      }
    - {
        alert: KbSearchErrorsBurnSlow,
        sli: availability,
        burn_rate: 6,
        long_window: 6h,
        short_window: 30m,
      }
---

<!-- ai-generated: 100% - selected and documented the SLO from the measured kb-index profile and Lab 3 metric contract -->

# SLO for `GET /kb/search`

## Availability

The 30-day availability objective is 99% for successful and non-5xx responses. The local 60-second run returned 2,391 successful responses and 8 upstream 502 responses, about 99.67% availability. The 1% error budget is 432 minutes per 30 days. Because `kb-index` is an external dependency, its failures consume this budget even when svcdesk is otherwise healthy; the objective leaves room for occasional upstream errors but makes sustained failure visible.

## Latency

The latency SLI counts `/kb/search` responses completed within 140 ms. The objective is 95%, with a 5% budget (2,160 minutes in 30 days). The measured p50 was 32.4 ms, p95 57.8 ms, and p99 141.3 ms; the 140 ms threshold is near the measured p99, is a finite histogram boundary, and the observed share within it was approximately 98.8%. The threshold is measurable without bucket interpolation and achievable with margin over the 95% objective.

## Alerts

| alert                  | SLI          | burn rate | long / short window | budget spent when it fires | severity: page or chat |
| ---------------------- | ------------ | --------: | ------------------- | -------------------------- | ---------------------- |
| KbSearchErrorsBurnFast | availability |      14.4 | 1h / 5m             | 14.4% per hour             | P1 page                |
| KbSearchErrorsBurnSlow | availability |         6 | 6h / 30m            | 6% per hour                | P2 chat                |

The fast alert pages because a sustained 14.4x burn can exhaust a 30-day budget in roughly 50 hours, and users should not wait for a business-hours review during a rapid outage. The slow alert goes to chat: a persistent 6x burn still threatens the objective, but its longer window gives the team time to respond without waking someone for a brief upstream fluctuation. Both rules require their long and short windows to cross the threshold, so recovery in the short window clears the alert.

## Buckets

The 29-boundary ladder resolves the measured p99 of 141.3 ms in `(0.14, 0.16]`, a 20 ms bucket that is 14.2% of q. Across the full +/-10% band around q, the adjacent buckets are `(0.12, 0.14]` and `(0.14, 0.16]`; each is no wider than 20% of the band's lower edge. The remaining boundaries widen gradually to cover slow responses while retaining the 140 ms SLI threshold as an exact boundary.
