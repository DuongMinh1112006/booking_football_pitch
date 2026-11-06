from django.contrib import admin

# Register your models here.
from .models import Users, Bookings, Pitches, Payments, TimeSlots

admin.site.register(Users)
admin.site.register(Bookings)
admin.site.register(Pitches)
admin.site.register(Payments)
admin.site.register(TimeSlots)