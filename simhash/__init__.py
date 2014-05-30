#Created by Liang Sun in 2013
import re
import logging
import collections

class Simhash(object):
    def __init__(self, value, f=64, reg=ur'[\w\u4e00-\u9fff]+', hashfunc=None):
        '''
        `f` is the dimensions of fingerprints

        `reg` is meaningful only when `value` is basestring and describes
        what is considered to be a letter inside parsed string. Regexp
        object can also be specified (some attempt to handle any letters
        is to specify reg=re.compile(r'\w', re.UNICODE))

        `hashfunc` accepts a utf-8 encoded string and returns a unsigned
        integer in at least `f` bits.
        '''

        self.f = f
        self.reg = reg
        self.value = None

        if hashfunc is None:
            import hashlib
            self.hashfunc = lambda x: int(hashlib.md5(x).hexdigest(), 16)
        else:
            self.hashfunc = hashfunc

        if isinstance(value, Simhash):
            self.value = value.value
        elif isinstance(value, basestring):
            self.build_by_text(unicode(value))
        elif isinstance(value, collections.Iterable):
            self.build_by_features(value)
        elif isinstance(value, long):
            self.value = value
        else:
            raise Exception('Bad parameter')

    def _slide(self, content, width=4):
        return [content[i:i+width] for i in xrange(max(len(content)-width+1, 1))]

    def _tokenize(self, content):
        ans = []
        content = content.lower()
        content = ''.join(re.findall(self.reg, content))
        ans = self._slide(content)
        return ans

    def build_by_text(self, content):
        features = self._tokenize(content)
        self._features = features
        return self.build_by_features(features)

    def build_by_features(self, features):
        hashs = [self.hashfunc(w.encode('utf-8')) for w in features]
        v = [0]*self.f
        masks = [1 << i for i in xrange(self.f)]
        for h in hashs:
            for i in xrange(self.f):
                v[i] += 1 if h & masks[i] else -1
        ans = 0
        for i in xrange(self.f):
            if v[i] >= 0:
                ans |= masks[i]
        self.value = ans

    def distance(self, another):
        assert self.f == another.f
        x = (self.value ^ another.value) & ((1 << self.f) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x-1
        return ans

class SimhashIndex(object):
    def get_near_dups(self, simhash):
        '''
        `simhash` is an instance of Simhash
        return a list of obj_id, which is in type of str
        '''
        assert simhash.f == self.f

        ans = set()

        for key in self.get_keys(simhash):
            dups = self.bucket.get(key, set())
            logging.debug('key:%s', key)
            if len(dups) > 100:
                logging.warning('Big bucket found. key:%s, len:%s', key, len(dups))

            for dup in dups:
                sim2, obj_id = dup.split(',', 1)
                sim2 = Simhash(long(sim2, 16), self.f)

                d = simhash.distance(sim2)
                if d <= self.k:
                    ans.add(obj_id)
        return list(ans)

    def add(self, obj_id, simhash):
        '''
        `obj_id` is a string
        `simhash` is an instance of Simhash
        '''
        assert simhash.f == self.f

        for key in self.get_keys(simhash):
            v = '%x,%s' % (simhash.value, obj_id)

            self.bucket.setdefault(key, set())
            self.bucket[key].add(v)

    def delete(self, obj_id, simhash):
        '''
        `obj_id` is a string
        `simhash` is an instance of Simhash
        '''
        assert simhash.f == self.f

        for key in self.get_keys(simhash):
            v = '%x,%s' % (simhash.value, obj_id)

            if v in self.bucket.get(key, set()):
                self.bucket[key].remove(v)

    def __init__(self, objs, f=64, k=2):
        '''
        `objs` is a list of (obj_id, simhash)
        obj_id is a string, simhash is an instance of Simhash
        `f` is the same with the one for Simhash
        `k` is the toleranec
        '''
        self.k = k
        self.f = f
        count = len(objs)
        logging.info('Initializing %s data.', count)

        self.bucket = {}

        for i, q in enumerate(objs):
            if i % 10000 == 0 or i == count-1:
                logging.info('%s/%s', i+1, count)

            self.add(*q)

    @property
    def offsets(self):
        '''
        You may optimize this method according to <http://www.wwwconference.org/www2007/papers/paper215.pdf>
        '''
        return [self.f / (self.k + 1) * i for i in xrange(self.k + 1)]

    def get_keys(self, simhash):
        for i, offset in enumerate(self.offsets):
            m = (i == len(self.offsets) - 1 and 2**(self.f - offset) - 1 or 2**(self.offsets[i + 1] - offset) - 1)
            c = simhash.value >> offset & m
            yield '%x:%x' % (c, i)

    def bucket_size(self):
        return len(self.bucket)
