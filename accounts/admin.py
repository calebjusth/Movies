from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.html import format_html
from django.utils import timezone

@admin.action(description="Mark selected users as verified")
def make_verified(modeladmin, request, queryset):
    queryset.update(is_verified=True)

@admin.action(description="Clear OTP for selected users")
def clear_otp(modeladmin, request, queryset):
    queryset.update(otp=None, otp_created_at=None)

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_verified', 'otp_display', 'otp_created_at', 'last_login', 'is_staff')
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'otp')
    ordering = ('-date_joined',)
    actions = [make_verified, clear_otp]

    fieldsets = UserAdmin.fieldsets + (
        ('Verification Info', {'fields': ('is_verified', 'otp', 'otp_created_at')}),
    )
    readonly_fields = ('otp_created_at',)

    def otp_display(self, obj):
        if obj.otp and obj.otp_created_at:
            expiry = obj.otp_created_at + timezone.timedelta(minutes=5)
            expired = timezone.now() > expiry
            color = 'green' if not expired else 'red'
            return format_html('<b style="color:{};">{}</b>', color, obj.otp)
        return '-'
    otp_display.short_description = 'OTP'

admin.site.register(CustomUser, CustomUserAdmin)
