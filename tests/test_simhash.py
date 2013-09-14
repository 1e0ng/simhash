# -*- coding: utf-8 -*-
from unittest import main, TestCase

from simhash import simhash

class TestSegmentTree(TestCase):
    def test_segtree(self):
        h = simhash('How are you?')
        self.assertEqual(h, 3572563133985320957)

if __name__ == '__main__':
    main()
