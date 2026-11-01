"""Bounded source-level parser regression; not full legacy-runtime acceptance."""
import ast
import builtins
import calendar
import hashlib
import pathlib
import re
import signal
import sys
import time
import types
import unittest

import future
from future.utils import iteritems, iterkeys, itervalues, PY2


def date_parser_source_namespace():
    """Compile only the installed, unchanged date-parser definitions.

    The full legacy backports package imports imp (removed in Python 3.12).
    This explicit source-level check does not insert a compatibility shim or
    claim that the entire package imports on this newer test interpreter.
    """
    path = pathlib.Path(future.__file__).parent / "backports" / "http" / "cookiejar.py"
    source = path.read_bytes()
    expected_hash = {"0.16.0": "4c32d112e2480cc91135df61e28aa429d46f9e009780cd278dac728a00d9f93a",
                     "0.18.3": "a0c97185a679fb186df8a671deac99e60ecbad94e9a7e239eec089eea50b76b7"}
    if hashlib.sha256(source).hexdigest() != expected_hash.get(future.__version__):
        raise AssertionError("Unrecognized installed official cookiejar source hash")
    module = ast.parse(source.decode("utf-8"), filename=str(path))
    constants = {"EPOCH_YEAR", "MONTHS", "MONTHS_LOWER", "UTC_ZONES",
                 "STRICT_DATE_RE", "WEEKDAY_RE", "LOOSE_HTTP_DATE_RE", "ISO_DATE_RE", "TIMEZONE_RE"}
    functions = {"_timegm", "offset_from_tz_string", "_str2time", "http2time", "iso2time"}
    selected = []
    found = set()
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in constants for target in node.targets):
            selected.append(node)
            found.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.FunctionDef) and node.name in functions:
            if node.decorator_list:
                raise AssertionError("Unexpected decorated parser function")
            selected.append(node)
            found.add(node.name)
        elif (isinstance(node, ast.For) and isinstance(node.iter, ast.Name)
              and node.iter.id == "MONTHS"):
            selected.append(node)
    if not constants.union(functions).issubset(found):
        raise AssertionError("Installed cookiejar parser layout changed")
    subset = ast.Module(body=selected)
    if "type_ignores" in ast.Module._fields:
        subset.type_ignores = []
    ast.fix_missing_locations(subset)
    # Contain the original module's re.ASCII assignment in a namespace-local
    # copy. The upstream assignment/conditional, regexes and functions are
    # executed unchanged; the process-wide stdlib module is never mutated.
    regex_api = types.ModuleType("isolated_source_validation_re")
    regex_api.__dict__.update(re.__dict__)
    namespace = {"re": regex_api, "time": time, "timegm": calendar.timegm, "PY2": PY2}
    for node in module.body:
        is_assignment = (isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)
            and target.value.id == "re" and target.attr == "ASCII" for target in node.targets))
        is_conditional = (isinstance(node, ast.If) and isinstance(node.test, ast.Name)
                          and node.test.id == "PY2")
        if is_assignment or is_conditional:
            flag_module = ast.Module(body=[node])
            if "type_ignores" in ast.Module._fields:
                flag_module.type_ignores = []
            exec(compile(ast.fix_missing_locations(flag_module), str(path), "exec"), namespace)
    exec(compile(subset, str(path), "exec"), namespace)
    return namespace


class ParserCpuBudgetExceeded(Exception):
    pass


class FutureCookiejarSecurityTest(unittest.TestCase):
    def test_ordinary_future_mapping_helpers(self):
        values = {"plain": 3, "配置": 7}
        self.assertEqual(sorted(values.items()), sorted(iteritems(values)))
        self.assertEqual(sorted(values.keys()), sorted(iterkeys(values)))
        self.assertEqual(sorted(values.values()), sorted(itervalues(values)))

    def test_observed_python3_builtins_are_standard_library(self):
        # FATE's three observed builtins imports are stdlib on Python 3;
        # they are not evidence of future.backports usage or exploitability.
        self.assertIn("builtins", sys.builtin_module_names)
        self.assertIs(builtins, sys.modules["builtins"])
        self.assertIs(builtins.dict, dict)
        self.assertIn(type({}).__name__, dir(builtins))
        self.assertIn(type("synthetic").__name__, dir(builtins))

    def test_original_source_date_parser_normal_controls(self):
        parser = date_parser_source_namespace()
        self.assertEqual(0, parser["http2time"]("Thu, 01 Jan 1970 00:00:00 GMT"))
        self.assertEqual(946681200, parser["http2time"]("01 Jan 2000 00:00:00 +0100"))
        self.assertEqual(946684800, parser["iso2time"]("2000-01-01T00:00:00Z"))
        self.assertIsNone(parser["http2time"]("not-a-date"))

    @unittest.skipUnless(hasattr(signal, "ITIMER_VIRTUAL"), "Needs a POSIX CPU-time budget")
    def test_cookie_expiry_whitespace_respects_cpu_budget(self):
        parser = date_parser_source_namespace()
        malformed = "01 Jan 2000" + (" " * 2048) + "!"
        def exhausted(signum, frame):
            raise ParserCpuBudgetExceeded("Cookie date parser exceeded 0.5 CPU seconds")
        previous = signal.signal(signal.SIGVTALRM, exhausted)
        signal.setitimer(signal.ITIMER_VIRTUAL, 0.5)
        try:
            self.assertIsNone(parser["http2time"](malformed))
        except ParserCpuBudgetExceeded as error:
            self.fail(str(error))
        finally:
            signal.setitimer(signal.ITIMER_VIRTUAL, 0)
            signal.signal(signal.SIGVTALRM, previous)

    @unittest.skipIf(sys.version_info >= (3, 12),
                     "Full legacy backports import needs imp; no Python 3.12 shim is inserted")
    def test_full_backports_module_on_its_supported_legacy_runtime(self):
        from future.backports.http import cookiejar
        self.assertIn("future/backports/http", cookiejar.__file__.replace("\\", "/"))
        self.assertEqual(0, cookiejar.http2time("Thu, 01 Jan 1970 00:00:00 GMT"))


if __name__ == "__main__":
    unittest.main()
