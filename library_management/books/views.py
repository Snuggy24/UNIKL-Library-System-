"""
Views for book management, borrowing, and reservations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .models import Book, Category, BorrowRecord, Reservation
from accounts.models import AuditLog


class BookListView(ListView):
    """Browse all available books."""
    
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Book.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(author__icontains=search) |
                Q(isbn__icontains=search)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Availability filter
        available = self.request.GET.get('available')
        if available == 'true':
            queryset = queryset.filter(available_copies__gt=0)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['search'] = self.request.GET.get('search', '')
        context['current_category'] = self.request.GET.get('category', '')
        return context


class BookDetailView(DetailView):
    """View single book details."""
    
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Check if user has already borrowed this book
            context['has_borrowed'] = BorrowRecord.objects.filter(
                user=self.request.user,
                book=self.object,
                status=BorrowRecord.Status.ACTIVE
            ).exists()
            # Check if user has reserved this book
            context['has_reserved'] = Reservation.objects.filter(
                user=self.request.user,
                book=self.object,
                status__in=[Reservation.Status.PENDING, Reservation.Status.READY]
            ).exists()
        return context


@login_required
def borrow_book(request, pk):
    """Borrow a book."""
    book = get_object_or_404(Book, pk=pk)
    
    # Check if user has too many books
    active_borrows = BorrowRecord.objects.filter(
        user=request.user,
        status=BorrowRecord.Status.ACTIVE
    ).count()
    
    max_books = getattr(settings, 'MAX_BOOKS_PER_USER', 5)
    if active_borrows >= max_books:
        messages.error(request, f'You cannot borrow more than {max_books} books at a time.')
        return redirect('books:book_detail', pk=pk)
    
    # Check if book is available
    if not book.is_available:
        messages.error(request, 'This book is not available for borrowing.')
        return redirect('books:book_detail', pk=pk)
    
    # Check if user already borrowed this book
    if BorrowRecord.objects.filter(
        user=request.user,
        book=book,
        status=BorrowRecord.Status.ACTIVE
    ).exists():
        messages.warning(request, 'You have already borrowed this book.')
        return redirect('books:book_detail', pk=pk)
    
    # Create borrow record
    borrow_record = BorrowRecord.objects.create(
        user=request.user,
        book=book
    )
    
    # Decrease available copies
    book.borrow()
    
    # Log the action
    AuditLog.log(
        user=request.user,
        action=AuditLog.Action.BORROW,
        model_name='Book',
        object_id=book.id,
        object_repr=str(book),
        details=f'Borrowed book: {book.title}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    messages.success(request, f'Successfully borrowed "{book.title}". Due date: {borrow_record.due_date.strftime("%B %d, %Y")}')
    return redirect('books:my_books')


@login_required
def return_book(request, pk):
    """Return a borrowed book."""
    borrow_record = get_object_or_404(
        BorrowRecord,
        pk=pk,
        user=request.user,
        status=BorrowRecord.Status.ACTIVE
    )
    
    # Mark as returned
    borrow_record.mark_returned()
    
    # Log the action
    AuditLog.log(
        user=request.user,
        action=AuditLog.Action.RETURN,
        model_name='Book',
        object_id=borrow_record.book.id,
        object_repr=str(borrow_record.book),
        details=f'Returned book: {borrow_record.book.title}',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    messages.success(request, f'Successfully returned "{borrow_record.book.title}".')
    return redirect('books:my_books')


class MyBooksView(LoginRequiredMixin, ListView):
    """View user's borrowed books."""
    
    template_name = 'books/my_books.html'
    context_object_name = 'borrow_records'
    
    def get_queryset(self):
        return BorrowRecord.objects.filter(
            user=self.request.user
        ).select_related('book').order_by('-borrowed_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        records = self.get_queryset()
        context['active_records'] = records.filter(status=BorrowRecord.Status.ACTIVE)
        context['returned_records'] = records.filter(status=BorrowRecord.Status.RETURNED)[:10]
        context['reservations'] = Reservation.objects.filter(
            user=self.request.user,
            status__in=[Reservation.Status.PENDING, Reservation.Status.READY]
        ).select_related('book')
        return context


@login_required
def reserve_book(request, pk):
    """Reserve an unavailable book."""
    book = get_object_or_404(Book, pk=pk)
    
    # Check if already reserved
    if Reservation.objects.filter(
        user=request.user,
        book=book,
        status__in=[Reservation.Status.PENDING, Reservation.Status.READY]
    ).exists():
        messages.warning(request, 'You have already reserved this book.')
        return redirect('books:book_detail', pk=pk)
    
    # Calculate queue position
    queue_position = Reservation.objects.filter(
        book=book,
        status=Reservation.Status.PENDING
    ).count() + 1
    
    # Create reservation
    Reservation.objects.create(
        user=request.user,
        book=book,
        queue_position=queue_position
    )
    
    messages.success(request, f'Successfully reserved "{book.title}". Queue position: {queue_position}')
    return redirect('books:my_books')


@login_required
def cancel_reservation(request, pk):
    """Cancel a reservation."""
    reservation = get_object_or_404(
        Reservation,
        pk=pk,
        user=request.user,
        status__in=[Reservation.Status.PENDING, Reservation.Status.READY]
    )
    
    reservation.cancel()
    messages.success(request, f'Reservation for "{reservation.book.title}" cancelled.')
    return redirect('books:my_books')
