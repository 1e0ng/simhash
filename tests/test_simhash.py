# -*- coding: utf-8 -*-
from unittest import main, TestCase

from simhash import Simhash

class TestSegmentTree(TestCase):
    def test_segtree(self):
        sh = Simhash('How are you? I am fine. Thanks. And you?')
        self.assertEqual(sh.value, 6460601123240241099)

        sh2 = Simhash('How old are you ? :-) I am fine. Thanks. And you?')
        self.assertEqual(sh.distance(sh2), 9)

        sh3 = Simhash(sh2)
        self.assertEqual(sh2.distance(sh3), 0)


if __name__ == '__main__':
    main()
