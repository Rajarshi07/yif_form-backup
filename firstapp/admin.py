from django.contrib import admin
from .models import events, registration, date_revenue, society_leads, state_connection, coupons

# Register your models here.

admin.site.register(events)
admin.site.register(date_revenue)
admin.site.register(society_leads)
admin.site.register(state_connection)
admin.site.register(coupons)

class RegistrationAdmin(admin.ModelAdmin):
    class Meta:
        model = registration
        fields = "__all__"
    list_display = ('name','event','email','participant_id',"coupon","transaction_id","timestamp")
    search_fields =  ('name', 'event', 'email', 'participant_id',"coupon","transaction_id","timestamp")

admin.site.register(registration,RegistrationAdmin)
