# Validation-limited future security maintenance

**Not full-runtime acceptance or ready-to-merge evidence:** the available test
interpreter is Python 3.12. Both old and candidate legacy `future.backports`
imports fail there because they import the removed stdlib `imp` module. No
`imp` shim, library edit, stdlib patch or new interpreter was introduced.
Actual Python 3.6 module/application acceptance remains unrun.

Pin `future` in `requirements.txt` from **0.16.0 to 0.18.3**, the first fixed
release for [#459 / GHSA-v3c5-jqr6-7qm8 / CVE-2022-40899](https://github.com/advisories/GHSA-v3c5-jqr6-7qm8).
The affected backported cookie date parser can spend excessive CPU processing
malformed expiry text from a Set-Cookie header.

[Official 0.18.3 metadata](https://pypi.org/project/future/0.18.3/) permits
Python >=2.6 excluding 3.0–3.2 and explicitly classifies Python 3.6. It declares
no runtime dependencies. The official source distribution SHA-256 is
`34a17436ed1e96697a86f9de3d15a3b0be01d8bc8de9c1dffd59fb8234ed5307`.
The release provides an sdist, not an official wheel. Maintenance built a local
pure-Python wheel with existing tools, verified its metadata and performed
isolated `--no-index --python-version 3.6 --no-deps` wheel selection. This is
packaging/metadata evidence, not execution by a Python 3.6 interpreter. The
external offline deployment wheelhouse must prepare the matching artifact
before deployment; it is not modified here.

## Scoped source use and bounded regression

Static tracked-Python import review found no direct `future`/`past` caller.
Three `import builtins` occurrences are the Python 3 stdlib module, not the
third-party backports. `__future__` language imports were not counted as
package use. No remote application exploitability is inferred.

The added unittest pins the two official cookiejar source hashes. It compiles
only the **unchanged original date-parser functions, constants and regexes**
from the installed source using AST. The upstream ASCII-flag assignment is
contained in a namespace-local copy of the regex module, without changing the
process-wide stdlib module. This explicit source-level harness is not a claim
that the complete backports package imported on the test interpreter.

On Python 3.12 the candidate has **4 passes, 1 explicit full-import skip**;
0.16.0 has **3 passes, 1 expected security failure, 1 skip**. Actual
`future.utils` mapping helpers, stdlib-builtins provenance, and source-level
normal HTTP/ISO dates and timezone semantics pass. A fixed 2060-character
invalid expiry fixture exceeds a 0.5 CPU-second POSIX budget on the old parser;
the candidate returns within that budget. An 8-second child-process limit
bounds maintenance runs. No network, large allocation or unbounded CPU attack
is performed. The supported-runtime full-module control is intentionally
skipped on Python >=3.12, and has not been run on actual Python 3.6.

Run with the pinned dependency installed:

```sh
python fate_flow/tests/test_future_cookiejar_security.py
```

The installed cookiejar and added test also parse with Python 3.6 grammar.
No full FATE requirements installation, ML/framework/native build, service,
training, deployment or production acceptance was performed. This narrowly
updates the declared dependency; no runtime upgrade or parser/library source
change is included. Draft publication does not close the GitHub alert.
