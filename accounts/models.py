from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import random
import string

class CustomUser(AbstractUser):
    is_verified = models.BooleanField(default=False)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    
    def generate_otp(self):
        """Generate a 6-digit OTP and set expiration time (5 minutes)"""
        self.otp = ''.join(random.choices(string.digits, k=6))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp
    
    def is_otp_valid(self, otp):
        """Check if OTP is valid and not expired"""
        if not self.otp or not self.otp_created_at:
            return False
        if self.otp != otp:
            return False
        if (timezone.now() - self.otp_created_at).total_seconds() > 300:  # 5 minutes
            return False
        return True

class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    
    def is_valid(self):
        """Token is valid for 1 hour and not used"""
        return not self.is_used and (timezone.now() - self.created_at).total_seconds() < 3600