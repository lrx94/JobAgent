import unittest

from src.providers.registry import ProviderRegistry


class FakeProvider:
    """Provider de test."""

    name = "Fake Provider"

    def search(self, request):
        return []


class OtherProvider:
    """Provider sans attribut 'name'."""

    def search(self, request):
        return []


class InvalidProvider:
    """Provider invalide (pas de méthode search)."""
    pass


class TestProviderRegistry(unittest.TestCase):

    def test_registers_provider(self):
        provider = FakeProvider()

        registry = ProviderRegistry([provider])

        self.assertEqual(len(registry), 1)
        self.assertIs(
            registry.get("Fake Provider"),
            provider,
        )

    def test_does_not_register_duplicate(self):
        registry = ProviderRegistry()

        registry.register(FakeProvider())
        registry.register(FakeProvider())

        self.assertEqual(len(registry), 1)

    def test_uses_class_name_when_name_missing(self):
        registry = ProviderRegistry(
            [OtherProvider()]
        )

        self.assertEqual(
            registry.names(),
            ["OtherProvider"],
        )

    def test_unregisters_provider(self):
        provider = FakeProvider()

        registry = ProviderRegistry([provider])

        removed = registry.unregister(provider)

        self.assertTrue(removed)
        self.assertEqual(len(registry), 0)

    def test_clear(self):
        registry = ProviderRegistry(
            [
                FakeProvider(),
                OtherProvider(),
            ]
        )

        registry.clear()

        self.assertEqual(len(registry), 0)

    def test_rejects_none(self):
        registry = ProviderRegistry()

        with self.assertRaises(ValueError):
            registry.register(None)

    def test_rejects_invalid_provider(self):
        registry = ProviderRegistry()

        with self.assertRaises(TypeError):
            registry.register(InvalidProvider())


if __name__ == "__main__":
    unittest.main()