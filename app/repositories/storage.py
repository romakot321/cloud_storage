from pathlib import Path
from string import ascii_lowercase
import random
import os.path
from uuid import UUID
from io import TextIOWrapper


class StorageRepository:
    files_path = Path('files/')
    filename_length = 32

    def _generate_filename(self) -> str:
        return ''.join(random.choices(ascii_lowercase + '0123456789', k=self.filename_length))

    def is_stored(self, filename: str) -> bool:
        return os.path.exists(self.files_path / filename)

    def _store(self, raw: TextIOWrapper, filename: str) -> str:
        """Return filename"""
        with open(self.files_path / filename, 'wb') as f:
            while True:
                data = raw.read(1024)
                if not data:
                    break
                f.write(data)
        return filename

    def _stream(self, filename: str) -> bytes | None:
        if not self.is_stored(filename):
            return
        with open(self.files_path / filename, 'rb') as f:
            while True:
                data = f.read(4098)
                if not data:
                    break
                yield data

    def create(self, raw: TextIOWrapper, filename: str) -> str:
        """Return filename"""
        return self._store(raw, filename)

    def get(self, filename: str):
        """Chunked read"""
        return self._stream(filename)

    def delete(self, filename: str):
        (self.files_path / filename).unlink()

