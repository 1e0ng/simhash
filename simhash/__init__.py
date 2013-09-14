#Created by Liang Sun in 2013
import re
import hashlib

def _slide(content, width=2):
    return [content[i:i+width] for i in xrange(len(content)-width+1)]

def _tokenize(content):
    ans = []
    words = re.findall(r'[a-zA-Z]+', content)
    for word in words:
        ans += _slide(word)
    return ans

def simhash(content):
    f = 64
    features = _tokenize(content)
    hashs = [int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16) for w in features]
    v = [0]*f
    for h in hashs:
        for i in xrange(f):
            mask = 1 << i
            v[i] += 1 if h & mask else -1
    ans = 0
    for i in xrange(f):
        if v[i] >= 0:
            ans |= 1 << i
    return ans
