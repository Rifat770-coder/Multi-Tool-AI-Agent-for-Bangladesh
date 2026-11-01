# Contributing

Follow README.md for Python 3.13 setup. Install `requirements.lock`, run `python -m pip check` and `python verify.py` before proposing changes. Create a topic branch and submit a pull request explaining the problem, behavior change, tests and limitations. Preserve the current four tools and UI unless a design change is explicitly agreed.

Use readable Python, standard-library tooling where practical, and update relevant documentation/tests. Never commit .env, credentials, personal data, downloaded CSVs or environments. Redact logs and screenshots. Bug reports should include OS, Python/package versions, reproduction steps, expected/actual results and sanitized errors. Discuss substantial features in an issue before implementation.

Dataset changes require source URLs, fixed revisions, real checksums, license/attribution review and conversion verification. See docs/DATA_LICENSES.md. Do not silently replace real data with fixtures. The code license is currently unresolved; discuss licensing with the maintainer before contributing substantial work.
