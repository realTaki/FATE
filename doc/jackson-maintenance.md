# Jackson 2.x Java 8 security maintenance

## Scope and alignment

Change only `arch/core/pom.xml`'s shared `jackson.version` from `2.12.7.1`
to `2.18.11`. This selects published `jackson-annotations` and
`jackson-databind` 2.18.11; databind's transitive `jackson-core` is also
2.18.11. The official BOM agrees on these three versions. Their POMs and
JARs exist on Maven Central, verified against its SHA-1 files with local
SHA-256 receipts. The family has no other required runtime dependencies.
The official Jackson parent declares Java 8 source/target; all three JARs'
main classes have class-file versions at most 52. There is no coordinate,
Java/runtime, framework, application API, or serialization-policy migration.

This is the minimum combined 2.18 patch for the mapped high group, not a
claim to be the latest release (2.18.12 also exists):

| Alert | Severity | Advisory | First patched in this line |
| --- | --- | --- | --- |
| 690 | high | GHSA-rmj7-2vxq-3g9f | 2.18.8 |
| 689 | high | GHSA-j3rv-43j4-c7qm | 2.18.8 |
| 680 | high | GHSA-wv8q-qhhj-9h54 | 2.18.11 |
| 679 | high | GHSA-cxp5-3px4-pw24 | 2.18.11 |

The same version is outside the current vulnerable ranges of the seven
mapped medium alerts: 691/GHSA-gx83-3vf8-gh7j (2.18.10),
688/GHSA-3wrr-7qpf-2prh (2.14.0), 686/GHSA-5gvw-p9qm-jgwh (2.18.9),
678/GHSA-vvgp-rfg2-7rr6 (2.18.9), 677/GHSA-wjgm-6hv5-3cvf (2.18.10),
642/GHSA-hgj6-7826-r7m5 (2.18.8), and 641/GHSA-5jmj-h7xm-6q6v
(2.18.9). These are advisory-range observations, not seven reproduced
exploits or GitHub alert closures. All 11 were open on the default branch
at verification; a draft does not fix default-branch alerts.

## Real, bounded Java 8 validation

`JacksonFamilySecurityTest` compiled and ran with Temurin 1.8.0_504,
JUnit 4.12, the complete coherent three-JAR candidate family, and the
unchanged production `GeneralJsonStringSerDes`, `GeneralJsonBytesSerDes`,
`BaseSerDes`, `SerDes`, `ReturnResult`, `ObjectTransform`, and
`ExceptionConstants`. No replacement production stubs or AST-only execution.
Existing Log4j 2.25.5, Spring 5.1.4 annotation classes and Commons Lang 3.8.1
provide the unchanged surrounding API dependencies.

Eight tests passed:

- Actual string/byte serializers retain a representative typed JSON wire
  fixture, UTF-8, null omission, comments, ignored unknown fields, null and
  invalid transport/malformed-input contracts.
- Actual `ReturnResult` and `ObjectTransform` perform ordinary JSON
  serialization/deserialization.
- A restrictive PTV rejects a denied concrete type nested in an allowed
  generic container and in an allowed array shape. Only inert test-local
  DTOs are involved; denied constructors do not run. An allowed String array
  still works. No gadget, command, JNDI, JDBC, or exploit chain is exercised.
- After 1,100 short unknown name IDs select a fallback, 100 remain cached
  (maximum permitted: 1,000); repeated-ID control still works.
- A shallow document under 4 KiB with 64 reverse-order forward references
  retains order and identity, using 64 ID comparisons (budget: 512), not
  timing-based or large-payload DoS testing.

The JVM is bounded to 128 MiB heap, 2 MiB stack and a 30-second process
limit. Log4j JMX is disabled in the local harness. The fixtures request no
network, DNS, filesystem provider, production service, or database effects.
The DNS/InetAddress/Path and other medium advisories were not dynamically
reproduced.

### Original baseline resolution is broken, not passed

The literal current POM asks for `jackson-annotations:2.12.7.1`. Its official
Maven Central POM URL returns HTTP 404, while databind 2.12.7.1 exists. Thus
the original whole Jackson graph cannot be claimed to resolve, compile or
pass. The candidate removes that particular missing-artifact problem.

A separately labelled, **nonliteral diagnostic** used published annotations
2.12.7 and core 2.12.7 with databind 2.12.7.1. It is not a replacement POM
change and not acceptance of the original dependency graph. Its four normal
project controls passed, but all four security assertions failed as
expected: generic/array allowlist bypass, 1,100 retained IDs and 2,144 ID
comparisons. The same representative typed wire fixture works in this
published old-family diagnostic and the candidate.

## Boundaries and remaining risk

The project's deprecated `enableDefaultTyping` calls remain unchanged and
permissive. Upgrading the library does **not** create an application-specific
type allowlist or make arbitrary untrusted polymorphic JSON safe. The PTV
regressions demonstrate fixed restrictive-validator mechanisms, not that
FATE's current mapper configuration enforces those restrictions. No
project name-based fallback or identity-annotated model was found in the
scoped Jackson usage; library-level regression is not proof of reachable
application exploitation.

New Jackson parser constraints and POJO introspection may affect untested
large/deep/custom models. Representative wire/API compatibility is tested,
not every persisted object or remote peer. Replacing permissive typing or
changing wire policy needs a separate deliberately designed change.

This is real targeted Java 8 project-source/API validation, **not** a full
Maven/reactor, complete core application, Spring/gRPC, database, native,
training, deployment, or all-advisory acceptance result. No changes to
credentials, permissions, deployment, runtime support, other dependency
pins or existing security fixes. GitHub CI state must be reported as
observed, not inferred from local tests. Merge remains separately decided.

## Official references

- [Jackson 2.18 release/compatibility](https://github.com/FasterXML/jackson/wiki/Jackson-Release-2.18)
- [Databind JDK requirements](https://github.com/FasterXML/jackson-databind/tree/2.18#jdk)
- [Official 2.18.11 BOM](https://repo.maven.apache.org/maven2/com/fasterxml/jackson/jackson-bom/2.18.11/jackson-bom-2.18.11.pom)
- [Official databind POM](https://repo.maven.apache.org/maven2/com/fasterxml/jackson/core/jackson-databind/2.18.11/jackson-databind-2.18.11.pom)
