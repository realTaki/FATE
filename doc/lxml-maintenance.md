# lxml: four mapped medium alerts on the legacy API line

Only `lxml==4.2.5` becomes `lxml==4.9.4` in the root requirements.
No other pin, parser policy, application code or runtime is changed.
The four actual Dependabot targets remain open until an authorized merge
and independent default-branch fixed receipts:

| Alert | Advisory | First patched version |
| --- | --- | --- |
| [29](https://github.com/realTaki/FATE/security/dependabot/29) | GHSA-pgww-xf46-h92r / CVE-2020-27783 | 4.6.2 |
| [32](https://github.com/realTaki/FATE/security/dependabot/32) | GHSA-jq4v-f5q6-mjqq / CVE-2021-28957 | 4.6.3 |
| [253](https://github.com/realTaki/FATE/security/dependabot/253) | GHSA-55x5-fj6c-h6m8 / CVE-2021-43818 | 4.6.5 |
| [344](https://github.com/realTaki/FATE/security/dependabot/344) | GHSA-wrxv-2j5q-m38w / CVE-2022-2309 | 4.9.1 |

The first three concern HTML Cleaner handling. Alert344 concerns particular
parser/iterwalk sequences with libxml2 2.9.10 through 2.9.14. This change
uses the publisher's unmodified maintenance release, not a custom cleaner
patch or a generalized audit.

## Fork upstream checked first

The actual parent is FederatedAI/FATE. Previously fetched immutable legacy
`v1.2.2` / `06d8c9cc` and `v1.4.6` / `d3db2a33` root requirements were
rechecked by canonical Git blob and SHA256: both still pin lxml4.2.5.
Neither inspected release supplies a corrected pin. This does not establish
the state of all later upstream branches. The separately stopped
`v1.11.4/python` lookup was not retried or rerouted, and no whole-upstream
or framework/runtime migration is included.

Official 4.9.4 metadata retains Python 3.6 and supplies cp36 wheels.
It has no new mandatory runtime dependency; listed additions are extras.
The tested official artifact is
`lxml-4.9.4-cp312-cp312-manylinux_2_28_x86_64.whl`, SHA256
`e8f9f93a23634cfafbad6e46ad7d09e0f4a25a2400e4a64b1b7b7c0fbaa06d9d`,
verified against PyPI JSON. Its native backend reports libxml2 2.10.3 and
libxslt 1.1.39. Other Python/platform wheels and system-library builds may
use different native libraries and were not executed here.

## Focused checks and actual limits

On the existing CPython 3.12.14, all 15 committed ordinary in-memory tests
pass, zero skips. They cover Unicode/namespaced XML and XPath,
serialize/reparse, HTML fragments and normal links, retained Cleaner and
forms options, explicit-offline iterparse, iterwalk, canonical serialization
using `tostring(method="c14n")`, ordinary parser recovery/reuse, objectify,
XSLT and schema checks. Three additional integration paths within those
15 tests exercise the current unmodified html5lib1.1 optional lxml builder,
walker and serializer with existing Six1.17/webencodings0.5.1.
No new dependency pin or closed-alert test run is required for that new
backend combination.

The test plus 28 available Python package files pass Python 3.6 grammar.
That is syntax evidence only: native Python 3.6 and the cp36 extension were
not executed, and no legacy interpreter was rebuilt. The old lxml4.2.5 has
no official cp312 wheel, so it was not run on this host. No baseline pass,
failure, or old-versus-new behavioral comparison is claimed.

The exact default branch has no direct tracked Python lxml references.
That does not exclude transitive or external consumers. These are component
smoke checks, not full FATE or deployment acceptance, tracked application
consumer tests, browser/server behavior, or exploit regressions. The
ordinary incomplete-document reuse case is not the exact alert344 crash
sequence. No long malformed input, active browser content, external entity,
file/network fetch, notebook/config execution or new runtime is used.
Explicit parser/XSLT resource controls apply only to the test fixtures.

The changelog notes behavior corrections since 4.2.5, including stricter
Cleaner option validation, attribute ordering, iterwalk events and objectify
numeric handling, plus different bundled native libraries. Universal
drop-in behavior or whole-legacy-dependency-graph consistency is not claimed.

Run with the root requirements available:

```sh
python fate_flow/tests/test_lxml_compatibility.py
```

## High627 remains uncovered

[Alert627](https://github.com/realTaki/FATE/security/dependabot/627),
GHSA-vfmq-68hx-4jfw / CVE-2026-41066, is still open. Its first fixed
version is6.1.0, requiring Python >=3.8. It concerns vulnerable defaults in
`iterparse()` and `ETCompatXMLParser()`. Explicit safe settings in these
test fixtures do not change those application defaults or close the alert.
A coherent runtime/consumer route or an applicable explicit application
policy needs separate qualification, not a blind major pin here.

This remains a draft pending its own concrete merge decision. No ready,
merge, auto-merge, release, tag, deployment, settings or history rewrite is
included. Missing CI is not a full-application green result.

Official references: [release](https://pypi.org/project/lxml/4.9.4/) and
[changelog](https://lxml.de/4.9/changes-4.9.4.html).
