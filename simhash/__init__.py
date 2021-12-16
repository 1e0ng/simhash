# Created by 1e0n in 2013
from __future__ import division, unicode_literals

import collections
import hashlib
import logging
import numbers
import re
import sys
from itertools import groupby

import numpy as np

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

if sys.version_info[0] >= 3:
    basestring = str
    unicode = str
    long = int

    def int_to_bytes(n, length):
        return n.to_bytes(length, 'big')

    def bytes_to_int(b):
        return int.from_bytes(b, 'big')
else:
    range = xrange

    def int_to_bytes(n, length):
        return '{:0{}x}'.format(n, length * 2).decode('hex')

    def bytes_to_int(b):
        return int(b.encode('hex'), 16)

def _hashfunc(x):
    return hashlib.md5(x).digest()


class Simhash(object):
    # Constants used in calculating simhash. Larger values will use more RAM.
    large_weight_cutoff = 50
    batch_size = 200

    def __init__(
            self, value, f=64, reg=r'[\w\u4e00-\u9fcc]+', hashfunc=_hashfunc, log=None
    ):
        """
        `f` is the dimensions of fingerprints, in bits. Must be a multiple of 8.

        `reg` is meaningful only when `value` is basestring and describes
        what is considered to be a letter inside parsed string. Regexp
        object can also be specified (some attempt to handle any letters
        is to specify reg=re.compile(r'\w', re.UNICODE))

        `hashfunc` accepts a utf-8 encoded string and returns either bytes
        (preferred) or an unsigned integer, in at least `f // 8` bytes.
        """
        if f % 8:
            raise ValueError('f must be a multiple of 8')

        self.f = f
        self.f_bytes = f // 8
        self.reg = reg
        self.value = None
        self.hashfunc = hashfunc
        self.hashfunc_returns_int = isinstance(hashfunc(b"test"), numbers.Integral)

        if log is None:
            self.log = logging.getLogger("simhash")
        else:
            self.log = log

        if isinstance(value, Simhash):
            self.value = value.value
        elif isinstance(value, basestring):
            self.build_by_text(unicode(value))
        elif isinstance(value, Iterable):
            self.build_by_features(value)
        elif isinstance(value, numbers.Integral):
            self.value = value
        else:
            raise Exception('Bad parameter with type {}'.format(type(value)))

    def __eq__(self, other):
        """
        Compare two simhashes by their value.

        :param Simhash other: The Simhash object to compare to
        """
        return self.value == other.value

    def _slide(self, content, width=4):
        return [content[i:i + width] for i in range(max(len(content) - width + 1, 1))]

    def _tokenize(self, content):
        content = content.lower()
        content = ''.join(re.findall(self.reg, content))
        ans = self._slide(content)
        return ans

    def build_by_text(self, content):
        features = self._tokenize(content)
        features = {k:sum(1 for _ in g) for k, g in groupby(sorted(features))}
        return self.build_by_features(features)

    def build_by_features(self, features):
        """
        `features` might be a list of unweighted tokens (a weight of 1
                   will be assumed), a list of (token, weight) tuples or
                   a token -> weight dict.
        """
        sums = []
        batch = []
        count = 0
        w = 1
        truncate_mask = 2 ** self.f - 1
        if isinstance(features, dict):
            features = features.items()

        for f in features:
            skip_batch = False
            if not isinstance(f, basestring):
                f, w = f
                skip_batch = w > self.large_weight_cutoff or not isinstance(w, int)

            count += w
            if self.hashfunc_returns_int:
                h = int_to_bytes(self.hashfunc(f.encode('utf-8')) & truncate_mask, self.f_bytes)
            else:
                h = self.hashfunc(f.encode('utf-8'))[-self.f_bytes:]

            if skip_batch:
                sums.append(self._bitarray_from_bytes(h) * w)
            else:
                batch.append(h * w)
                if len(batch) >= self.batch_size:
                    sums.append(self._sum_hashes(batch))
                    batch = []

            if len(sums) >= self.batch_size:
                sums = [np.sum(sums, 0)]

        if batch:
            sums.append(self._sum_hashes(batch))

        combined_sums = np.sum(sums, 0)
        self.value = bytes_to_int(np.packbits(combined_sums > count / 2).tobytes())

    def _sum_hashes(self, digests):
        bitarray = self._bitarray_from_bytes(b''.join(digests))
        rows = np.reshape(bitarray, (-1, self.f))
        return np.sum(rows, 0)

    @staticmethod
    def _bitarray_from_bytes(b):
        return np.unpackbits(np.frombuffer(b, dtype='>B'))

    def distance(self, another):
        assert self.f == another.f
        x = (self.value ^ another.value) & ((1 << self.f) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x - 1
        return ans


class SimhashIndex(object):

    def __init__(self, objs, f=64, k=2, log=None):
        """
        `objs` is a list of (obj_id, simhash)
        obj_id is a string, simhash is an instance of Simhash
        `f` is the same with the one for Simhash
        `k` is the tolerance
        """
        self.k = k
        self.f = f
        count = len(objs)

        if log is None:
            self.log = logging.getLogger("simhash")
        else:
            self.log = log

        self.log.info('Initializing %s data.', count)

        self.bucket = collections.defaultdict(set)

        for i, q in enumerate(objs):
            if i % 10000 == 0 or i == count - 1:
                self.log.info('%s/%s', i + 1, count)

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
            self.log.debug('key:%s', key)
            if len(dups) > 200:
                self.log.warning('Big bucket found. key:%s, len:%s', key, len(dups))

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
        You may optimize this method according to <http://static.googleusercontent.com/media/research.google.com/en//pubs/archive/33026.pdf>
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
