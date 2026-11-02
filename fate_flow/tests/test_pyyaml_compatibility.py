"""Ordinary YAML API compatibility for the exact FATE PyYAML dependency.

Keras 2.2.4 declares PyYAML and its model_from_yaml calls yaml.load(stream)
without Loader=. Test that legacy call with plain model configuration data;
this does not initialize Keras/TensorFlow or execute arbitrary YAML objects.
"""
import datetime
import io
import sys
import unittest
import warnings

import yaml


def legacy_load(stream):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", getattr(yaml, "YAMLLoadWarning", Warning))
        return yaml.load(stream)


class PyYamlCompatibilityTest(unittest.TestCase):
    def test_exact_security_pin(self):
        self.assertEqual(yaml.__version__, "5.4.1")

    def test_safe_nested_configuration(self):
        text = "worker:\n  enabled: true\n  retries: 3\n  rate: 0.25\n  missing: null\n  labels: [guest, host]\n"
        self.assertEqual(yaml.safe_load(text), {
            "worker": {"enabled": True, "retries": 3, "rate": 0.25,
                       "missing": None, "labels": ["guest", "host"]}})

    def test_unicode_and_stream_inputs(self):
        text = "name: \u6d4b\u8bd5\nroles: [guest, host]\n"
        expected = {"name": "\u6d4b\u8bd5", "roles": ["guest", "host"]}
        self.assertEqual(yaml.safe_load(io.StringIO(text)), expected)
        self.assertEqual(yaml.safe_load(io.BytesIO(text.encode("utf-8"))), expected)

    def test_safe_dump_roundtrip(self):
        config = {"name": "ordinary", "layers": [{"units": 3}, {"units": 1}],
                  "enabled": False, "optional": None, "ratio": 0.125}
        encoded = yaml.safe_dump(config, default_flow_style=False)
        self.assertEqual(yaml.safe_load(encoded), config)

    def test_legacy_keras_model_configuration_call(self):
        config = {"class_name": "Sequential", "config": [
            {"class_name": "Dense", "config": {
                "units": 3, "activation": "relu", "dtype": "float32",
                "batch_input_shape": (None, 12), "trainable": True}}]}
        # Exactly the legacy consumer's parser call, with ordinary data only.
        self.assertEqual(legacy_load(yaml.dump(config)), config)

    def test_small_configuration_anchor_merge(self):
        text = "defaults: &base {epochs: 2, enabled: true}\ntraining:\n  <<: *base\n  epochs: 4\n"
        self.assertEqual(yaml.safe_load(text), {
            "defaults": {"epochs": 2, "enabled": True},
            "training": {"epochs": 4, "enabled": True}})

    def test_multiple_document_order(self):
        self.assertEqual(list(yaml.safe_load_all("name: first\n---\nname: second\n")),
                         [{"name": "first"}, {"name": "second"}])

    def test_binary_and_date_values(self):
        config = {"blob": b"small ordinary bytes", "date": datetime.date(2026, 11, 2)}
        self.assertEqual(yaml.safe_load(yaml.safe_dump(config)), config)

    def test_empty_and_malformed_input(self):
        self.assertIsNone(yaml.safe_load(""))
        self.assertIsNone(legacy_load(""))
        with self.assertRaises(yaml.YAMLError):
            yaml.safe_load("shape: [1,\n")


if __name__ == "__main__":
    unittest.main()
