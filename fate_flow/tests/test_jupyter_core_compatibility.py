"""Real JupyterApp/path checks; never load or execute configuration files."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import jupyter_core
from jupyter_core.application import JupyterApp
from jupyter_core import paths


class JupyterCoreCompatibility(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(
            prefix="fate-jupyter-paths-", dir=os.environ.get("FATE_MAINT_TEST_TMP"))
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.home = self.root / "home"
        self.config = self.root / "config"
        self.data = self.root / "data"
        self.runtime = self.root / "runtime"
        self.cwd = self.root / "cwd"
        self.extra = self.root / "extra"
        for directory in [self.home, self.config, self.data,
                          self.runtime, self.cwd, self.extra]:
            directory.mkdir()
        self.environment = patch.dict(os.environ, {
            "HOME": str(self.home),
            "JUPYTER_CONFIG_DIR": str(self.config),
            "JUPYTER_DATA_DIR": str(self.data),
            "JUPYTER_RUNTIME_DIR": str(self.runtime),
            "JUPYTER_CONFIG_PATH": "",
            "JUPYTER_PATH": "",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        previous_cwd = os.getcwd()
        os.chdir(str(self.cwd))
        self.addCleanup(os.chdir, previous_cwd)

    def test_patched_version_gate(self):
        version = tuple(int(part) for part in jupyter_core.__version__.split(".")[:3])
        self.assertGreaterEqual(version, (4, 11, 2))

    def test_real_app_does_not_implicitly_trust_cwd(self):
        app = JupyterApp()
        self.assertNotIn(str(self.cwd), app.config_file_paths)
        self.assertEqual(list(self.cwd.iterdir()), [])

    def test_real_app_explicit_config_dir_has_priority(self):
        custom = self.root / "requested-config"
        custom.mkdir()
        app = JupyterApp(config_dir=str(custom))
        self.assertEqual(app.config_file_paths[0], str(custom))
        self.assertEqual(app.config_file_paths.count(str(custom)), 1)
        self.assertNotIn(str(self.cwd), app.config_file_paths)

    def test_trusted_cwd_can_still_be_explicitly_requested(self):
        app = JupyterApp(config_dir=str(self.cwd))
        self.assertEqual(app.config_file_paths[0], str(self.cwd))
        self.assertIn(str(self.cwd), app.config_file_paths)

    def test_existing_directory_override_apis(self):
        self.assertEqual(paths.jupyter_config_dir(), str(self.config))
        self.assertEqual(paths.jupyter_data_dir(), str(self.data))
        self.assertEqual(paths.jupyter_runtime_dir(), str(self.runtime))

    def test_explicit_config_search_path_is_honored(self):
        with patch.dict(os.environ, {"JUPYTER_CONFIG_PATH": str(self.extra)}):
            actual = paths.jupyter_config_path()
            self.assertEqual(actual[0], str(self.extra))
            self.assertIn(str(self.config), actual)
            app = JupyterApp()
            self.assertIn(str(self.extra), app.config_file_paths)
            self.assertNotIn(str(self.cwd), app.config_file_paths)

    def test_data_search_sections_are_preserved(self):
        with patch.dict(os.environ, {"JUPYTER_PATH": str(self.extra)}):
            actual = paths.jupyter_path("kernels")
            self.assertEqual(actual[0], str(self.extra / "kernels"))
            self.assertIn(str(self.data / "kernels"), actual)


if __name__ == "__main__":
    print("runtime=" + sys.version.replace("\n", " "), flush=True)
    print("jupyter_core=" + jupyter_core.__version__ + " at " + jupyter_core.__file__,
          flush=True)
    unittest.main(verbosity=2)
