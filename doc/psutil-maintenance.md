# psutil alert #4: compatible 5.x patch

## Change

`requirements.txt`: `psutil==5.4.7` → `psutil==5.6.7` only. All other pins,
including the already merged pycryptodomex3.19.1 and PyYAML5.4.1, are preserved.

The actual Dependabot alert is high-severity
[GHSA-qfc5-mcwq-26q8 / CVE-2019-18874](https://github.com/advisories/GHSA-qfc5-mcwq-26q8).
It lists versions through5.6.5 as affected and5.6.6 as patched. Upstream's
5.6.6 changelog records the reference-count fix;5.6.7 additionally corrects
Windows source-distribution compilation. This is the same5.x API family, not
a framework, application-protocol, or project-runtime migration.

Official release metadata for both5.4.7 and5.6.7 permits Python2.6/2.7 and3.4+
(excluding3.0–3.3). No normal Linux runtime dependencies are added. Official
sdist SHA256 values:

- 5.4.7: `5b6322b167a5ba0c5463b4d30dfd379cd4ce245a1162ebf8fc7ab5c5ffae4f3b`
- 5.6.7: `ffad8eb2ac614518bbe3c0b8eb9dffdb3a8d2e3a7d5da51c5b974fb723a5c5aa`

## Actual project use and checks

The current repository uses psutil only in
`fate_flow/utils/job_utils.py`: `kill_process()` instantiates `Process(pid)`,
enumerates `children(recursive=True)`, and calls `kill()`. The production
functions and their existing behavior are unchanged.

`fate_flow/tests/test_psutil_process_compatibility.py` compiles the two actual
unchanged source functions, supplying real `os`, `errno`, psutil, and a standard
logger without loading unrelated Flask/database/model dependencies. The tests
create uniquely marked local subprocesses and signal only that owned test
family. Cases cover PID validation, live/already-reaped processes, real child
enumeration, a direct kill, recursive child cleanup, and preservation of an
unrelated owned neighbour. A readiness handshake waits for exec completion;
this fixes a test-startup race, not production code.

Both official sources were built unchanged using the existing GCC and existing
CPython3.12.14, with `CC=gcc LDSHARED='gcc -shared' python setup.py build_ext
--inplace`. The runtime's default compiler name `clang` was unavailable; this
explicit selection uses an already installed compiler, not a new tool/runtime.

- Candidate5.6.7:7/7 pass, zero skips.
- Baseline5.4.7:6 ordinary behavior tests pass; only the explicit patched-version
 gate fails. This is not a double-free exploit reproduction.
- The new test also parses with Python3.6 grammar. Native3.6 execution is not
 claimed; no additional interpreter was installed or rebuilt for this change.

With a verified psutil build/import path:

```bash
PYTHONPATH=/path/to/verified/psutil-source-build \
  python fate_flow/tests/test_psutil_process_compatibility.py
```

This validates the actual psutil call sites on Linux with the existing runtime,
not the full FATE service/dependency environment, other operating systems, or
unrelated security issues. No malformed process data or crash/resource-exhaustion
payload is used. A draft/merge is not evidence that the actual default-branch
alert has closed; read its platform state separately after an approved merge.

Official sources: [release5.6.7](https://pypi.org/pypi/psutil/5.6.7/json),
[release5.6.6 changelog](https://github.com/giampaolo/psutil/blob/release-5.6.6/HISTORY.rst),
[release5.6.7 changelog](https://github.com/giampaolo/psutil/blob/release-5.6.7/HISTORY.rst).
