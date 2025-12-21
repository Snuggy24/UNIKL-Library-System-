"""
URL configuration for books app.
"""
from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('', views.BookListView.as_view(), name='book_list'),
    path('book/<int:pk>/', views.BookDetailView.as_view(), name='book_detail'),
    path('book/<int:pk>/borrow/', views.borrow_book, name='borrow_book'),
    path('borrow/<int:pk>/return/', views.return_book, name='return_book'),
    path('book/<int:pk>/reserve/', views.reserve_book, name='reserve_book'),
    path('reservation/<int:pk>/cancel/', views.cancel_reservation, name='cancel_reservation'),
    path('my-books/', views.MyBooksView.as_view(), name='my_books'),
]
