import os
import shutil
import uuid
from pathlib import Path

class LocalStorageEngine:
    """
    Local-first storage engine designed to copy and index supporting 
    documents (CVs, cover letters, JDs) into a secure, predictable directory.
    """
    def __init__(self, storage_dir: str = "data/attachments"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def attach_file(self, source_path: str) -> str:
        """
        Copies the target physical file to the internal attachments directory.
        Renames the file using a UUID to prevent collisions.
        Returns the new local relative path.
        """
        source = Path(source_path)
        if not source.exists() or not source.is_file():
            raise FileNotFoundError(f"Cannot attach file. Path does not exist or is not a file: {source_path}")
            
        extension = source.suffix
        new_filename = f"{uuid.uuid4()}{extension}"
        destination = self.storage_dir / new_filename
        
        shutil.copy2(source, destination)
        return str(destination)

    def create_backup(self, db_path: str, backup_dir: str = "data/exports/backups") -> str:
        """
        Creates a timestamped backup archive of both the SQLite database 
        and the local attachments directory, saved to data/exports/backups/.
        """
        from datetime import datetime
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        archive_name = f"cios_backup_{timestamp}"
        target_zip = backup_path / archive_name
        
        temp_dir = Path("data/temp_backup")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copy database file
            db_file = Path(db_path)
            if db_file.exists():
                shutil.copy2(db_file, temp_dir / db_file.name)
            
            # Copy attachments
            attachments_dest = temp_dir / "attachments"
            if self.storage_dir.exists():
                shutil.copytree(self.storage_dir, attachments_dest)
            else:
                attachments_dest.mkdir(exist_ok=True)
                
            # Zip everything in the temp directory
            zip_filepath = shutil.make_archive(
                base_name=str(target_zip),
                format="zip",
                root_dir=str(temp_dir)
            )
            return zip_filepath
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
