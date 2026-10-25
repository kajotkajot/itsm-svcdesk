---
lab4_postmortem:
  ticket: "1224ad8d-06a8-4ae3-865a-da2015a4ddb5"
  detecting_alert: ShopCheckoutErrors
  onset: 2026-10-12T07:05:45Z
  detection: 2026-10-12T07:09:19Z
  acknowledgement: 2026-10-12T07:10:07Z
  recovery: 2026-10-12T07:12:19Z
  mttd_seconds: 214
  mtta_seconds: 48
  mttr_seconds: 394
  identified_flags:
    [productCatalogFailure, adManualGc, recommendationCacheFailure]
---

<!-- ai-generated: 40% - drafted from the supplied recording and Prometheus snapshot evidence. -->

# Postmortem: Checkout errors during the seeded feature-flag fault

## Date

The incident occurred on 12 October 2026; this postmortem was prepared on 25 October 2026 from the assigned recording.

## Authors

Written by the on-call engineer responsible for the checkout incident and its follow-up actions.

## Status

The recorded incident is recovered; the proposed prevention and alerting actions remain open for review.

## Summary

A seeded feature-flag fault caused checkout errors and slower ad responses. The detecting alert fired 214 seconds after onset, and its first firing run recovered 394 seconds after onset.

## Impact

At 07:09:19Z, product-catalog server errors were 0.104 calls per second and checkout PlaceOrder errors were 0.0067 per second. The ad server p99 rose from about 5 ms on baseline to about 908 ms during the fault; these are span-metric values in milliseconds.

## Root Causes

The metrics support productCatalogFailure through product-catalog GetProduct errors, adManualGc through the ad latency spike, and recommendationCacheFailure through rising recommendation latency. The sealed recording is the source of ground truth; these flag names are the incident investigation's identification, not labels exposed by the telemetry.

## Trigger

The injector's recorded fault began at 07:05:45Z after the healthy baseline. The available snapshot establishes the onset but does not expose the sealed flag variants.

## Resolution

The recorded ShopCheckoutErrors alert recovered at 07:12:19Z after the fault was mitigated. The supplied snapshot has no per-flag toggle timestamps, so it cannot establish a reliable order or exact instant for each individual flag change.

## Detection

ShopCheckoutErrors detected the first qualifying symptom run at 07:09:19Z, 214 seconds after onset. The P1 ticket was acknowledged at 07:10:07Z, 48 seconds after detection.

## Action Items

| Action Item                                                                          | Type    | Owner         | Bug        |
| ------------------------------------------------------------------------------------ | ------- | ------------- | ---------- |
| Add a product-catalog error-rate alert and validate it against a healthy baseline.   | prevent | Service owner | LAB4-REC-1 |
| Add a runbook check for ad and recommendation latency during feature-flag rollbacks. | process | On-call lead  | LAB4-REC-2 |

## Lessons Learned

### What went well

The checkout alert detected the incident and the P1 ticket was acknowledged shortly after the page.

### What went wrong

The transcript's initial investigation did not distinguish client-side dependencies from server-side causes or verify the payment hypothesis.

### Where we got lucky

The recording preserved a single fault run, its full recovery, and enough service telemetry to evaluate the investigation afterward.

## Timeline

- 07:05:45Z: the seeded fault began after the healthy baseline (onset).
- 07:09:19Z: ShopCheckoutErrors began its first firing run (detection).
- 07:10:07Z: the P1 ticket was acknowledged (acknowledgement).
- 07:12:19Z: the detecting alert's first firing run ended (recovery).

## Supporting information

The Prometheus snapshot, ticket.json, and verbatim transcript are committed with this report. The metric queries and results are documented in ai-rca-eval.json; its predictions were checked at 07:11:45Z and against the baseline at 07:00:45Z.

## Problem record

- Incident record: 1224ad8d-06a8-4ae3-865a-da2015a4ddb5.
- Root cause: the seeded feature-flag fault produced product-catalog errors and ad and recommendation latency symptoms.
- Known error: checkout can fail when product-catalog calls return errors during the seeded fault.
- Workaround: disable the failing seeded flags and verify checkout errors and latency recover.
