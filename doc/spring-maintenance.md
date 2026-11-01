# Java 8 Spring-family security maintenance

Change the existing shared `spring.version` in `arch/pom.xml` from
**5.1.4.RELEASE to 5.2.22.RELEASE**. This aligns core/beans/context/tx/jdbc/test
and their Spring aop/expression/jcl dependencies on the same Spring 5 release.
All nine official candidate POMs reference matching Spring versions; required
non-optional dependencies remain within that family. Official artifacts were
checked against Maven Central SHA1 sidecars, with SHA256 receipts retained.
Candidate main classes are compatible with Java 8. No Java/runtime upgrade,
Spring 6/Jakarta migration, application configuration or other pin changes.

Exact actual alerts in `arch/pom.xml`:

- [#458 / GHSA-36p3-wjmg-h94x](https://github.com/advisories/GHSA-36p3-wjmg-h94x),
  critical, spring-beans; first fixed in 5.2.20.RELEASE.
- [#543 / GHSA-hh26-6xwr-ggv7](https://github.com/advisories/GHSA-hh26-6xwr-ggv7),
  high, spring-beans; first fixed in 5.2.22.RELEASE.
- [#558 / GHSA-g5mm-vmx4-3rg7](https://github.com/advisories/GHSA-g5mm-vmx4-3rg7),
  high, spring-context; first fixed in 5.2.21.RELEASE.

[Official 5.2.22 documentation](https://docs.spring.io/spring-framework/docs/5.2.22.RELEASE/spring-framework-reference/overview.html)
requires JDK 8+. This is a first-combined-patch candidate, **not** a claim that
this old branch is currently maintained or all Spring vulnerabilities are fixed.
Actual later alerts **#589 / GHSA-4gc7-5j7h-4qph**, **#590 / GHSA-4wp7-92pw-q264**
and **#661 / GHSA-659m-px2c-25wj** remain: later binding locale/bypass and
AntPathMatcher issues are not repaired or silently dismissed here.

## Actual Java 8 verification

Direct javac/JUnit 4.12 compiles unchanged actual project AsyncModelFactory,
DefaultListenableFutureCallBack, ReturnStatusFactory, DelayedResult,
SingleDelayedResult and the actual generated BasicMeta against the **old 5.1
Spring API**, then runs on each complete matching family.

Candidate: **6/6 pass**. Old family: **three normal controls pass and three
expected security-policy failures**. Normal checks execute a real minimal
AnnotationConfigApplicationContext with actual project prototype/@Autowired
beans and callbacks, parse the unchanged original applicationContext-core.xml
with local-only schema resolution (never refresh that production-scanning
context or create its task executors/services), and bind ordinary writable
properties through the real DataBinder API. No synthetic Spring stubs or AST
substitution is used.

Security boundaries check ASCII case-insensitive disallowedFields matching,
exclusion of read-only AutoCloseable properties, and exclusion of concrete
Class.declaredMethods metadata while retaining Class.name. Inherited interface
metadata such as annotations is **not** claimed universally hidden.

Spring4Shell's documented JDK 9+/MVC or WebFlux/Tomcat-WAR exploit conditions
are not reproduced on this actual Java 8 test runtime. The class-descriptor
check is policy evidence only. Likewise, the AutoCloseable check exercises
the corrected introspection mechanism, not a real multipart upload endpoint.
The scoped project review found annotations, bean lookups and Spring XML use,
not DataBinder/MultipartFile/Servlet Part callers. No application remote
exploitability is inferred.

With dependencies available, use Java 8:

```sh
mvn -f arch/core/pom.xml -Dtest=SpringFamilySecurityTest test
```

Maintenance used a 128 MiB heap, 2 MiB stack and 25-second child-process limit;
Log4j JMX is disabled in the test JVM. No external schema/network, production
service, JMX/DB/exploit chain, full Maven dependency convergence/reactor,
gRPC transport, training, deployment or production acceptance was performed.
The actual project XML is parsed only; the entire application context is not
started. A draft is not a merge, CI-green status or actual alert closure.
