# -*- coding: utf-8 -*-
from unittest import main, TestCase

from sklearn.feature_extraction.text import TfidfVectorizer

from simhash import Simhash, SimhashIndex


class TestSimhash(TestCase):

    def test_int_value(self):
        self.assertEqual(0, Simhash(0).value)
        self.assertEqual(4390059585430954713, Simhash(4390059585430954713).value)
        self.assertEqual(9223372036854775808, Simhash(9223372036854775808).value)

    def test_value(self):
        self.assertEqual(57087923692560392, Simhash(['aaa', 'bbb']).value)

    def test_distance(self):
        sh = Simhash('How are you? I AM fine. Thanks. And you?')
        sh2 = Simhash('How old are you ? :-) i am fine. Thanks. And you?')
        self.assertTrue(sh.distance(sh2) > 0)

        sh3 = Simhash(sh2)
        self.assertEqual(0, sh2.distance(sh3))

        self.assertNotEqual(0, Simhash('1').distance(Simhash('2')))

    def test_chinese(self):
        self.maxDiff = None

        sh1 = Simhash(u'你好　世界！　　呼噜。')
        sh2 = Simhash(u'你好，世界　呼噜')

        sh4 = Simhash(u'How are you? I Am fine. ablar ablar xyz blar blar blar blar blar blar blar Thanks.')
        sh5 = Simhash(u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar than')
        sh6 = Simhash(u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar thank')

        self.assertEqual(0, sh1.distance(sh2))

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
        voc = dict((i, w) for w, i in vec.vocabulary_.items())

        # Verify that distance between data[0] and data[1] is < than
        # data[2] and data[3]
        shs = []
        for i in range(D.shape[0]):
            Di = D.getrow(i)
            # features as list of (token, weight) tuples)
            features = zip([voc[j] for j in Di.indices], Di.data)
            shs.append(Simhash(features))
        self.assertNotEqual(0, shs[0].distance(shs[1]))
        self.assertNotEqual(0, shs[2].distance(shs[3]))
        self.assertLess(shs[0].distance(shs[1]), shs[2].distance(shs[3]))

        # features as token -> weight dicts
        D0 = D.getrow(0)
        dict_features = dict(zip([voc[j] for j in D0.indices], D0.data))
        self.assertEqual(17583409636488780916, Simhash(dict_features).value)

        # the sparse and non-sparse features should obviously yield
        # different results
        self.assertNotEqual(Simhash(dict_features).value,
                            Simhash(data[0]).value)

    def test_equality_comparison(self):
        a = Simhash('My name is John')
        b = Simhash('My name is John')
        c = Simhash('My name actually is Jane')

        self.assertEqual(a, b, 'A should equal B')
        self.assertNotEqual(a, c, 'A should not equal C')


class TestSimhashIndex(TestCase):
    data = {
        1: 'How are you? I Am fine. blar blar blar blar blar Thanks.',
        2: 'How are you i am fine. blar blar blar blar blar than',
        3: 'This is simhash test.',
        4: 'How are you i am fine. blar blar blar blar blar thank1',
    }

    def setUp(self):
        objs = [(str(k), Simhash(v)) for k, v in self.data.items()]
        self.index = SimhashIndex(objs, k=10)

    def test_get_near_dup(self):
        s1 = Simhash(u'How are you i am fine.ablar ablar xyz blar blar blar blar blar blar blar thank')
        dups = self.index.get_near_dups(s1)
        self.assertEqual(3, len(dups))

        self.index.delete('1', Simhash(self.data[1]))
        dups = self.index.get_near_dups(s1)
        self.assertEqual(2, len(dups))

        self.index.delete('1', Simhash(self.data[1]))
        dups = self.index.get_near_dups(s1)
        self.assertEqual(2, len(dups))

        self.index.add('1', Simhash(self.data[1]))
        dups = self.index.get_near_dups(s1)
        self.assertEqual(3, len(dups))

        self.index.add('1', Simhash(self.data[1]))
        dups = self.index.get_near_dups(s1)
        self.assertEqual(3, len(dups))


if __name__ == '__main__':
    main()
