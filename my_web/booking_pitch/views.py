import json
import os
import re
import redis
import random

from .tasks import check_and_cancel_booking, send_otp_email_task

import requests
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import Bookings, Users, Payments, Pitches, TimeSlots
from django.http import JsonResponse
from datetime import timedelta
from django.db.models import Q
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from dotenv import load_dotenv
load_dotenv()

# Create your views here.

def create_booking(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Vui lòng đăng nhập trước khi đặt sân!'})
    else:
        data = json.loads(request.body)
        timeslot_id = data.get('timeslot_id')
        booking_date = data.get('booking_date')

        user = request.user
        timeslot = TimeSlots.objects.get(id=timeslot_id)

        #tạo khóa distributed lock redis để tránh race condition
        lock_key = f"lock_time_slot_{timeslot_id}_{booking_date}"
        lock_acquired = cache.add(lock_key, "locked", timeout=5)

        print(lock_key)

        if not lock_acquired:
            return JsonResponse({
                "status": "error",
                "message": "Sân này đang có người thao tác, vui lòng thử lại!"
            }, status=409)  # 409 là mã lỗi Conflict


        try:
            pre_booking = Bookings.objects.filter(timeslot=timeslot, booking_date=booking_date).filter( Q(status = "Locked") | Q(status = 'PENDING')).exists()

            if pre_booking:
                return JsonResponse({
                    "status": "error",
                    "message": "Sân này đã có người đặt, vui lòng thử lại!"
                })

            booking = Bookings.objects.create(
                user=user,
                timeslot=timeslot,
                booking_date=booking_date,
                status="PENDING"
            )

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

            ds_timeslot_lock = TimeSlots.objects.filter(
                pitch__in = ds_cac_san,
                start_time = booking.timeslot.start_time
            )

            ds_booking_lock =[]
            for ts in ds_timeslot_lock:
                ds_booking_lock.append(
                    Bookings(
                        user = user,
                        timeslot = ts,
                        booking_date = booking_date,
                        status = 'LOCKED'
                    )
                )

            if ds_booking_lock:
                Bookings.objects.bulk_create(ds_booking_lock)


            #dùng time to live của Redis để đếm ngược thời gian thanh toán
            # redis_client = redis.Redis.from_url(settings.REDIS_URL)
            # booking_id = booking.id
            # redis_client.setex(f"booking_expired:{booking_id}", 600, "PENDING")

            check_and_cancel_booking.apply_async(args=[booking.id], countdown=40)

            # Tạo URL thanh toán chứa ID của booking vừa tạo
            # reverse() sẽ tìm URL có name='payment' và nhét booking_moi.id vào <int:booking_id>
            redirect_url = reverse('payment', kwargs={'booking_id': booking.id})
            return JsonResponse({
                'status': 'success',
                'redirect_url' : redirect_url
            })

        finally:
            pass
            # cache.delete(lock_key)


def home_view(request):
    danh_sach_san = Pitches.objects.all()
    context = {
        'pitches' : danh_sach_san
    }
    return render(request, 'booking_pitch/home.html', context)

def get_timeslot(request):
    pitch_id = request.GET.get('pitch_id')
    date = request.GET.get('date')

    all_timeslots = TimeSlots.objects.filter(pitch_id = pitch_id).order_by('start_time')
    data = []
    for slot in all_timeslots:
        da_co_nguoi_dat = Bookings.objects.filter(
            timeslot = slot,
            booking_date = date,
        ).filter(
            ~Q(status='CANCELLED')
        ).exists()

        trang_thai = "Locked" if da_co_nguoi_dat else "Available"
        data.append({
            'id' : slot.id,
            'start_time':slot.start_time,
            'status' : trang_thai
        })

    return JsonResponse({'timeslots': data})


def sign_up(request):
    if request.method == "POST":
        ten_dang_nhap = request.POST.get("username")
        mat_khau = request.POST.get("password")
        phone_number = request.POST.get("phone_number")
        gmail = request.POST.get('gmail')
        name = request.POST.get("name")
        if Users.objects.filter(username = ten_dang_nhap).exists():
            return render(request, "booking_pitch/sign_up.html", {'error' : 'Tên đăng nhập đã tồn tại!'})

        user = Users.objects.create_user(
            username=ten_dang_nhap,
            name=name,
            password=mat_khau,
            gmail = gmail,
            phone_number = phone_number,
            is_active = False
        )
        user.save()

        otp = str(random.randint(100000, 999999))
        cache.set(f'otp_{ten_dang_nhap}', otp, timeout=300)
        send_otp_email_task.delay(gmail, otp)
        return redirect(f'/otp_authentication/?username={ten_dang_nhap}')

    return render(request, 'booking_pitch/sign_up.html')

def otp_authentication(request):
    username = request.GET.get("username") or request.POST.get("username", "")

    if request.method == "POST":
        otp_nhap = request.POST.get("otp").strip()
        otp_dung = cache.get(f"otp_{username}")

        if otp_dung is None:
            return render(request, "booking_pitch/otp_authentication.html",
                          {"username": username, "error": "Mã OTP đã hết hạn!"})

        if otp_nhap != otp_dung:
            return render(request, "booking_pitch/otp_authentication.html",
                          {"username": username, "error": "Mã OTP không đúng!"})

        Users.objects.filter(username=username).update(is_active=True)
        cache.delete(f"otp_{username}")
        return redirect("/login/")

    return render(request, "booking_pitch/otp_authentication.html", {"username": username})

def login_view(request):
    if request.method == "POST":
        ten_dang_nhap = request.POST.get("username")
        mat_khau = request.POST.get("password")
        user = authenticate(request, username = ten_dang_nhap, password = mat_khau)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'booking_pitch/home.html', {'error' : 'Tài khoản không tồn tại!'})
    return render(request, "booking_pitch/login.html")

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required(login_url='/login/')
def payment(request, booking_id):
    booking = get_object_or_404(Bookings, id=booking_id, user = request.user)

    VIETQR_API_URL = 'https://api.vietqr.io/v2/generate'

    headers = {
        'x-client-id': os.getenv('CLIENT_ID'),
        'x-api-key': os.getenv('API_KEY'),
        'Content-Type': 'application/json'
    }

    payload = {
        "accountNo": os.getenv('accountNo'),
        "accountName": os.getenv('accountName'),
        "acqId": 970415,
        "amount": int(booking.timeslot.price/100),
        "addInfo": f"SEVQR {booking.id}",
        "format": "text",
        "template": "compact2"
    }

    qr_url = None
    try:
        response = requests.post(VIETQR_API_URL, headers=headers, json=payload)
        response_data = response.json()
        # Nếu gọi API thành công (code '00' thường là mã thành công của VietQR)
        if response_data.get('code') == '00':
            qr_url = response_data['data']['qrDataURL']
    except Exception as e:
        print(f"Lỗi khi gọi API VietQR: {e}")

    thoi_gian_het_han = booking.created_at + timedelta(minutes=10)
    expire_timestamp = int(thoi_gian_het_han.timestamp() * 1000)

    context = {
        'booking' : booking,
        'qr_url' : qr_url,
        'expire_timestamp' : expire_timestamp
    }

    return render(request, 'booking_pitch/payment.html', context)

