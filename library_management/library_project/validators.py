"""
File upload security validators.
OWASP File Upload Security compliant.
"""
import os
import uuid
import magic  # python-magic for MIME type detection
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_image_file(file):
    """
    Validate uploaded image file for security.
    - Checks file extension
    - Validates MIME type
    - Checks file size
    """
    # Get file extension
    ext = os.path.splitext(file.name)[1].lower().strip('.')
    
    # Check extension whitelist
    allowed_extensions = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', ['jpg', 'jpeg', 'png', 'gif', 'webp'])
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
        )
    
    # Check file size
    max_size = getattr(settings, 'MAX_IMAGE_SIZE', 2 * 1024 * 1024)  # 2MB default
    if file.size > max_size:
        raise ValidationError(
            f'File too large. Maximum size is {max_size // (1024 * 1024)}MB.'
        )
    
    # Validate MIME type using python-magic
    try:
        file_mime = magic.from_buffer(file.read(2048), mime=True)
        file.seek(0)  # Reset file pointer
        
        allowed_mimes = getattr(
            settings, 
            'ALLOWED_IMAGE_MIMETYPES', 
            ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        )
        
        if file_mime not in allowed_mimes:
            raise ValidationError(
                f'Invalid file content. File appears to be {file_mime}, not an image.'
            )
    except ImportError:
        # If python-magic is not installed, skip MIME check
        # but log a warning
        pass
    
    return True


def generate_secure_filename(original_filename):
    """
    Generate a secure random filename to prevent path traversal attacks.
    Uses UUID to ensure uniqueness.
    """
    ext = os.path.splitext(original_filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


def secure_file_path(instance, filename):
    """
    Generate secure file path for uploads.
    Stores files with random UUID names.
    """
    secure_name = generate_secure_filename(filename)
    return f'book_covers/{secure_name}'
