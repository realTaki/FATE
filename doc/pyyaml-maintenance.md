# PyYAML security pin while retaining Python 3.6 and the legacy consumer API

This narrow repair updates only `PyYAML==4.2b1` to `PyYAML==5.4.1`, targeting actual Dependabot alerts 646 (GHSA-rprw-h62v-c2w7, first patched5.1) and34 (GHSA-8q59-q68h-6hv4, first patched5.4). Other requirement pins and project runtime remain unchanged.

## Why this version

The official5.4.1 distribution supports Python3.6 and adds no runtime dependencies. Its canonical CPython3.6 Linux wheel was SHA256-verified against official PyPI metadata. FATE's declared Keras2.2.4 dependency requires PyYAML without a version ceiling; the canonical `keras.engine.saving.model_from_yaml` calls `yaml.load(yaml_string)` without a Loader argument. Version5.4.1 retains that call (with its upstream YAMLLoadWarning); moving directly to6 would make Loader mandatory. No FATE-owned Python YAML caller was found in the scoped source lookup.

The selected version repairs these two mapped alerts; this is not a claim of latest-version support or universal YAML safety. Prefer safe loading for new code. This change does not add arbitrary constructors or alter Keras/framework code.

## Actual native validation

Using a real isolated CPython3.6.15 test executable:

- candidate5.4.1:9/9 ordinary API tests pass, zero skips;
- exact official4.2b1 distribution's Python3 library:8 ordinary behavior controls pass; only the explicit5.4.1 version gate fails as expected;
- candidate CP36 native LibYAML extension imports and its C-safe/pure-safe ordinary configuration roundtrips agree.

Coverage includes nested configuration types, Unicode text/byte streams, safe dump/load, the legacy default-loader call with an ordinary Keras-shaped model dictionary and tuple, small configuration merges, multi-document order, bytes/dates, empty and malformed input. No arbitrary-object or code-execution payload was used. Whole Keras/TensorFlow model construction, training and full FATE application acceptance were not run.

The beta distribution's package constant reports `yaml.__version__ == '4.2'`; its identity is the official4.2b1 source archive and checksum, not a substituted stable release. Baseline testing uses its canonical Python3 library and makes no baseline optional-C-extension build claim. The default consumer APIs exercised are Python loaders; the candidate's optional C wheel was additionally verified.

The test-only interpreter reuses the retained official Python3.6.15 source archive, a private math-helper rename required by current glibc, and recorded source-unchanged `-O0 -g0` host compiler flags. It is not installed as the system or project runtime. Commands, official artifact hashes, native version, logs and source/consumer provenance are preserved in the maintenance receipt.

With the project dependency installed, run:

```sh
python -s -B fate_flow/tests/test_pyyaml_compatibility.py -v
```
