# Created by Liang Sun in 2013
from __future__ import division, unicode_literals

import sys
import re
import hashlib
import logging
from collections import defaultdict, Iterable
from scipy.sparse import csr_matrix


if sys.version_info[0] >= 3:
    basestring = str
    unicode = str
    long = int
else:
    range = xrange


class Simhash(object):

    def __init__(self, value, f=64, reg=r'[\w\u4e00-\u9fcc]+', hashfunc=None,
                 sparse_voc=None):
        """
        `f` is the dimensions of fingerprints

        `reg` is meaningful only when `value` is basestring and describes
        what is considered to be a letter inside parsed string. Regexp
        object can also be specified (some attempt to handle any letters
        is to specify reg=re.compile(r'\w', re.UNICODE))

        `hashfunc` accepts a utf-8 encoded string and returns a unsigned
        integer in at least `f` bits.

        `sparse_voc` is a word->index dict to use with sparse features.
        """

        self.f = f
        self.reg = reg
        self.value = None

        if hashfunc is None:
            def _hashfunc(x):
                return int(hashlib.md5(x).hexdigest(), 16)

            self.hashfunc = _hashfunc
        else:
            self.hashfunc = hashfunc

        if isinstance(value, Simhash):
            self.value = value.value
        elif isinstance(value, basestring):
            self.build_by_text(unicode(value))
        elif isinstance(value, csr_matrix):
            self.build_by_sparse_features(value, sparse_voc)
        elif isinstance(value, Iterable):
            self.build_by_features(value)
        elif isinstance(value, long):
            self.value = value
        else:
            raise Exception('Bad parameter with type {}'.format(type(value)))

    def _slide(self, content, width=4):
        return [content[i:i + width]
                for i in range(max(len(content) - width + 1, 1))]

    def _tokenize(self, content):
        content = content.lower()
        content = ''.join(re.findall(self.reg, content))
        ans = self._slide(content)
        return ans

    def build_by_text(self, content):
        features = self._tokenize(content)
        return self.build_by_features(features)

    def build_by_features(self, features):
        hashs = [self.hashfunc(w.encode('utf-8')) for w in features]
        v = [0] * self.f
        masks = [1 << i for i in range(self.f)]
        for h in hashs:
            for i in range(self.f):
                v[i] += 1 if h & masks[i] else -1
        ans = 0
        for i in range(self.f):
            if v[i] >= 0:
                ans |= masks[i]
        self.value = ans

    def build_by_sparse_features(self, features, voc=None):
        """
        Use TFIDF weights in the SimHash signature computation, instead
        of simply -1/1 as with non-sparse version.

        `features` must be either a str->float dict or a 1 x
        n_features csr_matrix row.

        `voc` if specified, must be a str->index dict, if not, the feature
        index as string will be used (because the hash function expects a
        string).
        """

        if isinstance(features, csr_matrix):
            assert features.shape[0] == 1  # make sure it's a sparse row
            features = dict(zip(features.indices, features.data))
        assert isinstance(features, dict), \
            'features must be a dict or csr_matrix sparse row'
        if voc:
            features = {voc[i]: w for i, w in features.items()}
        else:
            features = {str(i): w for i, w in features.items()}

        hashs = [(self.hashfunc(t.encode('utf-8')), w)
                 for t, w in features.items()]
        v = [0] * self.f
        masks = [1 << i for i in range(self.f)]
        for h, w in hashs:
            for i in range(self.f):
                v[i] += w if h & masks[i] else -w
        ans = 0
        for i in range(self.f):
            if v[i] >= 0:
                ans |= masks[i]
        self.value = ans

    def distance(self, another):
        assert self.f == another.f
        x = (self.value ^ another.value) & ((1 << self.f) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x - 1
        return ans


class SimhashIndex(object):

    def get_near_dupes(self, simhash):
        """
        `simhash` is an instance of Simhash
        return a list of obj_id, which is in type of str
        """
        assert simhash.f == self.f

        ans = set()

        for key in self.get_keys(simhash):
            dups = self.bucket.get(key, set())
            logging.debug('key:%s', key)
            if len(dups) > 200:
                logging.warning('Big bucket found. key:%s, len:%s',
                                key, len(dups))

            for dup in dups:
                sim2, obj_id = dup.split(',', 1)
                sim2 = Simhash(long(sim2, 16), self.f)

                d = simhash.distance(sim2)
                if d <= self.k:
                    ans.add((obj_id, d))
        return ans

    def add(self, obj_id, simhash):
        """
        `obj_id` is a string
        `simhash` is an instance of Simhash
        """
        assert simhash.f == self.f

        for key in self.get_keys(simhash):
            v = '%x,%s' % (simhash.value, obj_id)
            self.bucket[key].add(v)

    def delete(self, obj_id, simhash):
        """
        `obj_id` is a string
        `simhash` is an instance of Simhash
        """
        assert simhash.f == self.f

        for key in self.get_keys(simhash):
            v = '%x,%s' % (simhash.value, obj_id)

            if v in self.bucket.get(key, set()):
                self.bucket[key].remove(v)

    def __init__(self, objs, f=64, k=2):
        """
        `objs` is a list of (obj_id, simhash)
        obj_id is a string, simhash is an instance of Simhash
        `f` is the same with the one for Simhash
        `k` is the tolerance
        """
        self.k = k
        self.f = f
        count = len(objs)
        logging.info('Initializing %s data.', count)

        self.bucket = defaultdict(set)

        for i, q in enumerate(objs):
            if i % 10000 == 0 or i == count - 1:
                logging.info('%s/%s', i + 1, count)

            self.add(*q)

    @property
    def offsets(self):
        """
        You may optimize this method according to
        <http://www.wwwconference.org/www2007/papers/paper215.pdf>
        """
        return [self.f // (self.k + 1) * i for i in range(self.k + 1)]

    def get_keys(self, simhash):
        for i, offset in enumerate(self.offsets):
            m = (i == len(self.offsets) - 1 and 2 ** (self.f - offset) - 1 or
                 2 ** (self.offsets[i + 1] - offset) - 1)
            c = simhash.value >> offset & m
            yield '%x:%x' % (c, i)

    def bucket_size(self):
        return len(self.bucket)


if __name__ == '__main__':

    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer()
    data = [
        u'How are you? I Am fine. blar blar blar blar blar Thanks.',
        u'How are you i am fine. blar blar blar blar blar than',
        u'This is simhash test.'
    ]
    D = vec.fit_transform(data)
    voc = {w: i for i, w in vec.vocabulary_.items()}
    for i in range(D.shape[0]):
        print('shingles=%d, tfidf-no-voc=%d, tfidf-with-voc=%d' %
              (Simhash(data[i]).value, Simhash(D.getrow(i)).value,
               Simhash(D.getrow(i), sparse_voc=voc).value))
