from __future__ import annotations

import io

from werkzeug.datastructures import FileStorage


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def is_png(upload: FileStorage) -> bool:
    name = (upload.filename or "").lower()
    if not name.endswith(".png"):
        return False

    pos = upload.stream.tell()
    header = upload.stream.read(8)
    upload.stream.seek(pos, io.SEEK_SET)
    return header == PNG_SIGNATURE
