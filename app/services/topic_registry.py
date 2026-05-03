import json
from pathlib import Path

from app.core.constants import STANDARD_TOPICS


class TopicRegistry:
    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.topics_dir = self.base_dir / "topics"
        self.profiles_dir = self.base_dir / "profiles"
        self.topics_index_path = self.topics_dir / "index.json"
        self.profiles_index_path = self.profiles_dir / "index.json"
        self._ensure_indexes()

    def list_topics(self) -> list[str]:
        return self._read_index(self.topics_index_path)

    def add_topic(self, name: str) -> bool:
        return self._add_name(self.topics_index_path, self.topics_dir, name)

    def list_profiles(self) -> list[str]:
        return self._read_index(self.profiles_index_path)

    def add_profile(self, name: str) -> bool:
        return self._add_name(self.profiles_index_path, self.profiles_dir, name)

    def _ensure_indexes(self) -> None:
        self.topics_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        if not self.topics_index_path.exists():
            self._write_index(self.topics_index_path, list(STANDARD_TOPICS))
            for topic in STANDARD_TOPICS:
                (self.topics_dir / _safe_dir_name(topic)).mkdir(parents=True, exist_ok=True)
        if not self.profiles_index_path.exists():
            self._write_index(self.profiles_index_path, [])

    def _add_name(self, index_path: Path, parent_dir: Path, name: str) -> bool:
        normalized = name.strip()
        if not normalized:
            return False

        items = self._read_index(index_path)
        if normalized in items:
            return False

        items.append(normalized)
        self._write_index(index_path, items)
        (parent_dir / _safe_dir_name(normalized)).mkdir(parents=True, exist_ok=True)
        return True

    @staticmethod
    def _read_index(path: Path) -> list[str]:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        return [str(item) for item in data]

    @staticmethod
    def _write_index(path: Path, items: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def _safe_dir_name(name: str) -> str:
    return "".join("_" if char in '<>:"/\\|?*' else char for char in name.strip())
