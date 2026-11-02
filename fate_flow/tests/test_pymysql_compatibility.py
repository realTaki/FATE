"""Mapped alert #560: real PyMySQL/Peewee APIs without a database server.

Run with the declared Peewee 3.9.3 and candidate PyMySQL 1.1.1 installed.
All connection objects are deferred; no SQL, handshake or credentials are sent.
"""
import ast
import datetime
from decimal import Decimal
import pathlib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import peewee
import pymysql
from playhouse.pool import PooledMySQLDatabase


ROOT = pathlib.Path(__file__).resolve().parents[2]


class PyMySQLCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.network_guard = patch(
            "socket.create_connection", side_effect=AssertionError("no network in component tests"))
        self.network_guard.start()
        self.addCleanup(self.network_guard.stop)

    def connection(self):
        conn = pymysql.connect(
            db="synthetic_fate", host="127.0.0.1", user="synthetic", password="",
            charset="utf8", use_unicode=True, defer_connect=True)
        # Explicit offline server mode for ordinary parameter formatting only.
        # This is not a real handshake or a modification to the driver.
        conn.server_status = 0
        self.addCleanup(conn.close)
        return conn

    def pool(self):
        db = PooledMySQLDatabase(
            "synthetic_fate", host="127.0.0.1", port=3306, user="synthetic",
            password="", charset="utf8", max_connections=2, stale_timeout=30,
            defer_connect=True)
        self.addCleanup(db.close_all)
        return db

    def test_01_patched_distribution_version(self):
        # __version__ intentionally follows mysqlclient compatibility numbering.
        self.assertGreaterEqual(pymysql.VERSION[:3], (1, 1, 1))

    def test_02_original_peewee_driver_binding(self):
        self.assertEqual(peewee.__version__, "3.9.3")
        self.assertIs(peewee.mysql, pymysql)
        self.assertEqual(pymysql.apilevel, "2.0")
        self.assertEqual(pymysql.paramstyle, "pyformat")

    def test_03_real_pool_to_driver_constructor(self):
        db = self.pool()
        conn = db._connect()
        self.assertIsInstance(conn, pymysql.connections.Connection)
        self.assertFalse(conn.open)
        self.assertEqual(conn.db, "synthetic_fate")
        self.assertEqual(conn.charset, "utf8")
        self.assertTrue(db._is_closed(conn))  # ping(False) must not reconnect.

    def original_cluster_initializer(self, path):
        source = (ROOT / path).read_text()
        tree = ast.parse(source)
        node = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "BaseDataBase")
        # Only bypass the unrelated singleton/startup imports, never its body.
        node.decorator_list = []
        module = ast.Module(body=[node])
        if "type_ignores" in ast.Module._fields:
            module.type_ignores = []
        flags = []
        config = dict(name="synthetic_fate", host="127.0.0.1", user="synthetic", password="", defer_connect=True)
        ns = dict(DATABASE=config, WORK_MODE=1, WorkMode=SimpleNamespace(CLUSTER=1, STANDALONE=0),
                  USE_LOCAL_DATABASE=False, PooledMySQLDatabase=PooledMySQLDatabase,
                  RuntimeConfig=SimpleNamespace(init_config=lambda **kw: flags.append(kw)),
                  stat_logger=SimpleNamespace(info=lambda *args: None))
        exec(compile(module, str(ROOT / path), "exec"), ns)
        instance = ns["BaseDataBase"]()
        db = instance.database_connection
        self.addCleanup(db.close_all)
        self.assertEqual(config["name"], "synthetic_fate")  # Original copies config.
        self.assertEqual(flags, [{"USE_LOCAL_DATABASE": False}])
        conn = db._connect()
        self.assertIsInstance(conn, pymysql.connections.Connection)
        self.assertFalse(conn.open)

    def test_04_actual_flow_cluster_initializer(self):
        self.original_cluster_initializer("fate_flow/db/db_models.py")

    def test_05_actual_rsa_cache_cluster_initializer(self):
        self.original_cluster_initializer("federatedml/statistic/intersect/rsa_cache/db_models.py")

    def test_06_real_peewee_query_and_driver_binding(self):
        db = self.pool()

        class Row(peewee.Model):
            label = peewee.CharField()
            count = peewee.IntegerField()

            class Meta:
                database = db
                table_name = "synthetic_row"

        sql, params = Row.select().where((Row.label == "ordinary's label") & (Row.count == 3)).sql()
        self.assertEqual(params, ["ordinary's label", 3])
        formatted = self.connection().cursor().mogrify(sql, params)
        self.assertIn("ordinary\\'s label", formatted)
        self.assertNotIn("%s", formatted)

    def test_07_ordinary_types_and_null(self):
        text = self.connection().cursor().mogrify(
            "SELECT %s, %s, %s", (Decimal("4.20"), datetime.date(2026, 1, 2), None))
        self.assertEqual(text, "SELECT 4.20, '2026-01-02', NULL")

    def test_08_named_argument_mapping_still_supported(self):
        text = self.connection().cursor().mogrify("SELECT %(label)s", {"label": "ordinary"})
        self.assertEqual(text, "SELECT 'ordinary'")

    def test_09_dictionary_is_not_a_scalar_parameter(self):
        # Benign structural regression for the advisory fix; no injection text.
        with self.assertRaises(TypeError):
            self.connection().escape({"ordinary": "value"})

    def test_10_driver_exception_hierarchy(self):
        self.assertTrue(issubclass(pymysql.OperationalError, pymysql.DatabaseError))
        self.assertTrue(issubclass(pymysql.IntegrityError, pymysql.DatabaseError))
        self.assertIn("OperationalError", peewee.EXCEPTIONS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
