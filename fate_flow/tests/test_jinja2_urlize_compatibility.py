"""Offline normal templates and the pinned nbconvert ANSI filter, without servers.

Run directly with the root requirements available. No long ReDoS inputs,
untrusted templates, notebooks, browser, network or model execution is used.
"""

import importlib.util
import pathlib
import unittest
from html.parser import HTMLParser

import jinja2
import markupsafe


def load_original_nbconvert_ansi():
    """Load the real installed module without unrelated exporter startup."""
    package = importlib.util.find_spec("nbconvert")
    if package is None or package.origin is None:
        raise RuntimeError("The pinned nbconvert 5.3.1 package is required")
    path = pathlib.Path(package.origin).parent / "filters" / "ansi.py"
    spec = importlib.util.spec_from_file_location("_nbconvert_ansi_compatibility", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AnchorParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.append(dict(attrs).get("href"))


class Jinja2CompatibilityTest(unittest.TestCase):
    def test_patched_release_and_unchanged_markup_safe(self):
        self.assertEqual(jinja2.__version__, "2.11.3")
        self.assertEqual(markupsafe.__version__, "1.0")

    def test_urlize_ordinary_https_and_email(self):
        env = jinja2.Environment(autoescape=True)
        output = env.from_string("{{ value|urlize }}").render(
            value="Visit https://example.com/docs or person@example.org"
        )
        parser = AnchorParser()
        parser.feed(output)
        self.assertEqual(parser.hrefs, ["https://example.com/docs", "mailto:person@example.org"])

    def test_autoescape_unicode_and_trusted_markup(self):
        env = jinja2.Environment(autoescape=True)
        self.assertEqual(env.from_string("{{ value }}").render(value="中文 x < y & tea"),
                         "中文 x &lt; y &amp; tea")
        self.assertEqual(env.from_string("{{ value }}").render(value=markupsafe.Markup("<b>ok</b>")),
                         "<b>ok</b>")

    def test_inheritance_include_and_macro(self):
        env = jinja2.Environment(loader=jinja2.DictLoader({
            "base": "Header:{% block content %}{% endblock %}",
            "part": "{{ title }}",
            "page": '{% extends "base" %}{% block content %}{% macro item(x) %}[{{ x }}]{% endmacro %}{% include "part" %}{{ item(value) }}{% endblock %}',
        }))
        self.assertEqual(env.get_template("page").render(title="Report", value=3), "Header:Report[3]")

    def test_loop_controls_and_whitespace(self):
        env = jinja2.Environment(extensions=["jinja2.ext.loopcontrols"])
        template = env.from_string("{% for n in values %}{% if n == 2 %}{% continue %}{% endif %}{{ n }}{% endfor %}")
        self.assertEqual(template.render(values=[1, 2, 3]), "13")

    def test_context_filter_public_api(self):
        @jinja2.contextfilter
        def with_title(context, value):
            return context["title"] + ":" + value

        env = jinja2.Environment()
        env.filters["with_title"] = with_title
        self.assertEqual(env.from_string("{{ value|with_title }}").render(title="Report", value="ok"),
                         "Report:ok")

    def test_real_nbconvert_ansi_html_and_escaping(self):
        ansi = load_original_nbconvert_ansi()
        self.assertEqual(str(ansi.ansi2html("\x1b[31mred\x1b[0m")),
                         '<span class="ansi-red-fg">red</span>')
        self.assertEqual(str(ansi.ansi2html("x < y & tea")), "x &lt; y &amp; tea")

    def test_real_nbconvert_registered_filter(self):
        ansi = load_original_nbconvert_ansi()
        env = jinja2.Environment()
        env.filters["ansi2html"] = ansi.ansi2html
        self.assertEqual(env.from_string("{{ value|ansi2html }}").render(value="\x1b[1mbold\x1b[0m"),
                         '<span class="ansi-bold">bold</span>')

    def test_real_nbconvert_plain_and_latex(self):
        ansi = load_original_nbconvert_ansi()
        self.assertEqual(ansi.strip_ansi("\x1b[32mgreen\x1b[0m"), "green")
        self.assertEqual(ansi.ansi2latex("ordinary text"), "ordinary text")


if __name__ == "__main__":
    unittest.main(verbosity=2)
