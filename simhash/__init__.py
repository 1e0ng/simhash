#Created by Liang Sun in 2013
import re
import collections
import hashlib

class Simhash(object):
    def __init__(self, value, f=64, reg=ur'[\w\u4e00-\u9fff]+'):
        self.f = f
        self.reg = reg
        self.value = None

        if isinstance(value, Simhash):
            self.value = value.value
        elif isinstance(value, basestring):
            self.build_by_text(unicode(value))
        elif isinstance(value, collections.Iterable):
            self.build_by_features(value)
        elif isinstance(value, long):
            self.value = value
        elif isinstance(value, Simhash):
            self.value = value.hash
        else:
            raise Exception('Bad parameter')

    def _slide(self, content, width=2):
        return [content[i:i+width] for i in xrange(max(len(content)-width+1, 1))]

    def _tokenize(self, content):
        ans = []
        content = ''.join(re.findall(self.reg, content))
        ans = self._slide(content)
        return ans

    def build_by_text(self, content):
        features = self._tokenize(content)
        return self.build_by_features(features)

    def build_by_features(self, features):
        features = set(features) # remove duplicated features
        hashs = [int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16) for w in features]
        v = [0]*self.f
        for h in hashs:
            for i in xrange(self.f):
                mask = 1 << i
                v[i] += 1 if h & mask else -1
        ans = 0
        for i in xrange(self.f):
            if v[i] >= 0:
                ans |= 1 << i
        self.value = ans

    def distance(self, another):
        x = (self.value ^ another.value) & ((1 << self.f) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x-1
        return ans
