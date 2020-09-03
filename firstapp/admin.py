from django.contrib import admin
from .models import events, registration, date_revenue, society_leads, state_connection

# Register your models here.

admin.site.register(events)
admin.site.register(date_revenue)
admin.site.register(society_leads)
admin.site.register(state_connection)

class RegistrationAdmin(admin.ModelAdmin):
    class Meta:
        model = registration
        fields = "__all__"
    list_display = ('name','event','email')
    search_fields =  ('name', 'event', 'email')

admin.site.register(registration,RegistrationAdmin)