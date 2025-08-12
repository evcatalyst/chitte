# Repository Reset Log

Date: 2025-08-12

Reason:
- Clean up fragmented / failing CI
- Standardize pipelines
- Preserve environment secrets (Grok API)

Actions Taken:
- Removed legacy workflows from `.github/workflows/`
- Added new workflows:
  - ci.yml (lint + test + build matrix)
  - codeql.yml (static analysis)
  - dependency-review.yml
  - release.yml (manual + tag driven release)
  - housekeeping.yml (stale issue/PR management & placeholder for label sync)

Not Changed:
- Application source code
- Secrets (e.g., GROK_API_KEY)

Next Steps:
- Verify CI green on this PR
- Enable/confirm branch protection for `main`
- Optionally reintroduce advanced steps (coverage upload, artifact packaging) if needed

Rollback Strategy:
- Prior state is available via repository history before merging this PR.