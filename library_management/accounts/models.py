"""
Custom User model with role-based access control.
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with roles for RBAC."""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Administrator'
        LIBRARIAN = 'LIBRARIAN', 'Librarian'
        STUDENT = 'STUDENT', 'Student'
    
    # Remove username field, use email instead
    username = None
    email = models.EmailField('Email Address', unique=True)
    
    # Role field for RBAC
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    # Email verification fields
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )
    
    # Additional profile fields
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    student_id = models.CharField(max_length=20, blank=True, help_text='Student ID (for students only)')
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        help_text='Upload a profile picture (max 2MB)',
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_librarian(self):
        return self.role == self.Role.LIBRARIAN
    
    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    @property
    def can_manage_books(self):
        """Check if user can create/edit/delete books."""
        return self.role in [self.Role.ADMIN, self.Role.LIBRARIAN]
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.role == self.Role.ADMIN


class AuditLog(models.Model):
    """Audit log for tracking sensitive actions."""
    
    class Action(models.TextChoices):
        CREATE = 'CREATE', 'Create'
        UPDATE = 'UPDATE', 'Update'
        DELETE = 'DELETE', 'Delete'
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        BORROW = 'BORROW', 'Borrow Book'
        RETURN = 'RETURN', 'Return Book'
        FAILED_LOGIN = 'FAILED_LOGIN', 'Failed Login'
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} - {self.action} - {self.timestamp}"
    
    @classmethod
    def log(cls, user, action, model_name='', object_id=None, object_repr='', 
            details='', ip_address=None, user_agent=''):
        """Create an audit log entry."""
        return cls.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
