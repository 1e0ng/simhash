# -*- coding: utf-8 -*-
from unittest import main, TestCase

from simhash import Simhash, SimhashIndex

class TestSimhash(TestCase):
    def test_distance(self):
        sh = Simhash('How are you? I AM fine. Thanks. And you?')
        sh2 = Simhash('How old are you ? :-) i am fine. Thanks. And you?')
        self.assertTrue(sh.distance(sh2) > 0)

        sh3 = Simhash(sh2)
        self.assertEqual(sh2.distance(sh3), 0)

        self.assertNotEqual(Simhash('1').distance(Simhash('2')), 0)

    def test_chinese(self):
        self.maxDiff = None

        sh1 = Simhash(u'你好　世界！　　呼噜。')
        sh2 = Simhash(u'你好，世界　呼噜')

        sh4 = Simhash(u'How are you? I Am fine. ablar ablar xyz blar blar blar blar blar blar blar Thanks.')
        sh5 = Simhash(u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar than')
        sh6 = Simhash(u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar thank')

        self.assertEqual(sh1.distance(sh2), 0)

        self.assertTrue(sh4.distance(sh6) < 3)
        self.assertTrue(sh5.distance(sh6) < 3)


    def test_short(self):
        sh1 = Simhash('aa')
        sh2 = Simhash('aaa')

        self.assertNotEqual(sh1.value, sh2.value)


class TestSimhashIndex(TestCase):
    def setUp(self):
        data = {
            1: u'How are you? I Am fine. ablar ablar xyz blar blar blar blar blar blar blar Thanks.',
            2: u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar than',
            3: u'This is a different one.',
        }
        objs = [(str(k), Simhash(v)) for k, v in data.items()]
        self.index = SimhashIndex(objs)

    def test_get_near_dup(self):
        s1 = Simhash(u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar thank')
        dups = self.index.get_near_dups(s1)

        self.assertEqual(len(dups), 2)


if __name__ == '__main__':
    main()
