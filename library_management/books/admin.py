"""
Admin configuration for the Books app.
Provides comprehensive admin interface for library management.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Book, BorrowRecord, Fine, Reservation


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'book_count', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'author', 'isbn', 'category', 
        'availability_display', 'status', 'location'
    ]
    list_filter = ['status', 'category', 'language', 'publication_year']
    search_fields = ['title', 'author', 'isbn', 'publisher']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'author', 'isbn', 'publisher', 'publication_year')
        }),
        ('Classification', {
            'fields': ('category', 'language', 'description')
        }),
        ('Inventory', {
            'fields': ('total_copies', 'available_copies', 'status', 'location')
        }),
        ('Media', {
            'fields': ('cover_image',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('pages', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def availability_display(self, obj):
        color = 'green' if obj.available_copies > 0 else 'red'
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            color,
            obj.available_copies,
            obj.total_copies
        )
    availability_display.short_description = 'Available'


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'book', 'borrowed_date', 'due_date', 
        'status', 'overdue_display'
    ]
    list_filter = ['status', 'borrowed_date', 'due_date']
    search_fields = ['user__email', 'book__title', 'book__isbn']
    readonly_fields = ['borrowed_date']
    date_hierarchy = 'borrowed_date'
    list_per_page = 25
    
    fieldsets = (
        ('Loan Information', {
            'fields': ('user', 'book', 'status')
        }),
        ('Dates', {
            'fields': ('borrowed_date', 'due_date', 'returned_date')
        }),
        ('Staff', {
            'fields': ('issued_by', 'returned_to'),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def overdue_display(self, obj):
        if obj.status == BorrowRecord.Status.RETURNED:
            return format_html('<span style="color: gray;">Returned</span>')
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} days</span>',
                obj.days_overdue
            )
        return format_html('<span style="color: green;">On time</span>')
    overdue_display.short_description = 'Overdue'


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'status', 'created_at', 'paid_date']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'borrow_record__book__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Fine Details', {
            'fields': ('borrow_record', 'user', 'amount', 'status')
        }),
        ('Payment', {
            'fields': ('paid_date', 'paid_amount')
        }),
        ('Waiver', {
            'fields': ('waived_by', 'waiver_reason'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'book', 'status', 'queue_position', 
        'reserved_date', 'expiry_date'
    ]
    list_filter = ['status', 'reserved_date']
    search_fields = ['user__email', 'book__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Reservation Details', {
            'fields': ('user', 'book', 'status', 'queue_position')
        }),
        ('Dates', {
            'fields': ('reserved_date', 'notified_date', 'expiry_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
