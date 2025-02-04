from hashlib import sha256


def deterministic_hash(string: str):
    m = sha256()
    m.update(string.encode(encoding="utf-16"))
    return m.hexdigest()
