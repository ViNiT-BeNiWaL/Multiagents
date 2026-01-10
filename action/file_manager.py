from pathlib import Path

class FileManager:
    def __init__(self, base_dir: str):
        self.base = Path(base_dir)
        self.base.mkdir(exist_ok=True)

    def write_file(self, name: str, content: str):
        path = self.base / name
        path.write_text(content)
        return {"filename": name, "size": len(content)}
