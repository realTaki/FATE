# Python 3.6-compatible certifi maintenance

The existing deployment script creates a Python 3.6 environment. Pin certifi
2025.4.26, the newest non-yanked release whose official PyPI metadata declares
Python >=3.6, rather than the Python >=3.7 release proposed by Dependabot.
No Python runtime or TLS verification setting changes.

This addresses the exact `requirements.txt` e-Tugra removal alert
[GHSA-xqr8-7jwr-rhp7](https://github.com/advisories/GHSA-xqr8-7jwr-rhp7)
(first fixed in 2023.7.22). It is only a partial legacy-runtime repair:
GLOBALTRUST 2020 and emSign certificates remain in the unmodified official
bundle. This does **not** claim that the trust store is fully secure or current.
Removing later distrusted roots needs a separately reviewed supported-runtime
upgrade; no certificates are hand-edited here.

The official wheel metadata is available at
[PyPI certifi 2025.4.26](https://pypi.org/project/certifi/2025.4.26/).
The official wheel SHA-256 is
`30350364dfe371162649852c63336a15c70c6510c2ad5015b21c2345311805f3`.
It has no runtime dependencies. The existing `--no-index` deployment process
must have this exact release available in its externally maintained wheelhouse;
this source-only change does not replace or deploy that archive.

With the pinned requirements installed, run the offline regression:

```sh
python fate_flow/tests/test_certifi_trust_bundle.py
```

Maintenance checks verified the wheel hash and RECORD entries, Python 3.6
source grammar, the pre-3.7 resource fallback, and the public `where`/`contents`
API and CA loading on the available Python 3.12 interpreter. No Python 3.6
binary was available, so these checks are **not** actual Python 3.6 runtime,
full requirements installation, FATE service, TLS peer, training, database,
packaging or production acceptance. No full-trust-store security claim is made.
