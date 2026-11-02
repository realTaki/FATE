# Jupyter core: mapped high alert #428

Change only `jupyter-core==4.4.0` → `jupyter-core==4.11.2`, the first patched
version for [GHSA-m678-f26j-3hrp](https://github.com/advisories/GHSA-m678-f26j-3hrp).
The security change removes implicit trust of the current working directory
from `JupyterApp.config_file_paths`. Trusted explicit configuration directories
and search paths remain available. No production source or config is changed.

## Compatibility and runtime boundary

The candidate stays4.x and its only default Linux dependency is traitlets.
The exact existing traitlets4.3.2, ipython-genutils0.2.0, decorator4.3.0 and
six1.10.0 are retained and used in the tests; no traitlets/framework upgrade or
new runtime package is included. The pinned Notebook5.7.8, jupyter-client5.2.3
and jupyter-contrib-core0.3.3 metadata accept4.11.2. Verified Notebook5.7.8
source inherits JupyterApp and does not override config_file_paths.

**4.11.2 requires Python>=3.7 and is not a Python3.6 package.** The current
manifest already pins IPython8.10.0, which requires Python>=3.8, so this does not
raise the existing overall manifest constraint or install/change an interpreter.
It does not claim that the complete legacy manifest is coherent, nor acceptance
for a separate deployment still requiring Python3.6. That deployment condition
must not be hidden behind the old README or this component's successful tests.

## Real applicable validation

Using the existing CPython3.12.14, both original and candidate full JupyterApp
classes import and instantiate with those exact original transitive pins.
Candidate:7/7 pass, zero skips. Baseline:3 pass/4 fail; failures are the patched
version gate, observed default-CWD/config-priority behavior, and4.4's missing
explicit JUPYTER_CONFIG_PATH behavior. They are not four exploit reproductions.
Old traitlets SyntaxWarnings remain recorded for both versions.

Tests exercise the real JupyterApp property, explicit trusted-CWD/config-dir
behavior and public config/data/runtime/search-section APIs. All paths are
private temporary test directories with an empty HOME; no config file is loaded
or executed and no notebook/server/subprocess service is started. No library
shim, runtime rebuild, user account setting or source API migration is used.
These are complete affected-component tests, not a full notebook/FATE service,
Windows, live deployment or arbitrary-code-execution payload test.

```bash
python fate_flow/tests/test_jupyter_core_compatibility.py
```

A workflow depending on implicit CWD configuration should explicitly name its
trusted config directory/search path rather than re-enable implicit CWD trust.
No default Jupyter config file was found among this repository's named paths.

Official wheel SHA256:

- 4.4.0: `927d713ffa616ea11972534411544589976b2493fc7e09ad946e010aa7eb9970`
- 4.11.2: `3815e80ec5272c0c19aad087a0d2775df2852cfca8f5a17069e99c9350cecff8`

Existing security pins and independent drafts are unchanged. Publication/test
success is not actual alert closure; check the default-branch alert state after
a separately authorized merge. No deployment, release or scan-setting change
is part of this patch.
