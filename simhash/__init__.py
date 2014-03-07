#Created by Liang Sun in 2013
import re
import logging
import collections

class Simhash(object):
    def __init__(self, value, f=64, reg=ur'[\w\u4e00-\u9fff]+', hashfunc=None):
        '''
        `f` is the dimensions of fingerprints

        `reg` is meaningful only when `value` is basestring

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

    def _slide(self, content, width=2):
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
        x = (self.value ^ another.value) & ((1 << self.f) - 1)
        ans = 0
        while x:
            ans += 1
            x &= x-1
        return ans

class SimhashIndex(object):
    '''
    simhash is an instance of Simhash
    
    return a list of obj_id, which is in type of str
    '''
    def get_near_dups(self, simhash, tolerance=2):
        ans = set()

        for offset in [0, 21, 42]:
            n = simhash.value >> offset & (42==offset and 0x3fffff or 0x1fffff)
            key = '%x:%x' % (n, offset/21)
            ret = self.bucket.get(key, set())
            logging.debug('key:%s', key)
            if len(ret) > 100:
                logging.warning('Big bucket found. key:%s, len(ret):%s', key, len(ret))

            for r in ret:
                sim2, obj_id = r.split(',', 1)
                sim2 = Simhash(long(sim2, 16))

                d = simhash.distance(sim2)
                if d <= tolerance:
                    ans.add(obj_id)
        return list(ans)

    '''
    obj_id is a string
    simhash is an instance of Simhash
    '''
    def add(self, obj_id, simhash):
        for offset in [0, 21, 42]:
            c = simhash.value >> offset & (42==offset and 0x3fffff or 0x1fffff)

            k = '%x:%x' % (c, offset/21)
            v = '%x,%s' % (simhash.value, obj_id)

            self.bucket.setdefault(k, set())
            self.bucket[k].add(v)

    '''
    objs is a list of (obj_id, simhash)
    obj_id is a string, simhash is an instance of Simhash
    '''
    def __init__(self, objs):
        count = len(objs)
        logging.info('Initializing %s data.', count)

        self.bucket = {}

        for i, q in enumerate(objs):
            if i % 10000 == 0 or i == count-1:
                logging.info('%s/%s', i+1, count)

            self.add(*q)

    def bucket_size(self):
        return len(self.bucket)
