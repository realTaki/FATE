"""Ordinary Bleach/declared nbconvert compatibility for mapped alerts.

No browser, notebook execution, network, attack input or stress workload.
The exact original consumer modules run in a private package namespace only
to avoid unrelated exporter/package startup; their bodies are not modified.
"""
import hashlib
import importlib
import importlib.machinery
import pathlib
import sys
import types
import unittest

import bleach
import six


CONSUMER_HASHES = {
    "utils/base.py": "3e28f478bdce14eed2baac9c47f621d1b852e9be9f801b82ad49086fdcf85836",
    "preprocessors/base.py": "24b4b3535b5108052d23be50b356d485742d8b9998aa0ce0ed4b1f98329eeca5",
    "preprocessors/sanitize.py": "41b561741fe59a477c73ce2b9ae961a95b6324b4b2e94aebe19543353abdde2f",
}


def original_sanitizer():
    spec = importlib.machinery.PathFinder.find_spec("nbconvert", sys.path)
    if spec is None or not spec.origin:
        raise RuntimeError("declared nbconvert5.3.1 source is required")
    root = pathlib.Path(spec.origin).parent
    for name, expected in CONSUMER_HASHES.items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise RuntimeError("consumer is not unchanged nbconvert5.3.1: " + name)
    prefix = "_fate_nbconvert_bleach_compat"
    for name, path in [(prefix, root), (prefix + ".utils", root / "utils"),
                       (prefix + ".preprocessors", root / "preprocessors")]:
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module
    return importlib.import_module(prefix + ".preprocessors.sanitize").SanitizeHTML


class BleachCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.SanitizeHTML = original_sanitizer()

    def test_01_patched_versions_and_original_public_exports(self):
        self.assertGreaterEqual(tuple(map(int, bleach.__version__.split(".")[:3])), (3, 3, 0))
        self.assertEqual(six.__version__, "1.17.0")
        for name in ["ALLOWED_ATTRIBUTES", "ALLOWED_STYLES", "ALLOWED_TAGS", "clean"]:
            self.assertTrue(hasattr(bleach, name))
        from six.moves.urllib.parse import urlsplit
        self.assertEqual(urlsplit("https://example.invalid/docs").path, "/docs")

    def test_02_ordinary_allowed_markup_and_unicode(self):
        text = "<strong>ordinary</strong> <em>中文 café</em>"
        self.assertEqual(bleach.clean(text), text)

    def test_03_escape_strip_and_comments(self):
        self.assertEqual(bleach.clean("<section>ordinary</section>"),
                         "&lt;section&gt;ordinary&lt;/section&gt;")
        self.assertEqual(bleach.clean("<section><b>ordinary</b></section>", strip=True), "<b>ordinary</b>")
        self.assertEqual(bleach.clean("before<!-- ordinary comment -->after"), "beforeafter")

    def test_04_normal_link_attributes(self):
        text = '<a href="https://example.invalid/docs" title="ordinary">read</a>'
        self.assertEqual(bleach.clean(text), text)

    def test_05_short_ordinary_css_allowlist(self):
        text = '<span style="color: red; font-weight: bold;">ordinary</span>'
        out = bleach.clean(text, tags=["span"], attributes={"span": ["style"]}, styles=["color"])
        self.assertIn("color: red;", out)
        self.assertNotIn("font-weight", out)
        self.assertIn(">ordinary</span>", out)

    def test_06_plain_linkify_does_not_fetch(self):
        out = bleach.linkify("Read https://example.com/docs")
        self.assertIn('href="https://example.com/docs"', out)
        self.assertIn('rel="nofollow"', out)

    def test_07_real_consumer_raw_and_markdown_cells(self):
        processor = self.SanitizeHTML()
        resources = {}
        for kind in ["raw", "markdown"]:
            cell = types.SimpleNamespace(cell_type=kind, source="<strong>ordinary</strong>")
            result, returned_resources = processor.preprocess_cell(cell, resources, 0)
            self.assertIs(result, cell)
            self.assertIs(returned_resources, resources)
            self.assertEqual(cell.source, "<strong>ordinary</strong>")

    def test_08_real_consumer_output_policy(self):
        processor = self.SanitizeHTML()
        class DisplayOutput(dict):
            __getattr__ = dict.__getitem__

        output = DisplayOutput(output_type="display_data", data={
            "text/html": "<b>ordinary</b>", "text/plain": "ordinary",
            "application/json": {"ordinary": 1}, "application/x-unused": "ordinary"})
        # Plain display-data contract; the real consumer performs all filtering.
        result = processor.sanitize_code_outputs([output])
        self.assertIs(result[0], output)
        self.assertEqual(output.data["text/html"], "<b>ordinary</b>")
        self.assertEqual(output.data["application/json"], {"ordinary": 1})
        self.assertNotIn("application/x-unused", output.data)

    def test_09_real_preprocessor_dispatch(self):
        processor = self.SanitizeHTML(enabled=True)
        cell = types.SimpleNamespace(cell_type="markdown", source="<section>ordinary</section>")
        notebook = types.SimpleNamespace(cells=[cell])
        result, resources = processor(notebook, {})
        self.assertIs(result, notebook)
        self.assertEqual(cell.source, "&lt;section&gt;ordinary&lt;/section&gt;")
        self.assertEqual(resources, {})

    def test_10_real_consumer_traitlets_style_configuration(self):
        processor = self.SanitizeHTML(tags=["span"], attributes={"span": ["style"]}, styles=["color"])
        result = processor.sanitize_html_tags('<span style="color: red;">ordinary</span>')
        self.assertIn("color: red;", result)
        self.assertIn(">ordinary</span>", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
