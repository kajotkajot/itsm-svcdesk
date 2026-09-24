---
svcdesk_decisions:
  C1: wallclock # wallclock | business
  C2: immutable # reopen | immutable
  C3: vip # matrix | vip
---

<!-- ai-generated: 90% - AI drafted the structure and wording for the decisions, and the final review was completed by a human to ensure policy fit and clarity -->

# Decisions

## C1 - SLA clock for P1

**Decision:** Wallclock (24/7 continuous SLA, no business hours pause)

**Rejected alternative:** Business (SLA pause outside 09:00-17:00 Monday-Friday)

**Reason:** Wallclock provides consistent, predictable behavior for critical P1 tickets. Customers need assurance that critical issues are addressed immediately regardless of business hours. The additional implementation complexity of business-hours tracking is not justified for a first-generation system. Testing is simpler and more reproducible with 24/7 measurement.

**Service owner:** Operations Director (responsible for SLA compliance tracking and escalation policies)

**Customer outcome:** Critical tickets receive consistent 1-hour response target regardless of when they are reported. This ensures urgent issues do not experience delays due to off-hours timing.

## C2 - Closed tickets and reopening

**Decision:** Tickets are immutable after closure (full audit trail integrity)

**Rejected alternative:** Closed tickets MAY be reopened within 7 calendar days of closure

**Reason:** Once a ticket is closed, the lifecycle record must reflect a final, verified state. Allowing reopen flows creates ambiguity around ownership, time-to-resolution, and audit integrity, which weakens reporting and undermines confidence in the service history. The support process is clearer and more accountable when a completed case remains closed and a new ticket is created only when genuine follow-up work begins.

**Service owner:** Support Manager (responsible for reopening policies, customer satisfaction, and ticket quality)

**Customer outcome:** Support teams can trust that closure is final and auditable, which improves reporting accuracy and customer confidence. When a customer needs additional help, a fresh case can be created with a clear timeline instead of reactivating a completed record and obscuring the original resolution history.

## C3 - VIP reporters and the priority matrix

**Decision:** VIP reporters receive a priority boost of +2 levels within the standard matrix (VIP boost applied)

**Rejected alternative:** Matrix only (VIP status does not change the ticket's priority)

**Reason:** The priority matrix exists to route tickets to appropriate teams and prevent resource waste on low-urgency reports. VIP boost (+2 levels) significantly honors customer status while preserving the integrity of the triage process. A VIP report of a low-priority issue (impact=3, urgency=3, base P4) becomes P2, which is a meaningful improvement. Conversely, already-high-priority issues (P1, P2) remain at or near the top. This approach ensures VIP customers receive noticeably faster service while maintaining fair resource allocation.

**Service owner:** Customer Success Manager (responsible for VIP agreements and account-level response targets)

**Customer outcome:** VIP customers receive measurably faster response times on all tickets through the two-level priority boost. Standard customers continue to receive responses based on issue severity alone. The organization maintains control of resource allocation and can on-board new VIP accounts without destabilizing support operations.
