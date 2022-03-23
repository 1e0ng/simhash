# -*- coding: utf-8 -*-
import hashlib
from unittest import main, TestCase

from sklearn.feature_extraction.text import TfidfVectorizer

from simhash import Simhash, SimhashIndex, determine_clusters


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

    def test_custom_hashfunc(self):
        def int_hashfunc(x):
            return int(hashlib.md5(x).hexdigest(), 16)

        def sha_hashfunc(x):
            return hashlib.sha256(x).digest()

        a = Simhash('My name is John')
        b = Simhash('My name is John', hashfunc=int_hashfunc)
        c = Simhash('My name is John', hashfunc=sha_hashfunc)

        self.assertEqual(a, b, 'hashfunc returning int should have the same output as default hashfunc returning bytes')
        self.assertNotEqual(a, c, 'custom hashfunc should return different result from default hashfunc')

    def test_large_inputs(self):
        """ Test code paths for dealing with feature lists larger than batch_size, and weights larger than large_weight_cutoff. """
        many_features = [str(i) for i in range(int(Simhash.batch_size * 2.5))]
        many_features_large_weights = [(f, Simhash.large_weight_cutoff * i) for i, f in enumerate(many_features)]
        self.assertEqual(7984652473404407437, Simhash(many_features).value)
        self.assertEqual(3372825719632739723, Simhash(many_features_large_weights).value)


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


class TestDetermineClusters(TestCase):
    data = {
        1: 'How are you? I Am fine. blar blar blar blar blar Thanks.',
        2: 'How are you? I Am fine. blar blar blar blar blar Thanks.',
        3: 'This is simhash test.',
        4: 'How are you i am fine. blar blar blar blar blar thank1',
    }

    def setUp(self):
        self.objs = [(str(k), Simhash(v)) for k, v in self.data.items()]

    def test_exact_match_same_cluster(self):
        expected_cluster = {'1', '2'}
        index = SimhashIndex(self.objs, k=1)
        clusters = determine_clusters(index, self.objs)
        self.assertEqual((clusters[0] - expected_cluster), set())
        self.assertEqual((expected_cluster - clusters[0]), set())
        self.assertEqual(len(clusters), 3)

    def test_approximate_match_same_cluster(self):
        expected_cluster = {'1', '2', '4'}
        index = SimhashIndex(self.objs, k=4)
        clusters = determine_clusters(index, self.objs)
        self.assertEqual((clusters[0] - expected_cluster), set())
        self.assertEqual((expected_cluster - clusters[0]), set())
        self.assertEqual(len(clusters), 2)


if __name__ == '__main__':
    main()
