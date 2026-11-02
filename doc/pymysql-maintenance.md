# PyMySQL mapped security update

This change addresses FATE Dependabot alert **#560**, critical
[GHSA-v9hf-5j83-6xpp](https://github.com/advisories/GHSA-v9hf-5j83-6xpp)
(CVE-2024-36039). The first patched release is **1.1.1**; the existing pin
is 0.9.3. Only that pin and this focused test/documentation are changed.
No application SQL, schema, DB settings or server is changed.

## Compatibility and supported-runtime boundary

The real declared Peewee **3.9.3** and its `PooledMySQLDatabase` module load
unchanged with PyMySQL 1.1.1 on the existing CPython 3.12 test interpreter.
The test exercises the complete driver and these complete consumer modules,
their real deferred connector, both unchanged FATE cluster-initializer bodies,
Peewee query generation, ordinary positional/named argument formatting,
scalar dictionary rejection and the DB-API exception hierarchy.
The two FATE class bodies are AST-isolated only from unrelated server startup,
APSW and live configuration imports; they are not a complete FATE import.

**PyMySQL 1.1.1 requires Python >=3.7 and officially supports MySQL >=5.7
or MariaDB >=10.4. It is not a Python 3.6 / MySQL 5.6 compatibility promise.**
The existing manifest already includes IPython 8.10 requiring Python >=3.8;
the checked-in cluster default is MySQL **8.0.13**
(`cluster-deploy/scripts/default_configurations.sh`), within the driver's
supported server range. The old top-level native-install README still says
Python3.6/MySQL5.6+, so a separate deployment depending on those exact old
versions must resolve its real runtime/server requirements before promotion.
No interpreter or database migration is performed or assumed here, and the
full historical dependency graph is not claimed coherent.

The driver has no mandatory new runtime dependencies. Existing optional RSA
or ed25519 authentication extras are not added, removed or tested. No real
database credentials/configuration are read. Connections use synthetic inputs
with `defer_connect=True`, and an explicit socket guard prevents network access.
No SQL is executed, database server installed, authentication handshake tested,
data migrated, or security-exploit payload sent. Deferred connection state is
set only for local parameter formatting. This is applicable offline component
and consumer validation, not real MySQL/TLS/authentication/full-FATE acceptance.

## Reproduce

With the declared Peewee 3.9.3 and candidate PyMySQL 1.1.1 available:

```sh
python fate_flow/tests/test_pymysql_compatibility.py
```

The baseline uses unchanged official PyMySQL 0.9.3 with the same consumer and
tests. Expected differences are the patched-version gate and the new benign
scalar-dictionary rejection; ordinary compatibility checks must still pass.
A draft PR or a passing component test is not an actual closed Dependabot
alert. Verify the default-branch platform state after any separately approved
merge. No deployment, release, schema or account setting change is included.
