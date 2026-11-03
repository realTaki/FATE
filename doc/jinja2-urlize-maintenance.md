# Jinja2: one mapped Dependabot alert on the supported Python 3.6 line

Only `Jinja2==2.10.1` becomes `Jinja2==2.11.3` in the root requirements.
The original `MarkupSafe==1.0` and every other pin remain unchanged.
The actual medium alert [31](https://github.com/realTaki/FATE/security/dependabot/31)
is `GHSA-g3rq-g295-4j3m` / `CVE-2020-28493`, with first patched version
2.11.3. The publisher's release reduces `urlize` regex backtracking.
This uses that unmodified release, not a custom regex or sanitizer rewrite.

## Fork upstream checked first

Reuse of the previously fetched immutable parent `FederatedAI/FATE` release
files was checked by canonical Git blob hashes. `v1.2.2` / `06d8c9cc` and
`v1.4.6` / `d3db2a33` both still pin Jinja2 2.10.1 / MarkupSafe 1.0.
Neither of these inspected legacy releases supplies a corrected Jinja2 pin.
This is not a statement about all later FATE branches; the separate stopped
`v1.11.4/python` lookup was not retried or rerouted. No whole-upstream sync
or application/runtime migration is included here.

Official Jinja2 2.11.3 wheel SHA256:
`03e47ad063331dd6a3f04a43eddca8a966a26ba0c5b7207a9a9e4e08f1b29419`.
Both original and candidate artifacts and the original MarkupSafe 1.0 sdist
were verified against the official PyPI JSON hashes. Jinja2 2.11.3 declares
Python 3.6 support and still requires only MarkupSafe >=0.23.

## Actual native Python 3.6 validation

On isolated native CPython 3.6.15, the candidate plus the exact unchanged
MarkupSafe 1.0 passes all nine committed tests, zero skips. This was run
separately with its original pure-Python fallback and with its real C
extension: nine passes in each mode. In each corresponding baseline mode,
the eight ordinary checks pass; only the expected patched-version gate
fails. These are ordinary functional controls, not a DoS timing experiment.

Coverage includes normal URL/email linkification, Unicode autoescaping,
trusted Markup, inheritance/includes/macros, loop controls, the retained
contextfilter API, and actual unmodified nbconvert 5.3.1 ANSI functions
calling `jinja2.utils.escape`. The test imports that installed module by
source path to avoid unrelated exporter startup; its functions are not
mocked or rewritten. The official nbconvert wheel and module hashes are
recorded. The C extension was built from the original MarkupSafe C source
using native 3.6 standard-library distutils and the identical extension
name/source listed in its setup.py; this does not certify a complete pip
installation or every setup/frontend combination.

The interpreter is a temporary compiled fixture, not a system or project
runtime change. Official python.org 3.6.15 source bytes match the already
verified SHA256 `6e28d7cdd6dd513dd190e49bca3972e20fcf455090ccf2ef3f1a227614135d91`
and published MD5. The only build-source adjustment is the previously
documented private `sinpi` helper rename to avoid a modern glibc symbol
collision; its function logic is unchanged. Build concurrency is two,
without make install or global pip. Signature-key retrieval was not retried;
the prior signature-verification limitation remains. The fixture build tree
is removed after validation, retaining concise hashes, patch and logs.

An initial host-3.12 attempt with the real MarkupSafe 1.0 failed because its
old `collections.Mapping` import no longer exists there. That is not a
production Python 3.6 failure. MarkupSafe 1.1.1 was briefly probed only to
identify the host limitation; it is neither a production change nor the
acceptance combination. Native testing avoids inventing an unnecessary
second dependency upgrade.

Run on the supported requirements-provisioned environment:

```sh
python fate_flow/tests/test_jinja2_urlize_compatibility.py
```

## Limits and remaining actual alerts

The four separately mapped medium alerts 541 / 557 / 583 / 585 are not
covered: their first patched versions are on the 3.1 line. Jinja2 3.1 drops
Python 3.6 and removes legacy interfaces, including hooks used by old
consumers; 3.1.6 declares Python >=3.7. No blind major upgrade is attempted.

This is not the full FATE or nbconvert suite, a Flask/Notebook server,
browser, external-template sandbox acceptance, model training, deployment,
or proof of whole legacy dependency-graph consistency. No long pathological
input, untrusted template, notebook/config execution or external request is
used in the tests. The observed research dashboard call does not have a
tracked dashboard template, so no live dashboard success is claimed.

The target remains uncounted until a separately authorized merge and actual
default-branch Dependabot fixed receipt. A draft and absent CI are not a
green full-application result. No ready/merge/auto-merge/release/tag/deploy,
settings change or history rewrite is included.

Official references: [release](https://pypi.org/project/Jinja2/2.11.3/) and
[publisher changelog](https://jinja.palletsprojects.com/en/stable/changes/).
