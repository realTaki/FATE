# Java 8-compatible Commons Lang and JUnit maintenance

This changes only the existing versions in `arch/pom.xml`:

| Dependency | Before | After | Exact open alert |
| --- | --- | --- | --- |
| `org.apache.commons:commons-lang3` | 3.8.1 | 3.18.0 | [#595 / GHSA-j288-q9x7-2f5v](https://github.com/advisories/GHSA-j288-q9x7-2f5v), first patched 3.18.0 |
| `junit:junit` | 4.12 | 4.13.2 | [#409 / GHSA-269g-pwp5-87pp](https://github.com/advisories/GHSA-269g-pwp5-87pp), first patched 4.13.1 |

JUnit is **not test-scoped in this project**: the inherited parent dependency
has no `<scope>`, so Maven defaults to compile scope and Dependabot reports
runtime scope. This patch deliberately preserves that declaration and does not
introduce JUnit 5, scope changes or a test-framework migration.

## Official artifacts and dependency boundary

The [Commons Lang 3.18.0 POM](https://repo.maven.apache.org/maven2/org/apache/commons/commons-lang3/3.18.0/commons-lang3-3.18.0.pom)
declares source/target 1.8 and only test dependencies. Its main classes are
Java 8 bytecode (major 52). The [JUnit 4.13.2 POM](https://repo.maven.apache.org/maven2/junit/junit/4.13.2/junit-4.13.2.pom)
retains Hamcrest Core 1.3 as its sole non-test dependency; its main classes are
major 49, compatible with Java 8. Downloaded old/candidate Commons Lang and
candidate JUnit artifacts and candidate POMs were checked against official
Maven Central SHA1 sidecars, with SHA256 receipts retained outside the source
tree. No other dependency version, runtime, protocol or application source is
changed. This direct-artifact check is not full dependency convergence.

## Actual ordinary regressions

`LangJunitCompatibilityTest` adds nine offline tests:

- Real `FederatedRoles`, `FederatedUtils` and `SceneUtils`: sorted/deduplicated
  party identifiers, null/empty conventions, separators and ordinary Unicode.
- Real `MultipleRuntimeThrowables`: ordinary exception diagnostics.
- Real `RetryerBuilder`/`Retryer`: blank and duplicate descriptions, normal
  success and one immediate retry of a synthetic IOException.
- Existing StringUtils predicate semantics for null, blank and ordinary values.
- JUnit TemporaryFolder file/directory creation and cleanup after both success
  and a synthetic exception, using only files created by the test itself.

The check also executes five existing tests unchanged: all three
`MysqlConnectorSecurityTest` JDBC metadata tests (no connections), and only
`actualConfigurationPreservesUtf8AndOrdinaryJsonValues` plus
`actualConfigurationRetainsMalformedJsonErrorStatus` from
`JsonConfigurationSecurityTest`, exercising its actual TemporaryFolder rule
and real `Configuration` source. The other JSON security fixtures are not run
by this maintenance check.

Direct `javac` under retained Temurin Java **1.8.0_504** compiles the real utility,
exception, configuration and retry sources and tests against original Commons
Lang 3.8.1/JUnit 4.12. The same classes then pass **14/14 tests** with each of:
original pair, Lang-only upgrade, JUnit-only upgrade and both upgraded. The
candidate reuses the project's unchanged Guava 27.0.1-jre, Log4j 2.25.5,
org.json 20231013, MySQL Connector/J 8.2.0 and Hamcrest Core 1.3.

With a complete project build environment, the new test is runnable with:

```sh
mvn -f arch/core/pom.xml -Dtest=LangJunitCompatibilityTest test
```

These are focused direct Java 8 checks, not a full Maven/reactor, CI-green or
all-module/service acceptance claim. Maven is unavailable in the maintenance
environment; the separate existing Jackson annotations coordinate and absent
eggroll module also remain outside this patch. No vulnerability/DoS payload,
network service, database, training, native library, packaging or deployment
test was performed. A draft PR does not close default-branch alerts.
