import unittest

from app.auth.bloom_filter import BloomFilter


class BloomFilterTestCase(unittest.TestCase):
    def test_might_contains(self):
        # arrange
        bloom_filter = BloomFilter.create_from_expected_n(n=2)
        bloom_filter.put("foo")
        bloom_filter.put("baz")

        # act & assert
        self.assertTrue(bloom_filter.might_contains("foo"))
        self.assertFalse(bloom_filter.might_contains("bar"))
        self.assertTrue(bloom_filter.might_contains("baz"))
