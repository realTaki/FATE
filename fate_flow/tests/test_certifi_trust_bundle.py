"""Offline stdlib-only checks for the project's pinned certifi release.

Run with the requirements-installed interpreter; no network or FATE service
is started. This checks the mapped e-Tugra removal, not all CA-store risks.
"""
import os
import ssl
import unittest

import certifi


class CertifiTrustBundleTest(unittest.TestCase):
    def test_python36_compatible_release_is_installed(self):
        self.assertEqual("2025.04.26", certifi.__version__)

    def test_where_and_contents_agree(self):
        self.assertTrue(os.path.isfile(certifi.where()))
        with open(certifi.where(), encoding="ascii") as bundle:
            self.assertEqual(bundle.read(), certifi.contents())

    def test_bundle_loads_without_removed_e_tugra_roots(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.load_verify_locations(cafile=certifi.where())
        certificates = context.get_ca_certs()
        self.assertGreater(len(certificates), 100)
        for certificate in certificates:
            for field in ("subject", "issuer"):
                for rdn in certificate.get(field, ()):
                    for key, value in rdn:
                        self.assertNotIn("e-tugra", value.lower())


if __name__ == "__main__":
    unittest.main()
