---
lab5_triage:
  image: "TODO: ghcr.io/kajotkajot/itsm-svcdesk@sha256:<image-job-digest>"
  sarif_receipt: "TODO: issue number of the sarif receipt"
---

<!-- ai-generated: 100% - GitHub Copilot drafted the local decisions; CI findings and bake-off numbers are pending -->

# Triage

Local draft. Complete the image digest, receipt number, scanner findings, and canary matrix after the required GitHub Actions runs and SARIF receipt.

| Tool    | Rule                                           | Decision       | Reason                                                                                                                                                                                                                     |
| ------- | ---------------------------------------------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| trivy   | CVE-2025-62727, CVE-2026-48818, CVE-2026-54283 | fix            | CI run 44092574150 found all three HIGH findings in Starlette 0.46.2. Upgraded FastAPI to 0.163.1, which resolves Starlette 1.10.0; the same Trivy 0.74.0 image gate then reported zero HIGH or CRITICAL findings locally. |
| semgrep | svcdesk-no-catch-all-exception                 | accept         | The broad catches are limited to request JSON parsing and return the API's invalid-body response; narrow exception handling remains a follow-up.                                                                           |
| semgrep | svcdesk-no-sql-fstring                         | false-positive | update_ticket receives fixed workflow field names, while all data values are still passed through SQLite placeholders.                                                                                                     |

## Bake-off

Pending the canary SARIF receipt and the labels that the course reveals afterward. Do not treat the practice matrix as the result for this repository: the canary set is chosen for this login, and its labels are not available before the receipt. After receiving those files, record TP, FP, and FN for Trivy, Grype, OSV-Scanner, gitleaks, and Semgrep, along with precision, recall, and F1 from bakeoff.json. Compare the detectors as gates based on both missed defects and false alerts; a high recall alone can create alert fatigue, while a high precision with low recall leaves defects unseen. Note which scanner results were surprising, including any duplicate findings that count once under the published matching rule, and identify any labelled defects that none of the five scanners detected. Seeded defects make every measured recall an upper bound for real service defects, so these figures describe this canary set rather than general detector performance. Replace this paragraph with the measured numbers and your decision about which gates to keep once the canary run, receipt, labels, and matrix are complete.
