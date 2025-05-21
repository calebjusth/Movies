from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponseBadRequest
import secrets
from .models import CustomUser, PasswordResetToken
from .forms import (
    CustomUserCreationForm, 
    OTPVerificationForm,
    CustomPasswordResetForm,
    CustomSetPasswordForm
)

from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.contrib import messages

class CustomLoginView(LoginView):
    template_name = './accounts/login.html'
    
    def form_valid(self, form):
        # Check if user is verified before allowing login
        user = form.get_user()
        if not user.is_verified:
            messages.error(self.request, 'Your account is not verified. Please check your email for the OTP.')
            return self.form_invalid(form)
        return super().form_valid(form)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # User is inactive until OTP verification
            user.save()
            
            # Generate and send OTP
            otp = user.generate_otp()
            send_otp_email(user.email, otp)
            
            # Store user ID in session for OTP verification
            request.session['otp_user_id'] = user.id
            return redirect('verify_otp')
    else:
        form = CustomUserCreationForm()
    return render(request, './accounts/register.html', {'form': form})

def verify_otp(request):
    # Check if user is in the OTP verification flow
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return redirect('register')
    
    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            if user.is_otp_valid(otp):
                # OTP is valid, activate user
                user.is_verified = True
                user.is_active = True
                user.save()
                del request.session['otp_user_id']
                login(request, user)
                messages.success(request, 'Your account has been successfully verified!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid or expired OTP. Please try again.')
    else:
        form = OTPVerificationForm()
    
    return render(request, './accounts/verify_otp.html', {'form': form})

def resend_otp(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')
    
    try:
        user = CustomUser.objects.get(id=user_id)
        otp = user.generate_otp()
        send_otp_email(user.email, otp)
        messages.success(request, 'A new OTP has been sent to your email.')
    except CustomUser.DoesNotExist:
        messages.error(request, 'User not found. Please register again.')
        return redirect('register')
    
    return redirect('verify_otp')

def password_reset_request(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.get(email=email)
            
            # Create a reset token
            token = secrets.token_urlsafe(32)
            PasswordResetToken.objects.create(user=user, token=token)
            
            # Send reset email
            reset_url = request.build_absolute_uri(
                reverse('password_reset_confirm', kwargs={'token': token})
            )
            send_password_reset_email(user.email, reset_url)
            
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('login')
    else:
        form = CustomPasswordResetForm()
    return render(request, './accounts/password_reset_request.html', {'form': form})

def password_reset_confirm(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        if not reset_token.is_valid():
            messages.error(request, 'Invalid or expired reset link.')
            return redirect('password_reset_request')
            
        if request.method == 'POST':
            form = CustomSetPasswordForm(reset_token.user, request.POST)
            if form.is_valid():
                form.save()
                reset_token.is_used = True
                reset_token.save()
                messages.success(request, 'Your password has been reset successfully!')
                return redirect('login')
        else:
            form = CustomSetPasswordForm(reset_token.user)
            
        return render(request, './accounts/password_reset_confirm.html', {'form': form})
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid reset link.')
        return redirect('password_reset_request')

def send_otp_email(email, otp):
    subject = 'Your OTP for Account Verification'
    message = f'Your OTP is: {otp}\n\nThis OTP is valid for 5 minutes.'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

def send_password_reset_email(email, reset_url):
    subject = 'Password Reset Request'
    message = f'Click the following link to reset your password:\n\n{reset_url}\n\nThis link is valid for 1 hour.'
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )