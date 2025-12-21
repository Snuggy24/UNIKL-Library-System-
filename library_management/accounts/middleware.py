"""
Audit logging middleware for tracking user actions.
"""
from .models import AuditLog


class AuditLogMiddleware:
    """
    Middleware to log login/logout events and track request metadata.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store IP address in request for use by views
        request.client_ip = self.get_client_ip(request)
        request.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
