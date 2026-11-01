# Future cookie parsing maintenance

Pin `future` in `requirements.txt` from **0.16.0 to 0.18.3**, the first fixed
release for [#459 / GHSA-v3c5-jqr6-7qm8 / CVE-2022-40899](https://github.com/advisories/GHSA-v3c5-jqr6-7qm8).
The affected backported cookie date parser can spend excessive CPU processing
malformed expiry text from a Set-Cookie header. This is a narrow dependency
patch, not a Python/runtime or FATE application migration.

[Official 0.18.3 metadata](https://pypi.org/project/future/0.18.3/) permits
Python >=2.6 excluding 3.0–3.2 and explicitly classifies Python 3.6. It declares
no runtime dependencies. The official source distribution SHA-256 is
`34a17436ed1e96697a86f9de3d15a3b0be01d8bc8de9c1dffd59fb8234ed5307`.
The release supplies an sdist, not an official wheel. The isolated local
pure-Python wheel used for validation has all 142 `future`/`past` Python
modules byte-identical to that official source. An external offline deployment
wheelhouse must separately prepare the matching artifact; it is not changed here.

## Actual Python 3.6 validation

On 2026-11-01, maintenance built actual native **CPython 3.6.15** from the
[official Python.org source](https://www.python.org/downloads/release/python-3615/)
in an isolated writable directory, using GCC 14.2.0, `--without-ensurepip` and
`make -j2`, without `make install`, PGO, global pip or system interpreter changes.
The source archive matched Python.org's published MD5
`bc04aa6c2a1a172a35012abd668538cd`; its recorded SHA-256 is
`6e28d7cdd6dd513dd190e49bca3972e20fcf455090ccf2ef3f1a227614135d91`.
No GPG verification is claimed. Current glibc declares `sinpi`, so the isolated
runtime build needed only its private C math helper renamed from `sinpi` to
`_Py36_sinpi` (four occurrences, unchanged function logic). No `future`, stdlib
Python module or FATE application code was patched to make imports pass.
Python 3.6 is end-of-life; this is a compatibility test runtime, not a production
runtime recommendation or installation.

The exact added unittest now runs with **5 passes, 0 failures, 0 skips** on
candidate 0.18.3. Baseline 0.16.0 has **4 passes, 1 expected bounded parser
failure, 0 skips**. Both genuinely import the complete legacy
`future.backports.http.cookiejar` module. Native 3.6 exposed an unrelated harness
assumption: `builtins.__spec__.origin` is `None`. The provenance check now uses
`sys.builtin_module_names` and actual module/type identity, without a shim or
weakened import guard.

Six additional ordinary offline maintenance controls pass on both versions:
real runtime/package and backports/moves imports, full-module normal HTTP/ISO
date parsing, ordinary header parsing, backported CookieJar request/response
roundtrip, moved CookieJar roundtrip, and both cookie-header modules. Roundtrips
cover expiry, Secure and domain restrictions, without network requests.
The native `ssl` module imports against OpenSSL 3.5.7; this is not a TLS
handshake, certificate validation or service acceptance test. Optional build
modules including `_hashlib`, `_bz2` and `_lzma` were unavailable; stdlib
`hashlib` works, and none is required by these scoped controls. No complete
CPython standard-library test suite or full FATE build is claimed.

## Scope, bounded regression and historical evidence

Static tracked-Python import review found no direct `future`/`past` caller.
Three `import builtins` occurrences are Python 3 stdlib use, not third-party
backports. `__future__` language imports were not counted as package use.
No remote application exploitability is inferred.

The added source-level regression pins the two official cookiejar source
hashes and compiles unchanged original date-parser functions, constants and
regexes via AST. Its namespace-local regex-module copy contains the upstream
ASCII-flag assignment without changing the process-wide stdlib module. A fixed
2060-character invalid expiry fixture exceeds a 0.5 CPU-second POSIX budget on
the old parser; the candidate returns within that budget. An 8-second child
limit bounds maintenance runs. No new or enlarged attack fixture was added.

Earlier Python 3.12 validation had candidate **4 passes and 1 full-import
skip**, versus baseline **3 passes, 1 expected parser failure and 1 skip**.
Both complete legacy backports imports failed there because `imp` was removed.
Those historical limitations were real; the later native 3.6 runs above close
the supported-runtime/full-module gate rather than treating metadata, grammar
or offline wheel selection as execution evidence.

Run the committed unittest with the pinned dependency installed:

```sh
python fate_flow/tests/test_future_cookiejar_security.py
```

No full FATE requirements installation, ML/framework/native build, training,
service, deployment or production acceptance was performed. No deployment
artifact or runtime version was changed. Publication alone does not close the
GitHub alert.
