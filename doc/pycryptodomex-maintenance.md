# Python 3.6-compatible pycryptodomex maintenance

Pin `requirements.txt` from **pycryptodomex 3.6.6 to 3.19.1**, the first patched
release mapped to [Dependabot #540 / GHSA-j225-cvw7-qrx7](https://github.com/advisories/GHSA-j225-cvw7-qrx7).
This is a dependency-only production change: it does not change RSA parameters,
FATE encryption/protocol behavior, or the declared Python 3.6 runtime. It is not
an audit or redesign of FATE's cryptography.

[Official release metadata](https://pypi.org/pypi/pycryptodomex/3.19.1/json)
includes Python 3.6 support, keeps the `Cryptodome` namespace, and declares no
additional runtime dependencies. The selected Linux x86-64 wheel is
`pycryptodomex-3.19.1-cp35-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl`;
its published SHA-256 is
`96000b837bcd8e3bf86b419924a056c978e45027281e4318650c81c25a3ef6cc`.
The baseline is the official 3.6.6 `cp36-cp36m-manylinux1_x86_64` wheel, SHA-256
`34b3218fcdcd59c26de75c4ff8a15e6472e7b88f9e5b3b193cb1c001e7a0e815`.
Both downloaded artifacts matched their exact published PyPI hashes.

## Actual native Python 3.6 checks

Maintenance reconstructed the previously retained official CPython **3.6.15**
source fixture (SHA-256
`6e28d7cdd6dd513dd190e49bca3972e20fcf455090ccf2ef3f1a227614135d91`).
The isolated GCC 14.2.0 build used `--without-ensurepip` and `make -j2`, without
PGO, `make install`, global pip, OS package installation, or default interpreter
changes. Only the already-recorded private `sinpi` to `_Py36_sinpi` C-helper
rename was applied to avoid the current glibc name collision; its math logic
is unchanged. No Python-version alias, stdlib shim, or application patch was used.
After the initial default-optimization build exposed the host-tool limitation
below, the same tree was cleaned and rebuilt once with `CFLAGS='-O0 -g0'`.
The effective flags end with `-O0 -g0`, overriding configure's earlier `-O3`.
No additional source changes were made; this changes only the temporary test
tool's compiler configuration, not FATE or its production runtime.
This EOL interpreter is a temporary compatibility fixture, not a production
runtime recommendation. Its normal math, ctypes, struct, binascii, hashlib,
JSON, and SSL imports were probed; this is not complete CPython acceptance.

The exact focused test is:

```sh
python3.6 -s -B fate_flow/tests/test_pycryptodomex_rsa_compatibility.py
```

Use an isolated dependency path containing the selected official wheel and
FATE's existing `cffi==1.11.5` and `pycparser==2.19` pins. Their official wheel
and sdist respectively were hash-verified and extracted locally, not installed
globally. Both Cryptodome versions automatically selected their real upstream
CFFI backend; the test asserts it rather than forcing or mocking a backend.

**Nine tests pass, with zero failures or skips, on both 3.6.6 and 3.19.1** using
actual native CPython 3.6.15 (three initial CFFI runs and one final rebuilt-tool
run per version, with identical focused test bytes). They cover:

- the real `Random.new().read` callback and `RSA.generate` imports;
- unchanged FATE `RsaEncrypt.generate_key` default 1024-bit and explicit
  2048-bit generation, with its actual `.e`, `.d`, and `.n` consumption;
- actual key tuple getters/setters and uninitialized/list behavior;
- ordinary integer round trips using the generated tuple as an independent
  mathematical control;
- real library key reconstruction, memory-only PEM export/import, and an
  ordinary valid-ciphertext OAEP encrypt/decrypt round trip;
- the existing declared CFFI dependency/backend versions.

Only ephemeral synthetic keys and ordinary messages are used. No private key
is written to disk, and no credentials, network, signing, malformed-ciphertext,
timing, side-channel, oracle, or exploit test is involved. The valid OAEP round
trip is a compatibility smoke test, not proof that the advisory is reproduced
or that FATE uses OAEP.

## Deliberate scope and observed fixture limitation

The focused loader compiles the **unchanged AST nodes** for the actual
`Encrypt` and `RsaEncrypt` classes plus their actual Cryptodome imports from
`federatedml/secureprotol/encrypt.py`. It does not import that whole module's
unrelated NumPy/Paillier/affine dependency graph. No methods, math functions, or
`sys.modules` entries are replaced. Keyed FATE `RsaEncrypt.encrypt/decrypt`
calls through `gmpy2` are **not** covered; their independent tuple control must
not be described as execution of those wrappers. The existing gmpy2 pin and all
production class source remain unchanged.

An exploratory run without FATE's declared CFFI dependencies hit a native
CPython 3.6/GCC `ctypes._reset_cache` segmentation fault on baseline import,
before the focused tests. This resembles the known upstream
[CPython issue 89863](https://github.com/python/cpython/issues/89863).
The initial failure logs are retained, not counted as a package regression
test failure or silently hidden. The source-unchanged `-O0 -g0` rebuild then
passed an ordinary ctypes import/callback check and the original focused test
on both versions. No import reordering or additional runtime source patch was
used. The project acceptance above still uses the actual already-declared
CFFI backend, explicitly asserted for both versions. This is not a full ctypes
or CPython test-suite qualification.

Full FATE requirements installation, the complete application/module import,
training, services, deployment, and the full CPython suite were not run. Other
requirements and existing maintenance pins are not changed by this patch.
External offline deployment wheelhouses must separately provide the chosen
artifact; this PR does not modify or deploy one. CI and Dependabot closure must
be checked on the exact published head; a draft PR alone does not close #540.
