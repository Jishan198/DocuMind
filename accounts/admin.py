from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'is_verified', 'is_staff', 'created_at']
    ordering = ['email']
    fieldsets = UserAdmin.fieldsets + (
        ('DocuMind', {'fields': ('is_verified',)}),
    )

# Register your models here.
