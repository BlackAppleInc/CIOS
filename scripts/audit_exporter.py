import os
from pathlib import Path
from datetime import datetime

class AuditExporter:
    """
    Traverses the core directories and produces a consolidated markdown file 
    containing the source code for an algorithm audit.
    """
    def __init__(self, root_dir: str = None):
        if root_dir is None:
            self.root_dir = Path(__file__).resolve().parent.parent
        else:
            self.root_dir = Path(root_dir).resolve()
            
        self.export_dir = self.root_dir / "data" / "exports" / "audit"
        
        self.included_dirs = {"core", "infrastructure", "domain"}
        # schema.sql is under infrastructure/database/schema.sql, so it will be caught by "infrastructure"
        self.included_root_files = {"dashboard.py", "main.py"} 
        
        self.excluded_dirs = {"venv", "__pycache__", ".git", "data", "scripts"}

    def _should_include(self, path: Path) -> bool:
        # Check directory exclusions
        for part in path.parts:
            if part in self.excluded_dirs or part.startswith("."):
                return False
        
        # Check extensions
        if path.suffix not in ('.py', '.sql', '.md'):
            return False

        # If it's a root file, check if it's explicitly included
        if path.parent == self.root_dir:
            return path.name in self.included_root_files

        # If it's in a subdirectory, check if the top-level directory is included
        try:
            rel_parts = path.relative_to(self.root_dir).parts
            if rel_parts[0] in self.included_dirs:
                return True
        except ValueError:
            pass

        return False

    def generate_snapshot(self) -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d_%H%M")
        snapshot_filename = f"codebase_snapshot_{date_str}.md"
        snapshot_path = self.export_dir / snapshot_filename
        
        content = ["# CIOS Codebase Snapshot\n"]
        content.append(f"Generated at: {datetime.utcnow().isoformat()}\n\n")
        
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                file_path = Path(root) / file
                if self._should_include(file_path):
                    rel_path = file_path.relative_to(self.root_dir)
                    content.append(f"## {rel_path}\n")
                    
                    lang = "python"
                    if file_path.suffix == ".sql":
                        lang = "sql"
                    elif file_path.suffix == ".md":
                        lang = "markdown"
                        
                    content.append(f"```{lang}")
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        content.append(file_content)
                    except Exception as e:
                        content.append(f"# Error reading file: {e}")
                    content.append("```\n")

        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        with open(snapshot_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
            
        return str(snapshot_path.resolve())

if __name__ == "__main__":
    exporter = AuditExporter()
    out = exporter.generate_snapshot()
    print(f"Snapshot generated at: {out}")
