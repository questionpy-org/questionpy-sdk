import json
from pathlib import Path
from typing import Optional


class FormStorage:

    def __init__(self) -> None:
        # Mapping of package path to form data path
        self.paths: dict[Path, Path] = {}
        self.storage_path: Path = Path(__file__).parent / 'form_storage'

    def insert(self, key: Path, form_data: dict) -> None:
        path = self.storage_path / key.with_suffix('.json')
        self.paths[key] = path
        json.dump(form_data, open(path, 'w'))

    def get(self, key: Path) -> Optional[dict]:
        path = self.paths.get(key)
        if not path or not path.exists():
            return None
        return json.loads(open(path).read())
