"""Ordinary offline RSA compatibility; explicit FATE class-source isolation.

This does not import the whole legacy FATE application or exercise attacks.
It compiles the unchanged Encrypt/RsaEncrypt class AST and their real
Cryptodome imports, avoiding unrelated ML/Paillier dependencies. In particular,
keyed RsaEncrypt.encrypt/decrypt (which require gmpy2) are not tested here.
"""
import ast
import pathlib
import sys
import unittest

import cffi
import Cryptodome
import pycparser
from Cryptodome import Random
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
from Cryptodome.Util import _raw_api


def load_actual_rsa_classes():
    path = pathlib.Path(__file__).resolve().parents[2] / "federatedml" / "secureprotol" / "encrypt.py"
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    selected = []
    classes = set()
    imports = set()
    for node in module.body:
        if isinstance(node, ast.ImportFrom) and node.module in ("Cryptodome", "Cryptodome.PublicKey"):
            selected.append(node)
            imports.add((node.module, tuple((item.name, item.asname) for item in node.names)))
        elif isinstance(node, ast.ClassDef) and node.name in ("Encrypt", "RsaEncrypt"):
            selected.append(node)
            classes.add(node.name)
    if classes != {"Encrypt", "RsaEncrypt"} or imports != {
            ("Cryptodome", (("Random", None),)),
            ("Cryptodome.PublicKey", (("RSA", None),))}:
        raise AssertionError("Actual FATE RSA class/import layout changed")
    subset = ast.Module(body=selected)
    if "type_ignores" in ast.Module._fields:
        subset.type_ignores = []
    # No AST rewriting, replacement math functions, mocks, or sys.modules shims.
    namespace = {"__name__": "fate_actual_rsa_class_source_compatibility"}
    exec(compile(ast.fix_missing_locations(subset), str(path), "exec"), namespace)
    return namespace


class PycryptodomexRsaCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.actual = load_actual_rsa_classes()
        cls.rsa_class = cls.actual["RsaEncrypt"]
        cls.generated = cls.rsa_class()
        # Exercise the unchanged production default and exact Random.new().read
        # callback -> RSA.generate -> .e/.d/.n attribute consumption.
        cls.generated.generate_key()

    def test_real_library_imports_and_random_callback(self):
        self.assertIn(Cryptodome.__version__, ("3.6.6", "3.19.1"))
        self.assertIs(self.actual["Random"], Random)
        self.assertIs(self.actual["RSA"], RSA)
        data = Random.new().read(32)
        self.assertIsInstance(data, bytes)
        self.assertEqual(len(data), 32)

    def test_existing_declared_cffi_backend(self):
        # Both upstream versions automatically prefer this real dependency,
        # already pinned by FATE. No backend is forced or replaced by the test.
        self.assertEqual(cffi.__version__, "1.11.5")
        self.assertEqual(pycparser.__version__, "2.19")
        self.assertEqual(_raw_api.backend, "cffi")

    def test_actual_default_key_generation_and_attributes(self):
        e, d, n = self.generated.get_key_pair()
        self.assertEqual(e, 65537)
        self.assertEqual(n.bit_length(), 1024)
        self.assertGreater(d, 0)
        self.assertEqual(self.generated.get_public_key(), (e, n))
        self.assertEqual(self.generated.get_privacy_key(), (d, n))

    def test_generated_tuple_ordinary_integer_round_trip(self):
        # Independent mathematical compatibility control, NOT a claim to call
        # the gmpy2-backed keyed RsaEncrypt.encrypt/decrypt wrapper.
        e, d, n = self.generated.get_key_pair()
        for value in (0, 1, 2, 42, 256, 123456):
            self.assertEqual(pow(pow(value, e, n), d, n), value)

    def test_actual_public_private_key_setters(self):
        e, d, n = self.generated.get_key_pair()
        public = self.rsa_class()
        private = self.rsa_class()
        public.set_public_key({"e": e, "n": n})
        private.set_privacy_key({"d": d, "n": n})
        self.assertEqual(public.get_public_key(), (e, n))
        self.assertEqual(private.get_privacy_key(), (d, n))

    def test_actual_uninitialized_behavior(self):
        empty = self.rsa_class()
        self.assertEqual(empty.get_key_pair(), (None, None, None))
        self.assertIsNone(empty.encrypt(42))
        self.assertIsNone(empty.decrypt(42))
        self.assertEqual(empty.encrypt_list([1, 2]), [None, None])
        self.assertEqual(empty.decrypt_list([1, 2]), [None, None])

    def test_library_key_reconstruction_and_memory_only_serialization(self):
        e, d, n = self.generated.get_key_pair()
        key = RSA.construct((n, e, d))
        private_copy = RSA.import_key(key.export_key())
        public_copy = RSA.import_key(key.publickey().export_key())
        self.assertEqual((private_copy.n, private_copy.e, private_copy.d), (n, e, d))
        self.assertEqual((public_copy.n, public_copy.e), (n, e))
        self.assertFalse(public_copy.has_private())

    def test_library_ordinary_oaep_round_trip(self):
        # Valid, locally generated ciphertext only. No malformed input, timing,
        # side-channel, oracle, attack fixture, network, or persisted private key.
        e, d, n = self.generated.get_key_pair()
        key = RSA.construct((n, e, d))
        message = b"ordinary synthetic compatibility message"
        ciphertext = PKCS1_OAEP.new(key.publickey()).encrypt(message)
        self.assertEqual(len(ciphertext), 128)
        self.assertEqual(PKCS1_OAEP.new(key).decrypt(ciphertext), message)

    def test_actual_explicit_2048_bit_generation(self):
        larger = self.rsa_class()
        larger.generate_key(2048)
        e, d, n = larger.get_key_pair()
        self.assertEqual(n.bit_length(), 2048)
        self.assertEqual(e, 65537)
        self.assertEqual(pow(pow(42, e, n), d, n), 42)


if __name__ == "__main__":
    print("Runtime:", sys.version)
    print("Cryptodome:", Cryptodome.__version__, Cryptodome.__file__)
    unittest.main(verbosity=2)
