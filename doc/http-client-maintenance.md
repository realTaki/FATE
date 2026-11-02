# urllib3: coherent 1.x security patch

Only two requirement pins change:

- `urllib3==1.24.2` → `urllib3==1.26.20`
- `requests==2.20.0` → `requests==2.25.1`

The Requests companion is necessary:2.20.0 requires urllib3<1.25, so changing
urllib3 alone would create an invalid component graph.2.25.1 accepts
urllib3>=1.21.1,<1.27. Its other default constraints accept the unchanged
chardet3.0.4, idna2.7 and certifi2025.4.26. No runtime package is added.
The selected component graph preserves Python3.6 support in official metadata;
the interpreter, production functions, proxy settings and service configuration
are not changed. This does not claim the entire old FATE scientific dependency
graph is coherent.

## Exact mapped targets

The candidate exceeds the existing mapped first patches for high#530 and
medium#563/#534/#343/#138: respectively1.26.17,1.26.19,1.26.18,1.24.3 and1.25.9.
These were actual open Dependabot alerts on this repository at qualification.
They concern redirect/header/body handling and URL validation. This patch is
not a claim that all urllib3 or Requests advisories are resolved.

## Actual validation

Verified official wheels, using existing CPython3.12.14 and the exact five-package
component graph above:8/8 checks pass, zero skips. They exercise complete real
Requests/urllib3 modules and the unchanged FATE `local_api` source function and
actual `HEADERS` constant, isolated only from unrelated application imports.
Coverage includes JSON GET/POST, error wrapping, streaming reads, ordinary303
POST→GET body handling, same-origin preservation and cross-origin removal of
synthetic Cookie/Proxy-Authorization headers.

All HTTP requests go only to two short-lived owned127.0.0.1 test servers.
No external service, live account, user credential, malformed resource-exhaustion
payload or HTTP/2 protocol is involved. Tests use an empty HOME to avoid reading
account files; existing proxy configuration is unchanged. Servers are shut down
and joined at the end.

The old urllib3/Requests pair does not import on existing Python3.12:
`ModuleNotFoundError: urllib3.packages.six.moves`. This is recorded as a baseline
toolchain limitation, not a passing baseline or proof of a new candidate failure.
No old package is patched/shimmed and no interpreter is installed. Native3.6,
live TLS/production services and the complete FATE application are not claimed.

With the chosen real component graph installed/on PYTHONPATH:

```bash
python fate_flow/tests/test_http_client_compatibility.py
```

Official wheel SHA256 values for the changed packages:

- Requests2.25.1: `c210084e36a42ae6b9219e00e48287def368a26d03a048ddad7bfee44f75871e`
- urllib3 1.26.20: `0ed14ccfbf1c30a9072c7ca157e4319b70d65f623e91e7b32fadb2853431016e`

## Remaining versions and scope

Mapped urllib3 IDs681/631/609/606/605/594 and Requests' own existing alerts are
not covered. In particular, full coverage including urllib3#681 first requires
2.8.0, whose official metadata requires Python>=3.10; this exceeds the selected
legacy branch. A compatible Requests version must also permit urllib32.x:
2.31.0 permits urllib3<3 and requires Python>=3.7, while the mapped Requests
2.33.0 patch requires Python>=3.10. Only metadata was inspected for these versions;
no2.x library or runtime migration is included here. Actual deployment/runtime
and coherent downstream compatibility need evaluation before such a migration.

The independent psutil/Pygments drafts are not included; already merged security
history remains. Draft publication and local tests do not count as actual alert
closure. Read default-branch alert states after a separately authorized merge.