@csrf_exempt
def sepay_webhook(request):
    if request.method == 'POST':
        # Bóc gói JSON SePay gửi tới
        data = json.loads(request.body)

        transactionDate = data.get('transactionDate')
        code = data.get('code')
        transferAmount = data.get('transferAmount')

        content = data.get('content')
        if content:
            match = re.search(r'SEVQR\s*(\d+)', content, re.IGNORECASE)
            booking_id = int(match.group(1))
            booking = Bookings.objects.filter(id = booking_id).first()
            if booking:
                Payments.objects.create(
                    booking = booking,
                    content = content,
                    transferCode = code,
                    transactionDate = transactionDate,
                    amount = transferAmount,
                    status = 'PAID'
                )
                booking.status = "PAID"
                booking.save()

                channel_layer = get_channel_layer()
                room_group_name = f'payment_{booking_id}'

                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {
                        'type': 'payment_message',
                        'message': 'success'
                    }
                )

        # BẮT BUỘC trả về response 200/thành công để SePay biết đã nhận được tin
        return JsonResponse({'success': True})

    return JsonResponse({'success': False})



    # cách if else, dài và ko tối ưu duy trì, mở rộng, khó sửa lỗi.
    # user = Users.objects.first()
    # timeslot = TimeSlots.objects.get(id=90)
    # booking = Bookings.objects.create(
    #     user = user,
    #     timeslot = timeslot,
    #     booking_date = "2026-10-04",
    #     status = "Pending payment"
    # )
    # pitch_id = booking.timeslot.pitch.id
    # if pitch_id == "9/1":
    #     lock_1_timeslot = TimeSlots.objects.get(pitch_id = "7/1", start_time = booking.timeslot.start_time)
    #     Bookings.objects.create(
    #         user = user,
    #         timeslot = lock_1_timeslot,
    #         booking_date = "2026-10-04",
    #         status = "Locked"
    #     )
    #     lock_2_timeslot = TimeSlots.objects.get(pitch_id="7/2", start_time=booking.timeslot.start_time)
    #     Bookings.objects.create(
    #         user=user,
    #         timeslot = lock_2_timeslot,
    #         booking_date="2026-10-04",
    #         status="Locked"
    #     )
    # elif pitch_id == "9/2":
    #     lock_1_timeslot = TimeSlots.objects.get(pitch_id = "7/3", start_time = booking.timeslot.start_time)
    #     Bookings.objects.create(
    #         user = user,
    #         timeslot = lock_1_timeslot,
    #         booking_date = "2026-10-04",
    #         status = "Locked"
    #     )
    #     lock_2_timeslot = TimeSlots.objects.get(pitch_id="7/4", start_time=booking.timeslot.start_time)
    #     Bookings.objects.create(
    #         user=user,
    #         timeslot = lock_2_timeslot,
    #         booking_date="2026-10-04",
    #         status="Locked"
    #     )
