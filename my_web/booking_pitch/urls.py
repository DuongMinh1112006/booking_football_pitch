from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home_page'),
    path('get_timeslot/', views.get_timeslot, name="get_timeslot"),
    path('booking/', views.create_booking, name='booking'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.sign_up, name='sign_up'),
    path('logout/', views.logout_view, name='logout'),
    path('payment/<int:booking_id>/', views.payment, name='payment'),
    path('api/webhook/sepay/', views.sepay_webhook, name='sepay_webhook'),
    path("otp_authentication/", views.otp_authentication, name="otp_authentication"),
]