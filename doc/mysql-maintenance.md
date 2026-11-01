# Java 8-compatible MySQL Connector/J security maintenance

The exact `arch/core/pom.xml` alert is
[GHSA-m6vm-37g8-gqvh / CVE-2023-22102](https://github.com/advisories/GHSA-m6vm-37g8-gqvh).
The old `mysql:mysql-connector-java` coordinate ends at 8.0.33 and has no fixed
release. Its official Maven POM relocates to `com.mysql:mysql-connector-j`.
Use that official successor at **8.2.0**, the advisory's first fixed release.
This is not a database-server, Java-runtime, FATE-major or 9.x driver upgrade.

[Oracle's 8.2.0 release notes](https://dev.mysql.com/doc/relnotes/connector-j/en/news-8-2-0.html)
state MySQL Server >=5.7 and JDBC 4.2 support and document removal of BLOB
auto-deserialization. The configured `com.mysql.cj.jdbc.Driver` class remains.
The scoped project source/configuration review found no `autoDeserialize` use
or hard-coded connector JAR basename. No connection or TLS setting is changed.

The successor driver POM brings `protobuf-java` 3.21.9 instead of the prior
driver's 3.11.4. The project's existing protobuf/protoc/grpc version properties
are unchanged. This transitive runtime change is not hidden or excluded:
Java 8 compilation of all six actual project protobuf message classes,
regenerated with the existing protoc 3.6.1, and scalar/repeated round trips
passed on protobuf 3.21.9. This does not establish gRPC transport compatibility
or full Maven dependency convergence.

Run the offline JDBC regression with Java 8:

```sh
mvn -f arch/core/pom.xml -Dtest=MysqlConnectorSecurityTest test
```

Maintenance executed direct Java 8 javac/JUnit 4.12 checks of the three added
metadata-only tests, plus a driver-loading/URL/property probe with network
connections denied. Tests never connect to a database. No full Maven reactor,
RPC/gRPC service, MyBatis/database integration, training, native library,
packaging, deployment or production acceptance is claimed. The separate
missing `eggroll` reactor checkout was not initialized. This addresses the
one mapped advisory; it is not a claim that all dependency risks are resolved.
