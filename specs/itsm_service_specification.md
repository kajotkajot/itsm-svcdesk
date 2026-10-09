<!-- ai-generated: 100% - written by the lecturer; it is the specification the whole lab is graded against -->

# Service Desk Specification

## 1. Purpose

This specification defines the operating rules for the service desk workflow for the first release of the ITSM support service. It translates the approved decisions into implementable behavior and provides the basis for downstream API, database, and user-interface design.

## 2. Scope

The system covers incident reporting, ticket triage, priority assignment, SLA measurement, closure handling, and VIP handling. The service is limited to the support workflow described in the approved decision set and does not include advanced change management or asset lifecycle controls in this phase.

## 3. Core operational decisions

### 3.1 P1 SLA clock

The service must measure P1 response SLA using wallclock time, not business hours. The clock runs continuously, including nights, weekends, and public holidays. A response target of 1 hour is enforced for all P1 reports and is not paused when the business is closed.

### 3.2 Ticket immutability after closure

Once a ticket reaches a closed state, it must be treated as immutable. No status transition back to open is permitted for the original ticket record. Audit history must remain intact. If a customer reports a new issue linked to the same problem after closure, the service must create a separate follow-up ticket rather than reopen the closed record.

### 3.3 VIP priority handling

Tickets submitted by VIP reporters must receive a priority boost of +2 levels within the standard matrix. This adjustment applies only at triage time and does not alter the core rules of the priority matrix for non-VIP customers. A low urgency report from a VIP reporter may be elevated to a noticeably higher priority level, while already critical cases remain at the top of the queue.

## 4. Functional requirements

### 4.1 Ticket intake

The service must accept a ticket with at least: reporter identity, category, impact, urgency, description, and timestamp. Each ticket must be assigned a unique identifier and stored with a complete audit trail.

### 4.2 Priority calculation

The service must calculate priority from the standard matrix, then apply the VIP boost when the reporter qualifies for VIP treatment. The result must be deterministic and reproducible for the same input values.

### 4.3 SLA timing

The system must calculate P1 response deadlines against wallclock time. The SLA timer must continue running outside standard working hours and must be visible in reporting and dashboards.

### 4.4 Closure and audit integrity

When a ticket is closed, the system must lock the record for further modification of the original lifecycle data. Any later customer follow-up must be recorded as a new ticket or linked note, not as a reopen of the original record.

## 5. Non-functional requirements

- The system must maintain a clear audit trail for every ticket lifecycle event.
- The SLA model must be testable and easy to validate through deterministic scenarios.
- The priority logic must be explainable to service owners and support teams.
- Ticket handling must preserve fairness across standard and VIP customers while honoring agreed VIP commitments.

## 6. Acceptance criteria

1. A P1 ticket created at 23:00 on a Friday must still be measured against the same 1-hour response target until the response is recorded.
2. Closing a ticket must prevent reopening of the same ticket record.
3. A follow-up issue after closure must be represented as a new ticket.
4. A VIP ticket with base priority P4 and impact/urgency values equivalent to a low-priority report must be elevated by +2 levels according to policy.
5. Reports and dashboards must expose the final ticket decisions in a manner consistent with the approved service policy.

## 7. Result

This specification establishes the rules for the first release of the service desk and acts as the contract between product, support operations, and engineering. It is intentionally narrow so that the first implementation remains stable, auditable, and aligned with the approved decisions.
