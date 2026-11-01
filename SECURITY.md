# Security policy

This project has no published supported-release or response-time commitment. Security work currently targets the development branch; no maintenance of older revisions is promised.

A private reporting contact has not been confirmed. The maintainer must enable and test GitHub private vulnerability reporting or publish a private contact before inviting sensitive reports. If the repository Security tab offers ?Report a vulnerability?, use that private flow; its availability was not verified in this audit. Do not put credentials or exploit details in public issues. A public request for a private contact should contain no sensitive details.

Include affected commit, environment, impact, minimal reproduction and suggested mitigation privately. Redact credentials and personal records. Revoke/rotate exposed keys; deleting a file does not revoke a key. No history rewrite is authorized by this policy.

SQLite enforcement uses read-only connections, an assigned-table authorizer, a progress interrupt and a 200-row cap, independently of model prompts. These do not guarantee protection from every denial-of-service query: individual values/aggregate strings can still be large. Questions are limited to 2,000 characters. Model/provider timeout applies per call, not to the entire multi-call request.

Before public hosting, configure provider project budgets/alerts and available hard spend limits, restrict ingress or add hosting-level rate limits, and monitor usage. The UI has no authentication or global rate limit. Server-owned keys can incur charges. Confirm hosting settings in the provider dashboard; local code cannot verify those settings. Do not submit private questions or unnecessary contact data.
