"""Ordinary process regressions for FATE's unchanged psutil call sites.

Run with the desired real psutil build on PYTHONPATH. Only processes created
by this test are signalled. No malformed inputs or double-free reproduction.
"""
import ast
import errno
import json
import logging
import os
from pathlib import Path
import select
import subprocess
import sys
import time
import unittest
import uuid

import psutil


SOURCE = Path(__file__).resolve().parents[1] / "utils" / "job_utils.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
names = {"check_job_process", "kill_process"}
functions = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
assert {node.name for node in functions} == names
# Reuse the actual functions without importing unrelated Flask/DB/FATE services.
module = ast.parse("")
module.body = functions
namespace = {"os": os, "errno": errno, "psutil": psutil,
             "stat_logger": logging.getLogger("psutil-compatibility")}
exec(compile(module, str(SOURCE), "exec"), namespace)
check_job_process = namespace["check_job_process"]
kill_process = namespace["kill_process"]


class ProcessCompatibility(unittest.TestCase):
    def setUp(self):
        self.marker = "fate-psutil-regression-" + uuid.uuid4().hex
        self.owned = []

    def worker(self):
        process = subprocess.Popen(
            [sys.executable, "-c",
             "import time; print('ready',flush=True); time.sleep(30)", self.marker],
            stdout=subprocess.PIPE, universal_newlines=True)
        self.owned.append(process)
        self.assertTrue(select.select([process.stdout], [], [], 5)[0])
        self.assertEqual(process.stdout.readline().strip(), "ready")
        self.assertIn(self.marker, psutil.Process(process.pid).cmdline())
        return process

    def tearDown(self):
        for process in self.owned:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            if process.stdout:
                process.stdout.close()

    def test_fixed_version_gate(self):
        self.assertGreaterEqual(tuple(psutil.version_info), (5, 6, 6))

    def test_pid_validation_without_signalling(self):
        self.assertFalse(check_job_process(-1))
        with self.assertRaises(ValueError):
            check_job_process(0)
        self.assertFalse(kill_process(0))
        self.assertFalse(kill_process(None))

    def test_live_owned_process(self):
        process = self.worker()
        self.assertTrue(check_job_process(process.pid))
        self.assertEqual(psutil.Process(process.pid).pid, process.pid)
        self.assertIsNone(process.poll())

    def test_already_reaped_owned_process(self):
        process = self.worker()
        process.kill()
        process.wait(timeout=5)
        self.assertFalse(check_job_process(process.pid))
        self.assertTrue(kill_process(process.pid))

    def test_single_target_preserves_neighbour(self):
        target = self.worker()
        neighbour = self.worker()
        self.assertTrue(kill_process(target.pid))
        self.assertEqual(target.wait(timeout=5), -9)
        self.assertIsNone(neighbour.poll())
        self.assertTrue(check_job_process(neighbour.pid))

    def test_real_children_api(self):
        process = self.worker()
        children = psutil.Process(os.getpid()).children(recursive=True)
        self.assertIn(process.pid, [child.pid for child in children])
        self.assertEqual(psutil.Process(process.pid).children(recursive=True), [])

    def test_recursive_owned_family_preserves_neighbour(self):
        neighbour = self.worker()
        # Ignore SIGCHLD in the owned parent so the kernel auto-reaps its child.
        code = ("import json,signal,subprocess,sys,time; "
                "signal.signal(signal.SIGCHLD,signal.SIG_IGN); "
                "p=subprocess.Popen([sys.executable,'-c',"
                "\"import time; print('ready',flush=True); time.sleep(30)\",sys.argv[1]],"
                "stdout=subprocess.PIPE,universal_newlines=True); "
                "assert p.stdout.readline().strip()=='ready'; "
                "print(json.dumps({'child':p.pid}),flush=True); time.sleep(30)")
        parent = subprocess.Popen([sys.executable, "-c", code, self.marker],
                                  stdout=subprocess.PIPE, universal_newlines=True)
        self.owned.append(parent)
        self.assertTrue(select.select([parent.stdout], [], [], 5)[0])
        child_pid = json.loads(parent.stdout.readline())["child"]
        # Both the returned PID and ancestry must match our freshly owned family.
        self.assertIn(self.marker, psutil.Process(parent.pid).cmdline())
        child = psutil.Process(child_pid)
        self.assertIn(self.marker, child.cmdline())
        self.assertEqual(child.ppid(), parent.pid)
        self.assertIn(child_pid, [p.pid for p in
                                 psutil.Process(parent.pid).children(recursive=True)])
        try:
            self.assertTrue(kill_process(parent.pid))
            self.assertEqual(parent.wait(timeout=5), -9)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    if child.status() == psutil.STATUS_ZOMBIE:
                        break
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.01)
            else:
                self.fail("owned descendant remains running")
            self.assertIsNone(neighbour.poll())
        finally:
            try:
                if child.is_running() and child.status() != psutil.STATUS_ZOMBIE:
                    child.kill()
            except psutil.NoSuchProcess:
                pass


if __name__ == "__main__":
    print("runtime=" + sys.version.replace("\n", " "), flush=True)
    print("psutil=" + psutil.__version__ + " at " + psutil.__file__, flush=True)
    unittest.main(verbosity=2)
