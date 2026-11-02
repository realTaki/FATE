# Mapped Bleach sanitizer update

This narrow change covers the existing FATE Dependabot alerts:

- **#6**, high, GHSA-vqhp-cxgc-6wmm, first patched in3.1.4.
- **#3/#5/#30**, medium, first patched in3.1.1/3.1.2/3.3.0.

Use **Bleach3.3.1**, a3.3 maintenance patch retaining the old `styles` and
`ALLOWED_STYLES` interfaces required by the declared nbconvert5.3.1.
Only the Bleach pin, a necessary Six1.10.0→1.17.0 companion pin, this document
and one focused test are changed. No Jupyter/nbconvert framework upgrade or
application sanitization-policy edit is included.

## Real validation

The existing CPython3.12 interpreter runs the complete original Bleach3.3.1
component and the exact nbconvert5.3.1 `utils/base.py`, `preprocessors/base.py`
and `preprocessors/sanitize.py` modules, with unchanged traitlets4.3.2,
ipython-genutils0.2.0 and decorator4.3.0. Those three consumer files are hash
checked and loaded in a private package namespace only to avoid unrelated
exporter startup; no functional class/body is substituted or changed.

Candidate **10/10, zero skips**: ordinary allowed/escaped/stripped markup,
Unicode, comments, HTTPS attributes, short ordinary CSS allowlists, linkify,
the actual raw/markdown/output sanitizer, enabled preprocessing dispatch and
the real traitlets-configured `styles` call. No malicious XSS/regex input,
DoS workload, browser, remote request or notebook/code execution is used.
Synthetic cell/output containers supply only the normal input data contract;
all filtering is performed by the real consumer and Bleach.

The exact old Bleach1.5.0/html5lib0.9999999/Six1.10 combination cannot import
under the existing3.12 because `six.moves` uses the old importer protocol.
The first3.3.1 attempt with unchanged Six has the same issue. Updating only
the normal Six companion to1.17.0 resolves this without a library shim or
new interpreter. The baseline import failure is retained, **not a passing
baseline or a reproduction of the security advisory**. Existing traitlets
SyntaxWarnings and deprecation warnings are retained. No native3.6/full
FATE/notebook server/browser/Windows acceptance is claimed.

## Dependency and remaining-scope disclosure

Bleach3.3.1 itself supports Python2.7 or>=3.5; Six1.17 retains its legacy
Python support. Bleach now uses its bundled html5lib parser and declares
mandatory `packaging`, `webencodings`, and `six>=1.9` dependencies. The test
fixtures are official packaging22.0 and webencodings0.5.1 (plus the pins above);
packaging22 requiresPython>=3.7, below the existing root IPython8.10>=3.8
constraint. They are ordinary transitive packages, not new frameworks/tools.
No new root pin for these transitives, global installation, interpreter or
whole-legacy-graph coherence claim is made. The separate old html5lib pin is
left unchanged; this is not acceptance of all unrelated consumers of it.

**#640 (medium) and #639 (low) remain uncovered**. Their first patch is6.4.0,
which requiresPython>=3.10 and removes `ALLOWED_STYLES` / the `clean(styles=)`
interface used by this original consumer, replacing it with `css_sanitizer`.
That route needs an explicit coherent runtime and consumer CSS-policy change;
the6.4 release was inspected as metadata/source only, not installed/executed.
This PR must not be represented as all Bleach alerts closed or blind-promoted
to6.4. No actual alert is counted fixed until default-branch platform evidence
confirms it after a separately authorized merge.

## Reproduce the applicable component checks

With the declared nbconvert5.3.1 and original traitlets stack, candidate
Bleach3.3.1/Six1.17.0 and the transitive fixtures available:

```sh
python fate_flow/tests/test_bleach_compatibility.py
```

Only normal source/draft publication is intended. No merge, deployment,
release, scan setting, account change or history rewrite is included.
