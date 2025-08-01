import hashlib
import logging
import pathlib

import typing


def md5(fname:pathlib.Path) -> str:
    hash_md5 = hashlib.md5()
    with fname.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()