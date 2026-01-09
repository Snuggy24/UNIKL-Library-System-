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
from django.urls import reverse_lazy, reverse
from django.core.mail import send_mail
from .models import User, AuditLog
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm


class CustomLoginView(LoginView):
    """Custom login view with audit logging."""
    
    template_name = 'accounts/login.html'
    authentication_form = UserLoginForm
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        user = form.get_user()
        # Block login if email not verified
        if not user.is_email_verified:
            messages.error(self.request, 
                'Please verify your email before logging in. Check your inbox or request a new verification link.')
            return redirect('accounts:login')
        # Log successful login
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
        # Generate verification token and send email
        token = self.object.generate_verification_token()
        self.send_verification_email(self.object, token)
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
        messages.success(self.request, 'Registration successful! Please check your email to verify your account.')
        return response
    
    def send_verification_email(self, user, token):
        """Send verification email to newly registered user."""
        verification_url = self.request.build_absolute_uri(
            reverse('accounts:verify_email', kwargs={'token': token})
        )
        send_mail(
            subject='Verify your email - UNIKL Library System',
            message=f'Hi {user.first_name},\n\nPlease click the link below to verify your email:\n\n{verification_url}\n\nThis link expires in 24 hours.\n\nIf you did not create an account, please ignore this email.',
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
            recipient_list=[user.email],
        )
    
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


def verify_email(request, token):
    """Handle email verification link."""
    try:
        user = User.objects.get(email_verification_token=token)
        if user.is_email_verified:
            messages.info(request, 'Your email is already verified. You can log in.')
        elif user.is_token_valid():
            user.is_email_verified = True
            user.email_verification_token = None  # Clear token after use
            user.save()
            messages.success(request, 'Email verified successfully! You can now log in.')
        else:
            messages.error(request, 'This verification link has expired. Please request a new one.')
            return redirect('accounts:resend_verification')
    except User.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
    return redirect('accounts:login')


def resend_verification(request):
    """Resend verification email."""
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                messages.info(request, 'This email is already verified. You can log in.')
            else:
                token = user.generate_verification_token()
                verification_url = request.build_absolute_uri(
                    reverse('accounts:verify_email', kwargs={'token': token})
                )
                send_mail(
                    subject='Verify your email - UNIKL Library System',
                    message=f'Hi {user.first_name},\n\nPlease click the link below to verify your email:\n\n{verification_url}\n\nThis link expires in 24 hours.\n\nIf you did not request this, please ignore this email.',
                    from_email=None,
                    recipient_list=[user.email],
                )
                messages.success(request, 'Verification email sent! Please check your inbox.')
        except User.DoesNotExist:
            # Don't reveal if email exists (security best practice)
            messages.success(request, 'If this email is registered, a verification link will be sent.')
        return redirect('accounts:resend_verification')
    return render(request, 'accounts/resend_verification.html')
