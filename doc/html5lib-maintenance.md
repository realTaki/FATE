# html5lib: two mapped Dependabot serializer alerts

This independent change updates only `html5lib==0.9999999` to `html5lib==1.1`
in the root requirements. It addresses the real, currently open alerts
[339](https://github.com/realTaki/FATE/security/dependabot/339)
(`GHSA-8f6m-gfq9-g33v`, first patched `0.99999999`) and
[345](https://github.com/realTaki/FATE/security/dependabot/345)
(`GHSA-v9v9-xffq-rwr4`, first patched `0.999999999`). Both are medium severity.
This is a dependency release, not an application sanitizer rewrite or an audit.

## Upstream first

The actual fork parent is `FederatedAI/FATE`. Its known legacy release tags
`v1.2.2` (`06d8c9cc34fd8e0e8b5e56faeacaf99ece5dac3f`) and `v1.4.6`
(`d3db2a3358efc382a42daac6d04c3cfa8ed072a6`) were read first: both still pin
the affected `html5lib==0.9999999`. Neither supplies a repaired pin to reuse.
This does not establish the state of every later FATE branch. The separate
stopped lookup of the later `v1.11.4/python` directory was not retried, and
no whole-upstream synchronization or runtime/framework migration is included.

The replacement is the official unmodified html5lib release. Its wheel SHA256
is `0d78f8fde1c230e99fe37986a60526d7049ed4bf8a9fadbad5f00e22e58e041d`,
verified against the PyPI JSON record. Its metadata includes Python 3.6 and
requires Six >=1.9 plus webencodings. Existing Six 1.17.0 is retained;
webencodings 0.5.1 is already a dependency of the accepted Bleach 3.3.1.
There are no new root pins or changes to other dependencies.

## Focused verification

On the existing CPython 3.12.14, nine offline tests pass without skips:
ordinary document/fragment parsing, Unicode, byte encoding, explicit quoted
attribute serialization, DOM walking, round-trip ElementTree and strict
normal-document parsing. They also verify that the existing Bleach 3.3.1
continues to use its separate bundled html5lib and preserves ordinary clean
and linkify outputs. No library bodies or consumer functions are modified.

The exact old html5lib cannot import on this interpreter because it imports
`Mapping` from `collections`; that baseline attempt is a failure, not a
passing comparison or proof of an application regression. Candidate package
sources and this test (34 Python files) parse under the Python 3.6 grammar;
official metadata supports 3.6, but native Python 3.6 execution was not done.
An initial test used the unrecognized `.test` linkify suffix; the fixture was
corrected to ordinary `example.com`, retaining the initial failed log.

Run the focused tests in a requirements-provisioned environment:

```sh
python fate_flow/tests/test_html5lib_compatibility.py
```

The default-branch tracked Python sources contain no direct `html5lib`
reference. Nevertheless the old-to-new component releases have public API
changes: serializer quotation options now use strings, encoding keywords
changed, and the sanitizer/treewalker API changed. Untracked or external
consumers, optional lxml/Genshi builders, every legacy transitive consumer,
the full FATE unit suite, native 3.6, notebook/browser/server behavior and
deployment have not been accepted by these tests. The deprecated html5lib
sanitizer is not introduced or used here. No exploit fixture, external HTTP,
notebook/config execution or new runtime is needed for the focused tests.

The two alerts remain uncounted until an independently authorized merge and
actual default-branch Dependabot `fixed` receipts. A draft and absent CI are
not a green application CI result. No ready, merge, auto-merge, release,
deployment, settings change or history rewrite is authorized by this patch.

Official component references:
[release](https://pypi.org/project/html5lib/1.1/) and
[changelog](https://html5lib.readthedocs.io/en/latest/changes.html).
