# Guava JRE security maintenance on Java 8

## Change and dependency boundary

Update only the inherited `arch/pom.xml` property from **27.0.1-jre to
33.7.2-jre**, plus one focused test and this note. The numeric gap spans
multiple Guava releases; this is not assumed compatible merely because
both JARs use Java 8 bytecode. No FATE source API, gRPC/protobuf version,
wire protocol, JRE edition, runtime support, or framework migration is made.

The official 33.7.2 release explicitly publishes `33.7.2-jre` separately
from `33.7.2-android` and documents the native-deserialization allocation
fix. Keep the **JRE** edition. Official POMs, JARs and source JAR exist on
Maven Central; their published SHA-1 checksums and local SHA-256 receipts
were verified. All main classes in Guava and its five direct Maven
transitive artifacts are Java 8 compatible (class version <=52).

The transitive changes are explicit, not hidden:

| Direct dependency | 27.0.1-jre | 33.7.2-jre |
| --- | --- | --- |
| failureaccess | 1.0.1 | 1.0.3 |
| listenablefuture empty conflict-avoidance JAR | 9999.0-empty-to-avoid-conflict-with-guava | unchanged |
| jspecify | absent | **1.0.1 added** |
| error_prone_annotations | 2.2.0 | 2.50.0 |
| j2objc-annotations | 1.1 | 3.1 |
| jsr305 / checker-qual / animal-sniffer-annotations | direct Guava dependencies | no longer Guava-direct |

These entries have Maven compile scope, not optional scope. Upstream
documents failureaccess as the additional runtime implementation dependency;
the other nonempty additions/updates are annotation artifacts. Existing
gRPC 1.16.1 still declares jsr305 3.0.2, required by project annotations.
This is a targeted direct-dependency/POM and actual classpath check, not a
claim that the entire FATE Maven graph was resolved or built.

## Exact mapped alerts

- **#692 high / GHSA-xxph-c9ww-hj94**: native Java deserialization can use
  an untrusted declared size to preallocate storage in CompactHashMap,
  CompactHashSet and MapMakerInternalMap. First patched release: 33.7.2;
  the official JRE artifact is 33.7.2-jre.
- **#536 medium / GHSA-7g45-4rm6-3mm3** and
  **#535 low / GHSA-5mg8-w23w-74h3**: temporary-file/directory permissions.
  GitHub reports first `32.0.0-android`; the advisory describes the 32.0.0
  fix and recommends 32.0.1 because of Windows regressions. This does not
  instruct a JRE application to switch to Android. The 33.7.2-jre candidate
  retains the JRE flavor and includes those fixes.

All three alerts were still open on the default branch at verification.
A draft, local pass or version-range match is not an alert closure.

## Executable, bounded Java 8 evidence

Temurin 1.8.0_504 compiled **31 complete unchanged production retry/pipe
sources** and six actual project protobuf sources against the old Guava
27 API. It ran the candidate with all five declared direct transitive
artifacts, unchanged protobuf 3.6.1, and unchanged gRPC 1.16.1 modules.
No production stubs or AST-only execution. The original nine JUnit 4.12 tests passed. A later same-branch update adds
three real in-process RPC lifecycle tests: the current aggregate `Enclosed`
run passes **12/12**. The original 13:12 receipt and baseline diagnostic
remain historical evidence, not overwritten. Original controls:

1. Actual Retryer predicates, eventual success, exception propagation and
   maximum-attempt stop behavior.
2. Actual FixedTimeLimitAttemptOperation / SimpleTimeLimiter success,
   checked failure, timeout and worker interruption/cleanup. Required
   `create(ExecutorService)` and `callWithTimeout(Callable,long,TimeUnit)`
   contracts are retained and executed.
3. Real loading-cache policies matching project usage, explicit removal,
   statistics, and future listener/cancellation behavior.
4. Actual input-to-packet pipe ByteStreams limiting, finite chunking,
   protobuf payload preservation and close behavior.
5. Real old gRPC ClientCalls future completion/cancellation and ProtoUtils
   marshalling of the actual generated Endpoint message, using a controlled
   in-memory ClientCall transport fixture. No channel, socket or DNS.
6. Ordinary self-generated compact collection and weak-key MapMaker native
   serialization round trips.
7-9. Finite native-deserialization allocation boundaries described below.

### Allocation regression without OOM or a large malicious stream

Each fixture locally serializes exactly two inert String entries. A
recording ObjectOutputStream identifies its actual size integer; only that
integer is changed from 2 to **4096**. Inputs remain below 4 KiB. There are
no external streams, classes, gadget chains, giant counts or accepted OOMs.
The separate security JVM has **32 MiB heap / 2 MiB stack / 25 s limit**.

Test-only Java 8 reflection observes the actual deserialized backing-array
capacity after the first insertion, before the intentionally truncated
compact stream fails closed. Both candidate compact classes allocate 256,
not the declared 4096. The MapMaker fixture has a valid entry terminator
and returns two entries; total segment capacity is also 256.

