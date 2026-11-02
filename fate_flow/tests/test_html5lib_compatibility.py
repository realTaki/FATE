"""Offline ordinary html5lib APIs; not a browser or full FATE acceptance test.

Run directly with Python and the pinned requirements installed. The fixtures
contain ordinary markup only; no external resources or notebook code execute.
"""

import unittest

import html5lib


class Html5libCompatibilityTest(unittest.TestCase):
    def test_patched_release(self):
        self.assertEqual(html5lib.__version__, "1.1")

    def test_document_and_unicode(self):
        document = html5lib.parse("<title>Report</title><p>中文 café</p>")
        ns = "{http://www.w3.org/1999/xhtml}"
        self.assertEqual(document.tag, ns + "html")
        self.assertEqual(document.find(".//" + ns + "title").text, "Report")
        self.assertEqual(document.find(".//" + ns + "p").text, "中文 café")

    def test_fragment_and_ordinary_error_recovery(self):
        fragment = html5lib.parseFragment("<p>one<p>two")
        self.assertEqual([element.text for element in fragment], ["one", "two"])

    def test_explicit_quoted_attribute_serialization(self):
        fragment = html5lib.parseFragment('<p title="ordinary words">hello &amp; bye</p>')
        actual = html5lib.serialize(fragment, quote_attr_values="always")
        self.assertEqual(actual, '<p title="ordinary words">hello &amp; bye')

    def test_byte_stream_encoding(self):
        document = html5lib.parse(b"<p>caf\xe9</p>", transport_encoding="windows-1252")
        ns = "{http://www.w3.org/1999/xhtml}"
        self.assertEqual(document.find(".//" + ns + "p").text, "café")

    def test_dom_builder_and_walker(self):
        document = html5lib.parse("<p>Hello</p>", treebuilder="dom")
        self.assertEqual(document.getElementsByTagName("p")[0].firstChild.data, "Hello")
        tokens = list(html5lib.getTreeWalker("dom")(document))
        self.assertTrue(any(token.get("data") == "Hello" for token in tokens))

    def test_etree_round_trip(self):
        original = html5lib.parseFragment("<ul><li>one<li>two</ul>")
        serialized = html5lib.serialize(original, omit_optional_tags=False)
        reparsed = html5lib.parseFragment(serialized)
        self.assertEqual(list(reparsed[0].itertext()), ["one", "two"])

    def test_strict_parser_normal_document(self):
        parser = html5lib.HTMLParser(strict=True)
        document = parser.parse("<!doctype html><html><head><title>ok</title></head><body><p>ok</p></body></html>")
        self.assertEqual(document.tag, "{http://www.w3.org/1999/xhtml}html")

    def test_existing_bleach_uses_unchanged_bundled_parser(self):
        import bleach
        from bleach._vendor import html5lib as bundled

        self.assertEqual(bleach.__version__, "3.3.1")
        self.assertIsNot(bundled, html5lib)
        self.assertIn("bleach/_vendor/html5lib", bundled.__file__.replace("\\", "/"))
        self.assertEqual(bleach.clean("<b>ordinary</b> &amp; text"), "<b>ordinary</b> &amp; text")
        self.assertEqual(bleach.linkify("https://example.com/"), '<a href="https://example.com/" rel="nofollow">https://example.com/</a>')


if __name__ == "__main__":
    unittest.main(verbosity=2)
