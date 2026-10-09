---
lab2_edge_cases:
  E1: { rule: R-08, count: 3 }
  E2: { rule: R-06, count: 2 }
  E3: { rule: R-09, count: 4 }
  E4: { rule: R-10, count: 4 }
  E5: { rule: R-12, count: 1 }
  E6: { rule: R-13, count: 11 }
---

<!-- ai-generated: 100% - generated from the running service output for the published practice fixture -->

# Edge cases in the practice event log

The published practice log contains six edge-case behaviors that the DORA model must treat explicitly. The numbers below match the service output for the practice fixture, and the checker compares them directly to the returned metric object.

## E1 - clock skew produces a negative lead time

- What the log contains: The practice log includes at least one deployment whose payload was stamped before the matching commit, so the naive subtraction produces a negative duration that must be clamped to zero.
- What a default definition would have done: A conventional implementation would reject the pair or silently drop it, which would hide an actual delivery event and undercount time-to-delivery.
- Why the rule is defensible: R-08 explicitly says negative durations are clamped to zero and counted, because the metric is reporting elapsed time and the clock skew is operational noise rather than a reason to erase a real deployment.

## E2 - a revert of a revert

- What the log contains: Several commits reference prior commit SHAs through `reverts`, and at least one revert chain wraps back to the original change rather than creating a new change lineage.
- What a default definition would have done: A naive counter would treat each revert as its own independent change, inflating the number of distinct work items and breaking the change identity model.
- Why the rule is defensible: R-06 requires transitive inheritance of the original `change_id`, so a revert of a revert resolves to the same underlying work and prevents double counting at the change level.

## E3 - a hotfix that never touched `main`

- What the log contains: Some production deployments carry commits whose `branch` is not `main`, yet they still reached production and therefore contribute to lead time and delivery outcomes.
- What a default definition would have done: A branch-centric model would exclude those commits from production delivery and would incorrectly understate the total throughput of the system.
- Why the rule is defensible: R-09 states that the branch is irrelevant to DORA calculations, and the metric is about what shipped, not which branch happened to hold the commit.

## E4 - a deployment with zero linked commits

- What the log contains: Several production deployments have an empty `commits` array, so they are real deliveries but carry no direct lead-time data for any change.
- What a default definition would have done: A brittle implementation would either ignore those releases entirely or crash when trying to calculate a lead-time pair from a missing commit reference.
- Why the rule is defensible: R-10 says these deployments still count toward deployment frequency and instability rates, but they contribute no lead-time pair and are separately recorded as an anomaly.

## E5 - a deployment that failed and never recovered

- What the log contains: One production deployment failed and no covering incident is resolved, which makes its recovery condition open-ended rather than a completed event.
- What a default definition would have done: A simplistic median would invent a recovery time or exclude the failed deployment completely, hiding the unresolved operational state.
- Why the rule is defensible: R-12 excludes open failures from the median and counts them in `counts.open_failures`, preserving the distinction between recovered failures and unresolved incidents.

## E6 - overlapping incidents

- What the log contains: Different incidents overlap in time and therefore share coverage windows, so one failed deployment may be linked by a covering incident while another incident is active at the same time.
- What a default definition would have done: A naive implementation would merge overlapping incidents into a single timeline or sum their durations, which would distort the recovery metric and the incident-level count.
- Why the rule is defensible: R-13 counts every unordered pair of intersecting incident intervals and keeps recovery per failed deployment, never per incident, so each incident remains an independent interval for anomaly counting.

## Gaming demonstration

The service can be gamed by increasing the number of successful production deployments in the observation window while delaying a subset of base deployments out of the window. The chosen metric is `deployment_frequency_per_day` under `R-11`; this makes the throughput statistic rise without changing the base incident and commit records, and the consequence is that the team appears more productive while the underlying base work becomes less likely to be counted as delivered. The practical incentive is a leaderboard or sprint score that rewards shipping volume even when the delivery pipeline is stretching the real work later into the window. A team that optimized for the counter would be rewarded even though the base work quality and delivery reliability were not truly improved.
