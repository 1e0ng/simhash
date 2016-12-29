# Created by 1e0n in 2013
from __future__ import division, unicode_literals

import sys
import re
import hashlib
import logging
import collections
from itertools import groupby

if sys.version_info[0] >= 3:
    basestring = str
    unicode = str
    long = int
else:
    range = xrange


def _hashfunc(x):
    return int(hashlib.md5(x).hexdigest(), 16)


class Simhash(object):

    def __init__(self, value=None, f=64, reg=r'[\w\u4e00-\u9fcc]+', hashfunc=None):
        """
        `f` is the dimensions of fingerprints

        `reg` is meaningful only when `value` is basestring and describes
        what is considered to be a letter inside parsed string. Regexp
        object can also be specified (some attempt to handle any letters
        is to specify reg=re.compile(r'\w', re.UNICODE))

        `hashfunc` accepts a utf-8 encoded string and returns a unsigned
        integer in at least `f` bits.
        """

        self.f = f
        self.reg = reg
        self._hash = None
        self.features = collections.Counter()
        self.buffer = ''

        if hashfunc is None:
            self.hashfunc = _hashfunc
        else:
            self.hashfunc = hashfunc

        if isinstance(value, Simhash):
            self._hash = value._hash
        elif isinstance(value, basestring):
            self.update(unicode(value))
        elif isinstance(value, collections.Iterable):
            self.update(value)
        elif isinstance(value, long):
            self._hash = value
        elif value is None:
            pass
        else:
            raise Exception('Bad parameter with type {}'.format(type(value)))

    def _slide(self, content, width=4):
        return [content[i:i + width] for i in range(max(len(content) - width + 1, 1))]

    def _tokenize(self, content):
        content = content.lower()
        content = ''.join(re.findall(self.reg, content))
        ans = self._slide(content)
        return ans

    def update(self, features):
        """
        `features` might be a list of unweighted tokens (a weight of 1
                   will be assumed), a list of (token, weight) tuples, a
                   token -> weight dict or a string.
        """
        if isinstance(features, (str, unicode)):
            # If we receive a string, we will prepend our buffer, tokenize the
            # result, and withhold the last token in our buffer.
            if self.buffer:
                features = self.buffer + features
            if not features:
                return
            features = self._tokenize(features)
            self.buffer = features.pop()
            features = {k:sum(1 for _ in g) for k, g in groupby(sorted(features))}
        if isinstance(features, dict):
            features = features.items()
        for f in features:
            if isinstance(f, basestring):
                h = f.encode('utf-8')
                w = 1
            else:
                assert isinstance(f, collections.Iterable)
                h = f[0].encode('utf-8')
                w = f[1]
            self.features[h] += w

    # Preserve old interface.
    build_by_features = update
    build_by_text = update

    def finalize(self):
        if self.buffer:
            # Flush and clear the buffer.
            self.update([self.buffer])
            self.buffer = ''
        v = [0] * self.f
        masks = [1 << i for i in range(self.f)]
        for h, w in self.features.items():
            h = self.hashfunc(h)
            for i in range(self.f):
                v[i] += w if h & masks[i] else -w
        ans = 0
        for i in range(self.f):
            if v[i] >= 0:
                ans |= masks[i]
        self._hash = ans
        # Remove the features we have accumulated.
        self.features.clear()

    @property
    def value(self):
        if self._hash is None:
            self.finalize()
        return self._hash

    def distance(self, another):
        assert self.f == another.f
        x = (self.value ^ another.value) & ((1 << self.f) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x - 1
        return ans


class SimhashIndex(object):

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

        self.bucket = collections.defaultdict(set)

        for i, q in enumerate(objs):
            if i % 10000 == 0 or i == count - 1:
                logging.info('%s/%s', i + 1, count)

            self.add(*q)

    def get_near_dups(self, simhash):
        """
        `simhash` is an instance of Simhash
        return a list of obj_id, which is in type of str
        """
        assert simhash.f == self.f

        ans = set()

        for key in self.get_keys(simhash):
            dups = self.bucket[key]
            logging.debug('key:%s', key)
            if len(dups) > 200:
                logging.warning('Big bucket found. key:%s, len:%s', key, len(dups))

            for dup in dups:
                sim2, obj_id = dup.split(',', 1)
                sim2 = Simhash(long(sim2, 16), self.f)

                d = simhash.distance(sim2)
                if d <= self.k:
                    ans.add(obj_id)
        return list(ans)

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
            if v in self.bucket[key]:
                self.bucket[key].remove(v)

    @property
    def offsets(self):
        """
        You may optimize this method according to <http://www.wwwconference.org/www2007/papers/paper215.pdf>
        """
        return [self.f // (self.k + 1) * i for i in range(self.k + 1)]

    def get_keys(self, simhash):
        for i, offset in enumerate(self.offsets):
            if i == (len(self.offsets) - 1):
                m = 2 ** (self.f - offset) - 1
            else:
                m = 2 ** (self.offsets[i + 1] - offset) - 1
            c = simhash.value >> offset & m
            yield '%x:%x' % (c, i)

    def bucket_size(self):
        return len(self.bucket)
