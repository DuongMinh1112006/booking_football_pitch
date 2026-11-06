from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class Users(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    phone_number = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100)
    gmail = models.EmailField(max_length=100)

    def __str__(self):
        return self.name.title()


class Pitches(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    type = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    pitch_parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_pitches")

    def __str__(self):
        return f"Sân {self.type} số {self.name}"



class Bookings(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey("Users", on_delete=models.PROTECT)  #Lấy id của bảng Users làm khóa ngoại
    timeslot = models.ForeignKey("TimeSlots", on_delete=models.CASCADE) #Lấy id của bảng TimeSlots làm khóa ngoại

    booking_date = models.DateField()
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"ID:{self.id} {self.user.name.title()}  Date:{self.booking_date} Giờ:{self.timeslot.start_time} Sân:{self.timeslot.pitch.id} Status:{self.status}"



class TimeSlots(models.Model):
    id = models.IntegerField(primary_key=True)

    pitch = models.ForeignKey("Pitches", on_delete=models.CASCADE) #Lấy id của bảng Pitches làm khóa ngoại

    start_time = models.TimeField()
    end_time = models.TimeField()
    price = models.DecimalField(max_digits=10, decimal_places=0)

    def __str__(self):
        return f"ID:{self.id}  Sân:{self.pitch.id}  Giờ:{self.start_time}"



class Payments(models.Model):
    id = models.BigAutoField(primary_key=True)

    booking = models.ForeignKey("Bookings", on_delete=models.CASCADE)# Lấy id của bảng Bookings làm khóa ngoại
    transferCode = models.CharField(max_length = 100, null=True, blank=True)
    transactionDate = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=0)

    content = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=100)

    def __str__(self):
        return f"Id:{self.id}  Booking ID:{self.booking.id}"
