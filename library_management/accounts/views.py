"""
Views for user authentication, profile, and audit log.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import User, AuditLog
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm


class CustomLoginView(LoginView):
    """Custom login view with audit logging."""
    
    template_name = 'accounts/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        # Log successful login
        user = form.get_user()
        AuditLog.log(
            user=user,
            action=AuditLog.Action.LOGIN,
            details=f'User logged in successfully',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Log failed login attempt
        email = form.data.get('username', 'unknown')
        AuditLog.log(
            user=None,
            action=AuditLog.Action.FAILED_LOGIN,
            details=f'Failed login attempt for email: {email}',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        messages.error(self.request, 'Invalid email or password.')
        return super().form_invalid(form)
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class RegisterView(CreateView):
    """User registration view."""
    
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        # Log user registration
        AuditLog.log(
            user=self.object,
            action=AuditLog.Action.CREATE,
            model_name='User',
            object_id=self.object.id,
            object_repr=str(self.object),
            details='New user registered',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        messages.success(self.request, 'Registration successful! Please login.')
        return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class ProfileView(LoginRequiredMixin, DetailView):
    """User profile view."""
    
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile."""
    
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('accounts:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)


class AuditLogView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Admin-only audit log view."""
    
    model = AuditLog
    template_name = 'accounts/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50
    ordering = ['-timestamp']
    
    def test_func(self):
        return self.request.user.is_admin or self.request.user.is_superuser
    
    def handle_no_permission(self):
        messages.error(self.request, 'Access denied. Admin privileges required.')
        return redirect('books:book_list')


@login_required
def logout_view(request):
    """Logout view with audit logging."""
    AuditLog.log(
        user=request.user,
        action=AuditLog.Action.LOGOUT,
        details='User logged out',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('accounts:login')
