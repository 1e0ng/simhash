# -*- coding: utf-8 -*-
from unittest import main, TestCase

from simhash import Simhash, SimhashIndex


class TestSimhash(TestCase):
    def test_value(self):
        # Test 64 bit fingerprint.
        sh = Simhash('How are you? I AM fine. Thanks. And you?', f=64)
        #self.assertEqual(sh._features, [])
        self.assertEqual(sh.value, 6560575042654586091L)

        # Test 32 bit fingerprint.
        sh = Simhash('How are you? I AM fine. Thanks. And you?', f=32)
        self.assertEqual(sh.value, 3954722027L)

    def test_distance(self):
        sh = Simhash('How are you? I AM fine. Thanks. And you?')
        sh2 = Simhash('How old are you ? :-) i am fine. Thanks. And you?')
        self.assertEqual(sh.distance(sh2), 7)

        # Test that simhash constructed from another simhash has distance 0.
        sh3 = Simhash(sh2)
        self.assertEqual(sh2.distance(sh3), 0)

        self.assertNotEqual(Simhash('1').distance(Simhash('2')), 0)

        # 32 bit
        sh = Simhash('How are you? I AM fine. Thanks. And you?', f=32)
        sh2 = Simhash('How old are you ? :-) i am fine. Thanks. And you?',
                      f=32)
        self.assertEqual(sh.distance(sh2), 3)

        # Test that same string gives 0 simhash distance.
        sh2 = Simhash('How are you? I AM fine. Thanks. And you?', f=32)
        self.assertEqual(sh.distance(sh2), 0)

        # Test that same string but different bits raises exception.
        sh2 = Simhash('How are you? I AM fine. Thanks. And you?', f=64)
        with self.assertRaises(ValueError):
            sh.distance(sh2)

    def test_chinese(self):
        sh1 = Simhash(u'你好　世界！　　呼噜。')
        sh2 = Simhash(u'你好，世界　呼噜')

        #self.assertEqual(sh1._features, [])
        self.assertEqual(sh1.distance(sh2), 0)


class Test64BitSimhashIndex(TestCase):
    def setUp(self):
        data = {
            1: u'How are you? I Am fine. blar blar blar blar blar Thanks.',
            2: u'How are you i am fine. blar blar blar blar blar than',
            3: u'This is simhash test.',
        }
        objs = [(str(k), Simhash(v, f=64)) for k, v in data.items()]
        self.index = SimhashIndex(objs)

    def test_bucket_size(self):
        self.assertEqual(self.index.bucket_size(), 6)

    def test_get_near_dup(self):
        s1 = Simhash(u'How are you i am fine. blar blar blar blar blar thank')
        dups = self.index.get_near_dups(s1)

        self.assertEqual(len(dups), 2)


class Test32BitSimhashIndex(TestCase):
    def setUp(self):
        data = {
            1: u'How are you? I Am fine. blar blar blar blar blar Thanks.',
            2: u'How are you i am fine. blar blar blar blar blar than',
            3: u'This is simhash test.',
        }
        objs = [(str(k), Simhash(v, f=32)) for k, v in data.items()]
        self.index = SimhashIndex(objs)

    def test_bucket_size(self):
        self.assertEqual(self.index.bucket_size(), 6)

    def test_get_near_dup(self):
        s1 = Simhash(u'How are you i am fine. blar blar blar blar blar thank',
                     f=32)
        dups = self.index.get_near_dups(s1)

        self.assertEqual(len(dups), 2)


if __name__ == '__main__':
    main()
