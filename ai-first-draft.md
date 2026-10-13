---
lab3_first_draft:
  source: ai
  tool: "GitHub Copilot (model not exposed), 13 October 2026"
  ladder:
    [
      0.005,
      0.01,
      0.02,
      0.04,
      0.06,
      0.08,
      0.10,
      0.12,
      0.14,
      0.16,
      0.18,
      0.20,
      0.21,
      0.22,
      0.23,
      0.24,
      0.25,
      0.27,
      0.30,
      0.35,
      0.4,
      0.5,
      0.75,
      1,
      1.5,
      2,
      3,
      5,
      10,
    ]
  verdict: confirmed
  evidence: { p99_seconds: 0.1413, bucket: [0.14, 0.16], relative_width: 0.142 }
lab3_flawed_ladder:
  verdict: refuted # the only admissible verdict (M-27); the evidence is yours to compute
  evidence: { p99_seconds: 0.1413, bucket: [0.04, 0.5], relative_width: 3.255 }
---

<!-- ai-generated: 100% - recorded this assistant exchange before measuring the service or designing its histogram -->

# The assistant's first draft, and two verdicts

The measured q was 0.1413 s. The draft ladder places it in (0.14, 0.16], whose 0.02 s width is 14.2% of q; it therefore resolves the measured value. At 0.95q and 1.05q, the containing buckets are (0.12, 0.14] and (0.14, 0.16], both also within the 20% limit. The instructor ladder places q in (0.04, 0.5], with width 0.46 / 0.1413 = 3.255, so it does not resolve it.

## Prompt

Suggest histogram bucket boundaries in seconds and a Prometheus alert policy for `GET /kb/search` in a service that forwards requests to a variable-latency, sometimes-failing upstream. Give a strictly increasing ladder of no more than 30 positive finite boundaries, with extra resolution around likely sub-second request latencies but coverage for slower requests too. Do not claim to know this service's measured latency. Give an actionable multiwindow, multi-burn-rate availability policy with distinct fast- and slow-burn rules, stating the assumed objective, burn rates, windows, labels, and threshold expressions. Explain briefly why the ladder and alerts are reasonable starting hypotheses that must be checked against measurements and the service's SLO.

## Answer

Proposed histogram boundaries, in seconds:

`[0.005, 0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.21, 0.22, 0.23, 0.24, 0.25, 0.27, 0.30, 0.35, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 5, 10]`

This is a 29-boundary starting ladder. It has finer spacing around 0.2 seconds, where many API requests may fall, and wider spacing at higher latencies so the ladder still covers slow responses without exceeding 30 finite boundaries. No measured p99 is available yet, so this is a hypothesis, not a claim that the ladder resolves the actual p99. After measuring, check the bucket containing p99 and its relative width; adjust the production ladder if needed.

Example alert assumptions: availability objective 99%, a fast-burn rate of 14.4 over one hour and five minutes, and a slow-burn rate of 6 over six hours and 30 minutes. Each rule requires both its long and short window to cross its threshold: `14.4 * (1 - 0.99) = 0.144` for fast burn, and `6 * (1 - 0.99) = 0.06` for slow burn. The fast alert is P1; the slow alert is P2.

- Fast rule `KbSearchErrorsBurnFast`: the 5xx rate divided by all `/kb/search` requests over `[1h]` must exceed `14.4 * (1 - 0.99)`, and the same ratio over `[5m]` must also exceed it. Use `for: 2m` and labels `service=svcdesk`, `slo=availability`, `severity=P1`; investigate the upstream and recent changes.
- Slow rule `KbSearchErrorsBurnSlow`: the same error ratio over `[6h]` and `[30m]` must both exceed `6 * (1 - 0.99)`. Use `for: 5m` and labels `service=svcdesk`, `slo=availability`, `severity=P2`; investigate sustained burn before the budget is exhausted.

The ladder and alert are starting hypotheses only. Use measured latency to assess bucket resolution, and set the final objective and alert thresholds from the agreed SLO and observed failure behavior.

## Verdict on the draft ladder

The measured p99 is 0.1413 s. The draft bucket is (0.14, 0.16], so its relative width is (0.16 - 0.14) / 0.1413 = 0.142; `histogram_quantile` interpolates within a narrow bucket here. The verdict is confirmed because this width is below 0.20q.

## The draft alert rule

The first draft proposed fast and slow multiwindow availability burns. Both remain in `prometheus/alerts.yml`, with the 99% availability objective used for their constant thresholds; I kept a separate 95% latency objective in the SLO.

## Verdict on the instructor's flawed ladder

For the instructor ladder, q is in (0.04, 0.5], giving (0.5 - 0.04) / 0.1413 = 3.255. Its many fine boundaries are spent below 40 ms, while the measured 141.3 ms p99 falls in an extremely coarse bucket, so the verdict is refuted.
