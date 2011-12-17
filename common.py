import hashlib
def genid(dic):
	return hashlib.md5(str().join(map(str,dic.values()))).hexdigest()
