from django.core.files.base import ContentFile
from django.utils.text import slugify
from .models import PythonFile
import os
import hashlib
from datetime import datetime


class PythonFileService:
    """Python file management business logic"""

    def create_python_file(self, file, user, name=None, description=None):
        """Create Python file"""
        # Generate file name
        if not name:
            name = file.name

        # Convert filenames to a safe format
        safe_name = self.generate_safe_filename(name)

        # Save file
        python_file = PythonFile(
            name=safe_name,
            original_name=file.name,
            description=description,
            file_size=file.size,
            uploaded_by=user,
        )

        # save file
        python_file.file.save(safe_name, file, save=True)

        return python_file

    def generate_safe_filename(self, filename):
        """Generate safe filenames"""
        name, ext = os.path.splitext(filename)
        # File name slug
        safe_name = slugify(name)
        # Add a timestamp to ensure uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{safe_name}_{timestamp}{ext}"

    def get_file_content(self, python_file):
        """Get file contents"""
        if python_file.file:
            with python_file.file.open("r") as f:
                return f.read()
        return None

    def update_file_content(self, python_file, new_content):
        """Update file contents"""
        if python_file.file:
            # Delete existing file
            python_file.file.delete(save=False)

            # create new file
            content_file = ContentFile(new_content.encode("utf-8"))
            python_file.file.save(
                self.generate_safe_filename(python_file.name), content_file, save=True
            )
        return python_file

    def validate_python_syntax(self, content):
        """Validating Python syntax"""
        try:
            compile(content, "<string>", "exec")
            return True, None
        except SyntaxError as e:
            return False, str(e)

    def get_file_hash(self, file):
        """Calculate the hash value of the file"""
        hasher = hashlib.sha256()
        for chunk in file.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()
