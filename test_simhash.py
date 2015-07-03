# -*- coding: utf-8 -*-
from unittest import main, TestCase
from sklearn.feature_extraction.text import TfidfVectorizer
from simhash import Simhash, SimhashIndex


class TestSimhash(TestCase):

    def test_value(self):
        self.assertEqual(Simhash(['aaa', 'bbb']).value, 8637903533912358349)

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
        shs = [Simhash(s).value for s in ('aa', 'aaa', 'aaaa', 'aaaab', 'aaaaabb', 'aaaaabbb')]

        for i, sh1 in enumerate(shs):
            for j, sh2 in enumerate(shs):
                if i != j:
                    self.assertNotEqual(sh1, sh2)

    def test_sparse_features(self):
        data = [
            'How are you? I Am fine. blar blar blar blar blar Thanks.',
            'How are you i am fine. blar blar blar blar blar than',
            'This is simhash test.',
            'How are you i am fine. blar blar blar blar blar thank1'
        ]
        vec = TfidfVectorizer()
        D = vec.fit_transform(data)
        voc = {i: w for w, i in vec.vocabulary_.items()}
        for i in range(D.shape[0]):
            Di = D.getrow(i)
            features = zip([voc[j] for j in Di.indices], Di.data)
            self.assertNotEqual(Simhash(features).value, 0)


class TestSimhashIndex(TestCase):

    data = {
        1: 'How are you? I Am fine. blar blar blar blar blar Thanks.',
        2: 'How are you i am fine. blar blar blar blar blar than',
        3: 'This is simhash test.',
        4: 'How are you i am fine. blar blar blar blar blar thank1'
    }

    def setUp(self):
        objs = [(str(k), Simhash(v)) for k, v in self.data.items()]
        self.index = SimhashIndex(objs, k=10)

    def test_get_near_dupes(self):
        s1 = Simhash(u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar thank')
        dupes = self.index.get_near_dupes(s1)

        # This is because get_near_dupes now returns a list of
        # (obj_id, dist) tuples
        self.assertTrue(isinstance(list(dupes)[0], tuple))
        self.assertEqual(len(list(dupes)[0]), 2)

        self.assertEqual(len(dupes), 3)

        self.index.delete('1', Simhash(self.data[1]))
        dupes = self.index.get_near_dupes(s1)
        self.assertEqual(len(dupes), 2)

        self.index.delete('1', Simhash(self.data[1]))
        dupes = self.index.get_near_dupes(s1)
        self.assertEqual(len(dupes), 2)

        self.index.add('1', Simhash(self.data[1]))
        dupes = self.index.get_near_dupes(s1)
        self.assertEqual(len(dupes), 3)

        self.index.add('1', Simhash(self.data[1]))
        dupes = self.index.get_near_dupes(s1)
        self.assertEqual(len(dupes), 3)


if __name__ == '__main__':
    main()
