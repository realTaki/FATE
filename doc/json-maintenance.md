# Java 8-compatible JSON parser maintenance

Pin `org.json:json` in `arch/core/pom.xml` from **20151123** to **20231013**.
The exact open alerts are [#501 / GHSA-3vqj-43w4-2q58](https://github.com/advisories/GHSA-3vqj-43w4-2q58)
(first fixed in 20230227) and [#539 / GHSA-4jq9-2xhw-jpx7](https://github.com/advisories/GHSA-4jq9-2xhw-jpx7)
(first fixed in 20231013). This updates the same coordinate without changing
Java, a service runtime, another dependency or a configuration setting.

The [official release POM](https://raw.githubusercontent.com/stleary/JSON-java/20231013/pom.xml)
targets Java 8 and declares only test-scope dependencies. The official candidate
JAR has class major version 52 and SHA-256
`0f18192df289114e17aa1a0d0a7f8372cc9f5c7e4f7e39adcf8906fe714fa7d3`.
Both old and candidate JARs were checked against Maven Central SHA1 sidecars;
local SHA256 and original-source hashes were retained in maintenance receipts.

## Actual application boundary

The scoped Java source review found `Configuration.loadOtherConf` as the only
`org.json` import/call site: it reads UTF-8 adapter JSON into `JSONObject` and
returns stored objects. No XML conversion caller was observed in this scope.
No remote exploitability or use of every library feature is inferred.

The focused test compiles the **unchanged actual Configuration and StatusCode
sources** and the test against the original JSON API using Java 8. It verifies
ordinary UTF-8/nested/array/boolean/numeric/null values and a semantic JSON
round trip through the actual file-loading path. Malformed configuration keeps
the existing `UNKNOWNERROR` status. These two controls pass on both versions.

Two bounded library checks cover embedded-NUL/object-key parser shapes from
CVE-2023-5072 and a 1024-element-deep XML nesting limit. The candidate passes
**4/4 tests**. The old version has **one expected failure**: it accepts XML
nesting beyond the candidate's limit. The old version already rejects the
small embedded-NUL and depth-3 advisory-shaped inputs tested here; this is
**not** a reproduction of #539 on the old project pin. The candidate also
rejects those inputs. No exponential-memory proof of concept is executed.

Run with Java 8:

```sh
mvn -f arch/core/pom.xml -Dtest=JsonConfigurationSecurityTest test
```

Maintenance used direct Java 8 javac/JUnit 4.12, a 96 MiB heap, 4 MiB stack and
20-second child-process limit. Fixtures are tiny fixed strings and synthetic
temporary files, not real configuration data. No FATE service, network, model,
database or training is started by these tests.

This is not full Maven/reactor/core/service/native/packaging/deployment or
production acceptance. Exact numeric implementation classes, output key order
and all historical permissive parser behavior are not guaranteed identical.
The project sources and parser configuration remain unchanged. A candidate PR
is not an actual alert closure; GitHub must independently report `fixed` after
an explicitly approved merge.