The literal Guava 27.0.1-jre runtime diagnostic, with failureaccess 1.0.1,
passes the five API tests and ordinary serialization. It **reproduces only
MapMaker**: capacity4096 versus candidate256. Its compact map/set already
allocate only3 in this fixture, so those two are candidate boundary
controls, **not two old-version vulnerability reproductions**. An initial
runner expectation of three failures was corrected to the one actually
observed failure; raw logs are retained, with no Java fixture change.

The old-API javac control emitted a missing compile-only J2objc annotation
metadata warning, not a missing method or runtime failure. Candidate
runtime contains every declared direct artifact. Static classfile checks
also resolve all 102 Guava method/field references across six old gRPC
JARs, including inherited Java 8 Future methods; this supports but does not
replace the executable checks.

## Additional actual old-gRPC in-process lifecycle validation

The three added controls run **real grpc-core 1.16.1**
`InProcessServerBuilder`, `InProcessChannelBuilder`, managed channel and
in-process transport. They use `ServerCalls.asyncUnaryCall` and
`ClientCalls.futureUnaryCall` with actual FATE `BasicMeta.Endpoint` messages,
not a fake ClientCall or production replacement stub. They verify:

- Unary response preservation and server `INVALID_ARGUMENT` propagation.
- Client future cancellation reaching the real server Context.
- A 400 ms deadline producing `DEADLINE_EXCEEDED` and cancelling the real
  server Context.
- Channel and server termination within two seconds after every fixture.

Each fixture uses a unique in-memory registry name, no socket/port,
external service, DNS, TLS or Netty native transport. The test JVM has
64 MiB heap / 2 MiB stack / 25 s process limit. The three new tests passed,
then one aggregate of unchanged original nine plus new three passed12/12;
no old-version/security matrix was repeated.

The default `statsEnabled` and `tracingEnabled` flags on both actual builders
are observed true, never disabled or replaced to bypass dependencies.
Upstream in-process constructors themselves leave started/finished RPC
recording flags false; those exact defaults are preserved. This does not
claim a metrics/tracing exporter or recording acceptance test.

The originally declared gRPC compile/runtime artifacts
`io.opencensus:opencensus-api:0.12.3`,
`io.opencensus:opencensus-contrib-grpc-metrics:0.12.3`, and
`com.google.code.gson:gson:2.7` were obtained from official Maven Central
with published SHA-1 and local SHA-256 verification. Their required
non-test transitives are already represented by the selected Guava,
gRPC-context and annotation artifacts. No project POM/dependency/runtime
pin, framework or installed tool changed; no module/tracing stub, setting
change or optional external exporter was added. This closes the specific
previously untested native in-process channel/server compatibility boundary,
not the entire gRPC protocol/network or FATE application boundary.

## Limits and exposure

No direct ObjectInputStream, FileBackedOutputStream
or Files.createTempDir call was found in the scoped project search. This
is not proof of absence through libraries or callers. Native deserialization
must not accept arbitrary untrusted objects even after this patch. The
medium temporary-filesystem advisories were checked by official provenance,
not by creating or exposing host files.

The cache control is a representative real API policy test, not live gRPC
channel-cache creation, TLS, removal-shutdown or production lifecycle
acceptance. The new real in-process channel/server controls are not real-network, TLS,
native-Netty, exporter, complete protocol or interoperability acceptance. No full Maven/reactor/application/Spring,
DB/native/training/deployment matrix was run; no Maven/JDK/framework was
installed. Targeted compatibility is not universal compatibility for all
Guava Beta APIs, persisted objects or application workloads.

No deployment, release, permission, credential, scanner configuration,
force push or unrelated dependency changes. Existing drafts remain intact.
The historical 13:12 source-only composition of the OLD PR23 head with
Commons IO and Spring required explicit context resolution for adjacent
Spring/Guava property lines. That receipt proves the then-current combined
pins/tests/docs only, not the new full combined test/doc tree. This update
keeps the parent POM pin/blob unchanged, so the prospective property-context
warning remains; no combined runtime or automatically clean merge is claimed.
No new integration commit/ref or all-PR matrix was created. If Spring lands
first, refresh/resolve this draft against the new base before its separately
approved merge.

GitHub CI must be reported as observed; local tests do not make CI green.
Merge remains separately decided.

## Official references

- [33.7.2 release and JRE/Android artifacts](https://github.com/google/guava/releases/tag/v33.7.2)
- [Guava compatibility policy](https://github.com/google/guava/wiki/Compatibility)
- [Official 33.7.2-jre POM](https://repo.maven.apache.org/maven2/com/google/guava/guava/33.7.2-jre/guava-33.7.2-jre.pom)
- [Official dependency parent](https://repo.maven.apache.org/maven2/com/google/guava/guava-parent/33.7.2-jre/guava-parent-33.7.2-jre.pom)

## 2026-11-01 approved default-branch composition

The approved Spring and Jackson repairs are now on master. The adjacent Spring/Guava POM conflict was explicitly resolved by preserving Spring 5.2.22.RELEASE, Guava 33.7.2-jre and all already merged default-branch pins. This source-only merge leaves the accepted twelve-test Guava test blob unchanged; its original Java 8 evidence is retained. It establishes the current source union, not a full combined-reactor runtime result.
