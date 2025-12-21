"""
Library Management Models: Book, Category, BorrowRecord, Fine, Reservation
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import timedelta


class Category(models.Model):
    """Book categories/genres for organization."""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def book_count(self):
        return self.books.count()


class Book(models.Model):
    """Book model for the library catalog."""
    
    class Status(models.TextChoices):
        AVAILABLE = 'AVAILABLE', 'Available'
        BORROWED = 'BORROWED', 'Borrowed'
        RESERVED = 'RESERVED', 'Reserved'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    
    # Basic Information
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    isbn = models.CharField(
        'ISBN',
        max_length=13,
        unique=True,
        help_text='13-digit ISBN number'
    )
    publisher = models.CharField(max_length=255, blank=True)
    publication_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(2100)
        ]
    )
    
    # Classification
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books'
    )
    
    # Physical Details
    pages = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=50, default='English')
    
    # Inventory
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )
    
    # Additional Info
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to='book_covers/',
        null=True,
        blank=True
    )
    location = models.CharField(
        max_length=50,
        blank=True,
        help_text='Shelf/Section location in library'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['title']
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['title']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
    @property
    def is_available(self):
        return self.available_copies > 0
    
    def borrow(self):
        """Decrease available copies when borrowed."""
        if self.available_copies > 0:
            self.available_copies -= 1
            if self.available_copies == 0:
                self.status = self.Status.BORROWED
            self.save()
            return True
        return False
    
    def return_book(self):
        """Increase available copies when returned."""
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            if self.available_copies > 0:
                self.status = self.Status.AVAILABLE
            self.save()
            return True
        return False


class BorrowRecord(models.Model):
    """Tracks book borrowing transactions."""
    
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Currently Borrowed'
        RETURNED = 'RETURNED', 'Returned'
        OVERDUE = 'OVERDUE', 'Overdue'
        LOST = 'LOST', 'Reported Lost'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrow_records'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='borrow_records'
    )
    
    # Dates
    borrowed_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField()
    returned_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Processed by (librarian who processed the transaction)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_records'
    )
    returned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_records'
    )
    
    class Meta:
        verbose_name = 'Borrow Record'
        verbose_name_plural = 'Borrow Records'
        ordering = ['-borrowed_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.book.title}"
    
    def save(self, *args, **kwargs):
        # Set default due date if not provided
        if not self.due_date:
            borrow_days = getattr(settings, 'BORROW_PERIOD_DAYS', 14)
            self.due_date = timezone.now() + timedelta(days=borrow_days)
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        if self.status == self.Status.RETURNED:
            return False
        return timezone.now() > self.due_date
    
    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        delta = timezone.now() - self.due_date
        return delta.days
    
    @property
    def calculated_fine(self):
        """Calculate fine based on overdue days."""
        if not self.is_overdue:
            return 0
        fine_per_day = getattr(settings, 'FINE_PER_DAY', 0.50)
        return self.days_overdue * fine_per_day
    
    def mark_returned(self, librarian=None):
        """Mark the book as returned."""
        self.returned_date = timezone.now()
        self.status = self.Status.RETURNED
        self.returned_to = librarian
        self.save()
        self.book.return_book()


class Fine(models.Model):
    """Fines for late book returns."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        WAIVED = 'WAIVED', 'Waived'
    
    borrow_record = models.OneToOneField(
        BorrowRecord,
        on_delete=models.CASCADE,
        related_name='fine'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fines'
    )
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Payment details
    paid_date = models.DateTimeField(null=True, blank=True)
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Waiver details
    waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='waived_fines'
    )
    waiver_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fine'
        verbose_name_plural = 'Fines'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - ${self.amount} ({self.status})"
    
    def mark_paid(self, amount=None):
        """Mark fine as paid."""
        self.paid_date = timezone.now()
        self.paid_amount = amount or self.amount
        self.status = self.Status.PAID
        self.save()
    
    def waive(self, waived_by, reason=''):
        """Waive the fine."""
        self.waived_by = waived_by
        self.waiver_reason = reason
        self.status = self.Status.WAIVED
        self.save()


class Reservation(models.Model):
    """Book reservations/holds."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        READY = 'READY', 'Ready for Pickup'
        FULFILLED = 'FULFILLED', 'Fulfilled'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reservations'
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Dates
    reserved_date = models.DateTimeField(default=timezone.now)
    notified_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    # Queue position (for books with multiple reservations)
    queue_position = models.PositiveIntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'
        ordering = ['queue_position', 'reserved_date']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=models.Q(status__in=['PENDING', 'READY']),
                name='unique_active_reservation'
            )
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.book.title} (#{self.queue_position})"
    
    def notify_ready(self):
        """Mark reservation as ready for pickup."""
        self.status = self.Status.READY
        self.notified_date = timezone.now()
        # Set expiry to 3 days from now
        self.expiry_date = timezone.now() + timedelta(days=3)
        self.save()
    
    def cancel(self):
        """Cancel the reservation."""
        self.status = self.Status.CANCELLED
        self.save()
    
    def fulfill(self):
        """Mark reservation as fulfilled (book borrowed)."""
        self.status = self.Status.FULFILLED
        self.save()
