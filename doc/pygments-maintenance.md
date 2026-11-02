# Pygments: minimal patch for two mapped high alerts

`requirements.txt` changes only `Pygments==2.2.0` → `Pygments==2.7.4`.
This is the first patched version for the repository's real high alerts
[#33](https://github.com/realTaki/FATE/security/dependabot/33) and
[#36](https://github.com/realTaki/FATE/security/dependabot/36):

- [GHSA-pq64-v7f5-gqh8](https://github.com/advisories/GHSA-pq64-v7f5-gqh8)
- [GHSA-9w8r-397f-prfh](https://github.com/advisories/GHSA-9w8r-397f-prfh)

The candidate remains2.x, supports Python>=3.5 and adds no runtime dependency.
No interpreter/framework, notebook configuration, lexer implementation or
application source is changed. Existing pycryptodomex/PyYAML and other accepted
security pins are retained; the separate psutil draft is not included.

## Applicable checks

The FATE Python source has no direct Pygments call; the pinned notebook tools
are its relevant declared consumers. Ordinary tests cover real Python/SML/Java/
JSON token streams, HTML escaping/style output, the actual nbconvert5.3.1
highlighting helper (HTML/magic-language override/plain-text fallback/LaTeX),
and the actual IPython8.10.0 lexer leaf. These leaves are loaded from verified
official package sources without starting unrelated notebook/interactive
services. Upstream files are not rewritten or copied into the production tree.

Using the existing CPython3.12.14:

- Candidate2.7.4:7/7 pass, zero skips.
- Baseline2.2.0:6 ordinary checks pass; only the explicit patched-version gate
  fails. Old-source SyntaxWarnings are retained in the local logs.

Inputs are short ordinary source examples, not crash, malformed-regex,
infinite-loop or resource-exhaustion payloads. These are API/consumer checks,
not an exploit reproduction, native Python3.6 execution, or a full FATE/Jupyter
environment acceptance.

Official wheel SHA256 values used for this check:

- Pygments2.2.0: `78f3f434bcc5d6ee09020f92ba487f95ba50f1e3ef83ae96b9d5ffa1bab25c5d`
- Pygments2.7.4: `bc9591213a8f0e0ca1a5e68a479b4887fdc3e75d0774e5c71c31920c427de435`
- nbconvert5.3.1: `260d390b989a647575b8ecae2cd06a9eaead10d396733d6e50185d5ebd08996e`
- IPython8.10.0: `b38c31e8fc7eff642fc7c597061fff462537cf2314e3225a19c906b7b0d8a345`

With those declared consumer sources and the chosen Pygments on PYTHONPATH:

```bash
python fate_flow/tests/test_pygments_compatibility.py
```

## Explicit remaining scope

This patch does **not** cover existing medium#521 (first patch2.15.0) or low#623
(first patch2.20.0). Their published Python floors are3.7 and3.9 respectively.
The current manifest already pins IPython8.10.0 (Python>=3.8,
Pygments>=2.4.0, traitlets>=5) alongside traitlets4.3.2. Thus old Python3.6
documentation is not evidence of a coherent current full dependency graph;
this patch neither raises that existing overall floor nor resolves the
pre-existing notebook constraints.

A separate2.15.1 qualification passed six cases, but unknown-language plugin
discovery imported the whole IPython package and encountered a missing
pickleshare test dependency. That is an incomplete fixture, not proof that
2.15.1 is incompatible or an authorization failure. The higher-version/plugin
path still needs coherent consumer-dependency validation; it is not silently
included or marked ready here. No notebook/runtime migration was attempted.

Draft publication or a successful test does not close an alert. Verify the
actual default-branch alert states after a separately authorized merge.
