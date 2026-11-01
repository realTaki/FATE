# Java 8-compatible Commons IO maintenance

Update the existing `commons-io:commons-io` dependency in `arch/pom.xml` from
**2.6 to 2.14.0**. The exact open alerts are
[#570 / GHSA-78wr-2p64-hpwj](https://github.com/advisories/GHSA-78wr-2p64-hpwj)
(XmlStreamReader resource consumption, first fixed in 2.14.0) and
[#411 / GHSA-gwrp-pvrq-jmwv](https://github.com/advisories/GHSA-gwrp-pvrq-jmwv)
(invalid path normalization, first fixed in 2.7).

The [official 2.14.0 POM](https://raw.githubusercontent.com/apache/commons-io/rel/commons-io-2.14.0/pom.xml)
declares Java 8 and only test-scope dependencies. Candidate main classes have
major version 52. Both old/candidate JARs were checked against official Maven
Central SHA1 sidecars, with SHA256 receipts retained. This changes neither a
runtime nor another dependency, service setting or Maven coordinate.

## Observed application use and actual checks

Scoped `arch` source use consists of `IOUtils.closeQuietly` in the input/output
proxy pipe close paths. No XmlStreamReader or FilenameUtils application call
was observed in that scope. Library alerts do not by themselves establish
remote application exploitability.

The offline regression compiles the unchanged real `Pipe`, `BasePipe`,
`InputStreamToPacketUnidirectionalPipe` and `PacketToOutputStreamUnidirectionalPipe`
sources and six actual project-generated protobuf message sources against the
original Commons IO 2.6 API. It uses the declared protobuf 3.6.1 API, Guava
27.0.1-jre, Spring 5.1.4 annotations, existing Log4j 2.25.5 and JUnit 4.12 without
starting a Spring container, network or business service. This focused classpath
is not a claim of full Maven dependency convergence.

Actual Java 8 tests give **5/5 candidate passes**. The old 2.6 has **two expected
security failures**: malformed UNC parent prefixes are not rejected, and the
old XML-prolog regex exceeds a hard 8192-character-access budget on a fixed
769-character malformed input. That test uses the same public pattern consumed
by XmlStreamReader; it does not run an unbounded CPU attack or rely on timing.

Three controls pass on both versions: actual input-pipe payload/quiet-close,
actual output-pipe payload/flush/quiet-close (including synthetic IOException
handling), and ordinary UTF-8 XML/path behavior. Streams and payloads are
in-memory synthetic fixtures; no live files, endpoints or credentials are used.

With project dependencies available, use Java 8:

```sh
mvn -f arch/networking/proxy/pom.xml -Dtest=CommonsIoPipeSecurityTest test
```

Maintenance used direct Java 8 javac/JUnit, a 96 MiB test heap, 2 MiB stack and
20-second process limit. It did not run a full Maven/reactor, Spring container,
gRPC transport, database, training, native library, packaging, deployment or
production acceptance matrix. The application sources and stream settings are
unchanged. A draft is not a merge, CI-green result or actual alert closure.
