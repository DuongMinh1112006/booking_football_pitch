import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class PaymentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # 1. Lấy order_id từ đường dẫn URL mà client vừa gọi
        self.booking_id = self.scope['url_route']['kwargs']['booking_id']
        self.room_group_name = f'payment_{self.booking_id}'

        # 2. Đưa đường ống của người dùng này vào một "phòng chờ" riêng biệt
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )


        # 3. Chấp nhận kết nối mở đường ống
        await self.accept()

    async def disconnect(self, close_code):
        # Khi người dùng tắt trang, tự động đá họ ra khỏi phòng để dọn tài nguyên
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Hàm này nhận tin nhắn từ Redis đẩy xuống và ném thẳng qua ống kính cho trình duyệt
    async def payment_message(self, event):
        message = event['message']

        # Gửi dữ liệu dạng JSON xuống cho JavaScript ở Frontend hứng
        await self.send(text_data=json.dumps({
            'status': message
        }))