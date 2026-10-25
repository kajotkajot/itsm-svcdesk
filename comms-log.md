---
lab4_comms:
  awareness: 2026-10-12T07:10:07Z
  detection: 2026-10-12T07:09:19Z
  classification: 2026-10-12T07:20:00Z
  nis2:
    early_warning_due: 2026-10-13T07:10:07Z
    notification_due: 2026-10-15T07:10:07Z
    notification_sent: 2026-10-12T08:30:00Z
    final_report_due: 2026-11-12T08:30:00Z
  ksc:
    early_warning_due: 2026-10-13T07:09:19Z
    notification_due: 2026-10-15T07:09:19Z
    notification_sent: 2026-10-12T08:30:00Z
    final_report_due: 2026-11-12T08:30:00Z
  dora:
    initial_due: 2026-10-12T11:20:00Z
    initial_sent: 2026-10-12T08:30:00Z
    intermediate_due: 2026-10-15T08:30:00Z
    intermediate_sent: 2026-10-15T08:00:00Z
    final_due: 2026-11-15T08:00:00Z
  log:
    - {
        at: 2026-10-12T08:30:00Z,
        to: NIS2 competent authority and Polish CSIRT,
        what: Significant incident notification under NIS2 and KSC,
      }
    - {
        at: 2026-10-12T08:30:00Z,
        to: Financial supervisor,
        what: DORA initial major ICT-related incident notification,
      }
    - {
        at: 2026-10-15T08:00:00Z,
        to: Financial supervisor,
        what: DORA intermediate report,
      }
    - {
        at: 2026-11-12T08:30:00Z,
        to: NIS2 competent authority and Polish CSIRT,
        what: NIS2 and KSC final incident reports,
      }
    - {
        at: 2026-11-15T08:00:00Z,
        to: Financial supervisor,
        what: DORA final report,
      }
---

<!-- ai-generated: 70% - calculated regulatory deadlines from the recorded incident instants and documented rules. -->

# Communications log: the regulators' clocks

## The three instants you defend

Detection for KSC is the first qualifying alert at 07:09:19Z on 12 October 2026. Awareness for NIS2 is 07:10:07Z, when the on-call acknowledged the page and had confirmed that the checkout incident was significant. The incident was classified as major for DORA at 07:20:00Z, after recovery at 07:12:19Z and review of the observed impact on checkout, product-catalog, ad, and recommendation. The classification time is a defensible response decision, not a timestamp encoded in the snapshot.

The NIS2 early-warning deadline is 24 elapsed hours after awareness, and its notification deadline is 72 elapsed hours after awareness. The KSC deadlines use the detection instant in the same way. Each final-report deadline is one calendar month after the corresponding notification sent time. For DORA, classification plus four hours is earlier than awareness plus 24 hours, so the initial-report deadline is 11:20Z on 12 October. The intermediate-report deadline is 72 hours after the initial report, and the final-report deadline is one calendar month after the intermediate report.

## The log

At 08:30Z on 12 October, the service would notify the NIS2 competent authority and the Polish CSIRT of the significant incident, within both early-warning deadlines. At the same time, it would send the DORA initial notification, ahead of its 11:20Z deadline. At 08:00Z on 15 October, it would send the DORA intermediate report, 30 minutes before its deadline. The NIS2 and KSC final reports would be sent by 08:30Z on 12 November, and the DORA final report by 08:00Z on 15 November.
