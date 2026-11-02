"""Ordinary highlighting/declared-consumer checks, without adversarial input.

Use the project's pinned nbconvert and IPython sources on PYTHONPATH. Their
highlighting leaves are loaded in isolation; unrelated notebook services and
interactive application dependencies are deliberately not started.
"""
import ast
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import sys
import unittest
import warnings

import pygments
from pygments import highlight, lex
from pygments.formatters import HtmlFormatter, LatexFormatter
from pygments.lexers import get_lexer_by_name
from pygments.token import Keyword


def declared_package_file(package, relative):
    spec = importlib.util.find_spec(package)
    if spec is None or spec.origin is None:
        raise RuntimeError("missing declared consumer: " + package)
    return Path(spec.origin).resolve().parent / relative


def nbconvert_highlight():
    path = declared_package_file("nbconvert", "filters/highlight.py")
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    functions = [node for node in tree.body
                 if isinstance(node, ast.FunctionDef)
                 and node.name == "_pygments_highlight"]
    if len(functions) != 1:
        raise RuntimeError("declared nbconvert highlighting helper missing")
    module = ast.parse("")
    module.body = functions
    namespace = {"warn": warnings.warn}
    exec(compile(module, str(path), "exec"), namespace)
    return namespace["_pygments_highlight"]


class PlainHTML(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def displayed_text(html):
    parser = PlainHTML()
    parser.feed(html)
    return "".join(parser.parts).strip()


class HighlightCompatibility(unittest.TestCase):
    def test_patched_version_gate(self):
        version = tuple(int(part) for part in pygments.__version__.split(".")[:3])
        self.assertGreaterEqual(version, (2, 7, 4))

    def test_normal_lexer_token_streams(self):
        cases = {
            "python3": "value = 42\nprint(value)\n",
            "sml": "fun add (x, y) = x + y\nval answer = add (20, 22)\n",
            "java": "class Demo { int value = 42; }\n",
            "json": '{"value": 42, "enabled": true}\n',
        }
        for language, source in cases.items():
            with self.subTest(language=language):
                tokens = list(lex(source, get_lexer_by_name(language)))
                self.assertEqual("".join(value for _, value in tokens).strip(),
                                 source.strip())
        sml = list(lex(cases["sml"], get_lexer_by_name("sml")))
        self.assertTrue(any(token in Keyword and value in {"fun", "val"}
                            for token, value in sml))

    def test_html_escaping_and_style(self):
        source = "value = '<safe>&'\n"
        formatter = HtmlFormatter(cssclass="highlight")
        html = highlight(source, get_lexer_by_name("python3"), formatter)
        self.assertEqual(displayed_text(html), source.strip())
        self.assertNotIn("<safe>", html)
        self.assertIn("&lt;safe&gt;", html)
        self.assertIn("&amp;", html)
        self.assertIn(".highlight", formatter.get_style_defs(".highlight"))

    def test_actual_nbconvert_magic_language_override(self):
        source = "answer = 42\nprint(answer)\n"
        html = nbconvert_highlight()(source, HtmlFormatter(), "ipython3",
                                     {"magics_language": "python3"})
        self.assertEqual(displayed_text(html), source.strip())

    def test_actual_nbconvert_plain_text_fallback(self):
        source = "ordinary <text> & Unicode 雪\n"
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            html = nbconvert_highlight()(source, HtmlFormatter(),
                                         "fate_unknown_language")
        self.assertEqual(displayed_text(html), source.strip())
        self.assertTrue(any("No lexer found" in str(item.message)
                            for item in caught))

    def test_actual_nbconvert_latex(self):
        latex = nbconvert_highlight()("answer = 42\n", LatexFormatter(), "python3")
        self.assertIn(r"\begin{Verbatim}", latex)
        self.assertIn(r"\end{Verbatim}", latex)
        self.assertIn("answer", latex)
        self.assertIn("42", latex)

    def test_declared_ipython_lexer_leaf(self):
        path = declared_package_file("IPython", "lib/lexers.py")
        spec = importlib.util.spec_from_file_location("_fate_ipython_lexers", str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = "answer = 42\nprint(answer)\n"
        html = highlight(source, module.IPython3Lexer(), HtmlFormatter())
        self.assertEqual(displayed_text(html), source.strip())


if __name__ == "__main__":
    print("runtime=" + sys.version.replace("\n", " "), flush=True)
    print("Pygments=" + pygments.__version__ + " at " + pygments.__file__, flush=True)
    print("nbconvert=" + str(declared_package_file("nbconvert", "filters/highlight.py")),
          flush=True)
    print("IPython=" + str(declared_package_file("IPython", "lib/lexers.py")), flush=True)
    unittest.main(verbosity=2)
