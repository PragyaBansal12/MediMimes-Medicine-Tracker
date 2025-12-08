from django.contrib import admin
from .models import Medication, DoseLog, UserProfile, Appointment

# Register basic models
admin.site.register(Medication)
admin.site.register(DoseLog)

# --- THE NEW REGISTRY TOOLS ---

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """The tool used by Admins to authorize Doctors."""
    list_display = ('user', 'role', 'specialty')
    list_filter = ('role',)

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """The master oversight table for the Admin."""
    list_display = ('patient', 'doctor', 'status', 'created_at')
    list_filter = ('status', 'created_at')