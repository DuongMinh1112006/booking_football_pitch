from celery import shared_task
from .models import Bookings, TimeSlots
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def check_and_cancel_booking(booking_id):

    booking = Bookings.objects.get(id=booking_id)

    san_vua_dat = booking.timeslot.pitch
    san_cha = san_vua_dat.pitch_parent
    danh_sach_san_con = san_vua_dat.sub_pitches.all()

    ds_cac_san = []
    if san_cha:
        ds_cac_san.append(san_cha)
        san_cha_cua_cha = san_cha.pitch_parent
        if san_cha_cua_cha:
            ds_cac_san.append(san_cha_cua_cha)

    if danh_sach_san_con.exists():
        for san_con in danh_sach_san_con:
            ds_cac_san.append(san_con)
            ds_con_cua_san_con = san_con.sub_pitches.all()
            if ds_con_cua_san_con.exists():
                for con_cua_san_con in ds_con_cua_san_con:
                    ds_cac_san.append(con_cua_san_con)

    Bookings.objects.filter(
        timeslot__pitch__in = ds_cac_san,
        booking_date = booking.booking_date,
        timeslot__start_time = booking.timeslot.start_time,
        status = "LOCKED"
    ).update(status = "CANCELLED")

    if booking.status == 'PENDING':
        booking.status = 'CANCELLED'
        booking.save()
        print(f"[CELERY] Đã tự động hủy đơn {booking_id} do bom hàng!")


@shared_task
def send_otp_email_task(email, otp):
    subject = 'Mã xác thực tài khoản Đặt Sân Bóng'
    message = f'Chào bạn,\n\nMã OTP kích hoạt tài khoản của bạn là: {otp}\nMã này sẽ hết hạn sau 5 phút.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]

    send_mail(subject, message, email_from, recipient_list)
    return f"Đã gửi OTP đến {email}"