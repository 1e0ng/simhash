# -*- coding: utf-8 -*-
from unittest import main, TestCase

from simhash import Simhash

class TestSegmentTree(TestCase):
    def test_segtree(self):
        sh = Simhash('How are you? I AM fine. Thanks. And you?')
        #self.assertEqual(sh._features, [])
        self.assertEqual(sh.value, 8704894745043123761L)

        sh2 = Simhash('How old are you ? :-) i am fine. Thanks. And you?')
        self.assertEqual(sh.distance(sh2), 9)

        sh3 = Simhash(sh2)
        self.assertEqual(sh2.distance(sh3), 0)

        self.assertNotEqual(Simhash('1').distance(Simhash('2')), 0)

    def test_chinese(self):
        sh1 = Simhash(u'你好　世界！　　呼噜。')
        sh2 = Simhash(u'你好，世界　呼噜')

        #self.assertEqual(sh1._features, [])
        self.assertEqual(sh1.distance(sh2), 0)


if __name__ == '__main__':
    main()
