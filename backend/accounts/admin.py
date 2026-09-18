from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import ClientUser


@admin.register(ClientUser)
class ClientUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Client details", {"fields": ("referral_code",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Client details", {"fields": ("email", "referral_code")}),)
    list_display = ("username", "email", "first_name", "last_name", "referral_code", "is_staff")

# Register your models here.
