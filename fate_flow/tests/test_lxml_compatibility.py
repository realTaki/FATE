"""Ordinary in-memory lxml APIs; no browser, external resource or DoS fixture.

Run directly with the root requirements available. Explicit parser/XSLT
resource controls keep these test fixtures offline, not change app policy.
"""

import io
import unittest

import html5lib
import lxml
from lxml import etree, html, objectify
from lxml.html.clean import Cleaner


def xml_parser():
    return etree.XMLParser(resolve_entities=False, no_network=True)


class LxmlCompatibilityTest(unittest.TestCase):
    def test_patched_maintenance_release(self):
        self.assertEqual(lxml.__version__, "4.9.4")
        self.assertEqual(etree.LXML_VERSION[:3], (4, 9, 4))

    def test_xml_namespace_unicode_and_xpath(self):
        root = etree.fromstring('<r xmlns:d="urn:demo"><d:item n="2">中文 café</d:item></r>'.encode("utf-8"), xml_parser())
        self.assertEqual(root.xpath("string(d:item)", namespaces={"d": "urn:demo"}), "中文 café")
        self.assertEqual(root.xpath("sum(d:item/@n)", namespaces={"d": "urn:demo"}), 2.0)

    def test_xml_serialize_round_trip(self):
        root = etree.Element("report")
        etree.SubElement(root, "item").text = "x < y & tea"
        data = etree.tostring(root, encoding="utf-8", xml_declaration=True)
        restored = etree.fromstring(data, xml_parser())
        self.assertEqual(restored.findtext("item"), "x < y & tea")

    def test_html_fragment_and_normal_links(self):
        root = html.fragment_fromstring('<p>中文 &amp; tea</p><a href="https://example.com/">Read</a>', create_parent="section")
        self.assertEqual(root.tag, "section")
        self.assertEqual(root.xpath("string(.//p)"), "中文 & tea")
        self.assertEqual(root.xpath(".//a/@href"), ["https://example.com/"])

    def test_cleaner_preserves_ordinary_allowed_markup(self):
        cleaner = Cleaner(scripts=True, javascript=True, style=False, safe_attrs_only=True)
        root = cleaner.clean_html(html.fromstring('<div><p class="summary">Report &amp; tea</p><a href="https://example.com/">Read</a></div>'))
        self.assertEqual(root.xpath("string(.//p)"), "Report & tea")
        self.assertEqual(root.xpath(".//p/@class"), ["summary"])
        self.assertEqual(root.xpath(".//a/@href"), ["https://example.com/"])

    def test_cleaner_retains_legacy_forms_option(self):
        cleaner = Cleaner(forms=True)
        root = cleaner.clean_html(html.fromstring('<div><form><p>ordinary label</p></form></div>'))
        self.assertEqual(root.xpath(".//form"), [])
        self.assertIn("ordinary label", root.text_content())

    def test_iterwalk_normal_tree(self):
        root = etree.fromstring(b"<report><item>one</item><item>two</item></report>", xml_parser())
        events = [(event, node.tag) for event, node in etree.iterwalk(root, events=("start", "end"))]
        self.assertEqual(events, [("start", "report"), ("start", "item"), ("end", "item"),
                                  ("start", "item"), ("end", "item"), ("end", "report")])

    def test_explicit_offline_iterparse(self):
        events = etree.iterparse(io.BytesIO(b"<report><item>one</item><item>two</item></report>"),
                                 events=("end",), resolve_entities=False, no_network=True)
        self.assertEqual([(node.tag, node.text) for event, node in events],
                         [("item", "one"), ("item", "two"), ("report", None)])

    def test_objectify_ordinary_numbers(self):
        parser = objectify.makeparser(resolve_entities=False, no_network=True)
        root = objectify.fromstring(b"<report><count>2</count><score>1.5</score></report>", parser)
        self.assertEqual(int(root.count), 2)
        self.assertEqual(float(root.score), 1.5)

    def test_canonical_serialization(self):
        root = etree.fromstring(b'<report z="2" a="1"><item>ok</item></report>', xml_parser())
        self.assertEqual(etree.tostring(root, method="c14n"),
                         b'<report a="1" z="2"><item>ok</item></report>')

    def test_parser_reuse_after_ordinary_incomplete_document(self):
        parser = xml_parser()
        with self.assertRaises(etree.XMLSyntaxError):
            etree.fromstring(b"<report>", parser)
        root = etree.fromstring(b"<report><item>ok</item></report>", parser)
        self.assertEqual([node.tag for event, node in etree.iterwalk(root)], ["item", "report"])

    def test_in_memory_xslt_and_schema(self):
        source = etree.fromstring(b"<report><item>one</item><item>two</item></report>", xml_parser())
        stylesheet = etree.fromstring(b'''<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
            <xsl:output method="text"/><xsl:template match="/"><xsl:value-of select="count(report/item)"/></xsl:template>
        </xsl:stylesheet>''', xml_parser())
        access = etree.XSLTAccessControl(read_file=False, write_file=False, create_dir=False,
                                        read_network=False, write_network=False)
        transform = etree.XSLT(stylesheet, access_control=access)
        self.assertEqual(str(transform(source)), "2")
        schema = etree.XMLSchema(etree.fromstring(b'''<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="count" type="xs:unsignedInt"/>
        </xs:schema>''', xml_parser()))
        self.assertTrue(schema.validate(etree.fromstring(b"<count>2</count>", xml_parser())))
        self.assertFalse(schema.validate(etree.fromstring(b"<count>ordinary</count>", xml_parser())))

    def test_current_html5lib_lxml_builder(self):
        self.assertEqual(html5lib.__version__, "1.1")
        document = html5lib.parse("<title>Report</title><p>中文 &amp; tea</p>", treebuilder="lxml")
        ns = {"h": "http://www.w3.org/1999/xhtml"}
        self.assertEqual(document.xpath("string(//h:title)", namespaces=ns), "Report")
        self.assertEqual(document.xpath("string(//h:p)", namespaces=ns), "中文 & tea")

    def test_current_html5lib_lxml_walker(self):
        document = html5lib.parse("<p>ordinary words</p>", treebuilder="lxml")
        tokens = list(html5lib.getTreeWalker("lxml")(document))
        self.assertTrue(any(token.get("data") == "ordinary words" for token in tokens))

    def test_current_html5lib_lxml_serialization(self):
        document = html5lib.parse('<p title="ordinary words">x &amp; y</p>', treebuilder="lxml")
        output = html5lib.serialize(document, tree="lxml", quote_attr_values="always")
        self.assertIn('<p title="ordinary words">x &amp; y', output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
