# IDNA 548: legacy Python-compatible HTTP dependency closure

## Scope and upstream

This draft addresses the real medium Dependabot [alert 548](https://github.com/realTaki/FATE/security/dependabot/548), GHSA-jjg7-2v4v-x38h / CVE-2024-3651. Its first fixed idna version is 3.7. It is not a generalized audit or a claim that FATE's HTTP stack is fully patched.

The inspected parent FederatedAI/FATE legacy releases v1.2.2 and v1.4.6 still pin idna 2.7 and requests 2.20.0. Their immutable root requirement blobs were verified before reuse. Neither inspected release supplies this fixed dependency closure; later upstream branches are not ruled out.

Only three production dependency entries change:

- idna 2.7 to 3.7, the publisher's unmodified first fixed version.
- requests 2.25.1 to 2.27.1, retaining Python 3.6 support while allowing idna >=2.5,<4 on Python 3. The old Requests metadata requires idna <3, so changing only idna would be inconsistent.
- Explicitly add charset-normalizer 2.0.12 because Requests 2.27.1 requires ~=2.0.0 on Python 3, even when chardet is present. The use_chardet_on_py3 extra does not remove that requirement.

Existing chardet 3.0.4, urllib3 1.26.20, certifi 2025.4.26 and all other pins remain unchanged. The six-package mandatory closure was checked against official metadata with Python 3.6 and 3.12 markers; this is not resolution or installation of the entire legacy root requirements. No production runtime is changed. Requests still prefers the original chardet when present.

## Focused validation

Unmodified official PyPI wheels were used, with SHA256 checks:

- idna 3.7: `82fee1fc78add43492d3a1898bfa6d8a904cc97d8427f683ed8e798d07761aa0`
- requests 2.27.1: `f22fa1e554c9ddfd16e6e41ac79759e17be9e492b3587efa038054674760e72d`
- charset-normalizer 2.0.12: `6881edbebdb17b39b4eaaa821b438bf6eddffb4468cf344f09f89def34a8b1df`

Existing CPython 3.12.14: 18 checks pass, no skips. Ten checks cover ordinary IDNA roundtrips/UTS46, small invalid labels, prepared Unicode hostnames, JSON/multipart preparation, original decoder identity, and the documented nonfinite JSON policy. Eight existing HTTP tests exercise the unchanged `api_utils.local_api` function, JSON GET/POST/error wrapping, streaming, and redirects against only two owned loopback servers. Unicode hostname preparation does not perform DNS or send a request. No external service or FATE server is contacted.

With the original idna 2.7 / requests 2.25.1 and unchanged shared dependencies, the same suite has 17 passes and only the expected idna >=3.7 version-gate failure. The nonfinite JSON test deliberately accepts each version's documented behavior; it does not claim equivalence. An initial fixture incorrectly expected ValueError for outgoing nonfinite JSON; the observed candidate InvalidJSONError was preserved and the assertion corrected, without changing any library source.

To reproduce in an isolated environment containing the exact six pins above:

```
python -m unittest -v fate_flow.tests.test_idna_http_compatibility fate_flow.tests.test_http_client_compatibility
```

Official metadata declares support for Python 3.6 and all 147 Python files from the baseline/candidate wheel fixtures plus the new test parse with the 3.6 grammar. **Native Python 3.6 was not executed.** No interpreter rebuild or global installation occurred. These finite component checks are not full FATE, full root installation, TLS/proxy authentication, every caller payload, deployment, or exploit/DoS regression validation. The repository's documented full suite requires a complete legacy installation and remains unrun.

## Behavior boundaries and remaining alerts

Both idna versions implement IDNA2008. Unicode tables change from Unicode 10 to 15.1, malformed-label validation tightens, and the optional codec registration changes to idna2008. No direct tracked Python idna imports or codec registrations were found, but transitive or external callers may differ.

Requests 2.27.1 rejects outgoing JSON NaN/Infinity with InvalidJSONError rather than emitting nonstandard JSON. Incoming JSON decoding errors use a ValueError-compatible Requests exception. Ordinary payload and broad application error wrapping were tested, but this does not establish that every existing caller avoids nonfinite values or relies only on those exception classes.

Newer idna [632](https://github.com/realTaki/FATE/security/dependabot/632), first fixed 3.15 (official Python >=3.8 requirement), remains uncovered. The recorded Requests alerts 506/559/591/621 are not fixed by 2.27.1. This preserves the existing legacy runtime boundary instead of silently upgrading it to satisfy newer releases. A draft, successful tests, or a dependency graph is not actual fixed status; alert 548 is counted only after a separately approved merge and GitHub default-branch closure.
