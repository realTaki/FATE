# Java 8 logging maintenance

`arch/pom.xml` uses Log4j API and Core 2.25.5 together. The parent property
is inherited by the Java core, federation and proxy modules. Java 8 and all
other dependencies are unchanged; this is not an upgrade to FATE 2.x.

Apache identifies 2.25.5 as a fixed version for the API MapMessage non-finite
JSON issue, CVE-2026-49844. It also includes the earlier Log4j 2 security
fixes missing from the original 2.11.1. See the
[Apache security advisories](https://logging.apache.org/security.html) and
[Java 8 requirement](https://logging.apache.org/log4j/2.x/manual/installation.html#requirements).
This does not assert that this application exposes every affected feature.

Run the logging regression tests with a Java 8 JDK:

```sh
mvn -f arch/core/pom.xml -Dtest=Log4jSecurityTest test
```

The tests check API/Core alignment, literal untrusted message text,
RFC 8259-compliant non-finite MapMessage values and ordinary finite values.
They do not start a business service, connect to a network or load a model.

Maintenance verification also compiled the actual core and its generated
protobuf sources under Java 8, and loaded all three unchanged Java logging
configurations in isolated logging-only JVMs with network operations denied.
Every configured rolling-file output retained the literal message marker.
This is not full reactor, packaging, database, native library, federation,
training, deployment or production acceptance. The original reactor refers
to an absent `eggroll` checkout; that external project was not initialized.
Existing Java internal-API/deprecation/unchecked warnings remain.

Other legacy Java/Python dependencies and existing Dependabot pull requests
are unchanged. Current live Dependabot alerts were not readable in the
existing authentication context; lack of access is not zero alerts.
Upstream FATE is substantially newer and crosses a major version/runtime
boundary, so it was assessed but not blindly synchronized.
