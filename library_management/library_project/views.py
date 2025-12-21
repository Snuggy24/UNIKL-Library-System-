"""
Custom error handlers - No stack traces exposed to users.
"""
from django.shortcuts import render


def bad_request(request, exception=None):
    """400 Bad Request handler."""
    return render(request, 'errors/400.html', status=400)


def permission_denied(request, exception=None):
    """403 Forbidden handler."""
    return render(request, 'errors/403.html', status=403)


def page_not_found(request, exception=None):
    """404 Not Found handler."""
    return render(request, 'errors/404.html', status=404)


def server_error(request):
    """500 Internal Server Error handler."""
    return render(request, 'errors/500.html', status=500)
