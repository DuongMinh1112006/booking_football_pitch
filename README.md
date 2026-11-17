# Hệ thống Web đặt sân bóng trực tuyến

Hệ thống quản lý và đặt sân bóng đá trực tuyến theo thời gian thực, hỗ trợ thanh toán tự động qua mã QR và đóng gói triển khai đa dịch vụ trên Linux VPS.

**Demo:** [http://103.165.145.102](http://103.165.145.102)

---

## Tính năng chính

1. **Tìm kiếm và đặt sân bóng trực tuyến:**
   - Người dùng có thể xem danh sách sân bóng, kiểm tra các khung giờ còn trống theo ngày, chọn sân phù hợp và thực hiện đặt lịch trực tiếp trên website.
   - Hệ thống tự động ngăn chặn tình trạng hai người đặt trùng cùng một sân vào một khung giờ.

2. **Quản lý sân ghép linh hoạt (Sân lớn – Sân nhỏ):**
   - Hỗ trợ mô hình sân ghép thực tế (ví dụ: sân 7 người được ghép từ 2 sân 5 người).
   - Khi có người đặt sân lớn, hệ thống tự động khóa lịch của các sân nhỏ cấu thành trong cùng khung giờ đó (và ngược lại), đảm bảo không xảy ra chồng chéo lịch thi đấu.

3. **Thanh toán chuyển khoản qua mã QR tự động:**
   - Tự động tạo mã QR thanh toán riêng cho từng đơn đặt sân.
   - Ngay khi người dùng chuyển khoản thành công, hệ thống tự động xác nhận và cập nhật trạng thái đặt sân ngay lập tức trên màn hình mà không cần tải lại trang hay chờ nhân viên duyệt thủ công.

4. **Giữ chỗ tạm thời và tự động hủy đơn quá hạn:**
   - Khi người dùng bấm đặt sân, hệ thống giữ chỗ trong 10 phút để thực hiện thanh toán.
   - Nếu quá thời hạn thanh toán mà giao dịch chưa hoàn tất, đơn đặt sân sẽ tự động hủy và mở lại khung giờ trống cho người khác đặt.

5. **Đăng ký tài khoản và xác thực qua Email:**
   - Hỗ trợ người dùng đăng ký, đăng nhập, xác thực tài khoản qua email và theo dõi lại toàn bộ lịch sử đặt sân của cá nhân.

6. **Quản trị hệ thống dành cho chủ sân:**
   - Cho phép quản trị viên thêm/sửa/xóa thông tin sân bóng, thiết lập mối quan hệ sân ghép, điều chỉnh khung giờ, giá thuê và theo dõi toàn bộ danh sách đơn đặt sân.
---

## Công nghệ sử dụng

- **Back-end:** Python, Django, Django Channels (ASGI / Daphne), Celery
- **Database & Caching:** PostgreSQL, Redis
- **DevOps & Infrastructure:** Docker, Docker Compose, Nginx (Reverse Proxy & WebSocket Upgrade), Ubuntu VPS
- **Front-end:** HTML, CSS, JavaScript (WebSocket Client)
---
## Giao diện chính hệ thống
**1. Trang chủ, khung giờ chọn sân**
<img width="1296" height="648" alt="image" src="https://github.com/user-attachments/assets/7bb3786c-06fd-474e-868b-f1f1f7d15c29" />
*Người dùng đăng nhập thành công, chọn loại sân, số sân, ngày sau đó chọn khung giờ đá. Sau đó toàn bộ khung giờ sẽ hiện ra, người dùng bấm vào khung giờ cần đặt. Khung giờ không chọn được là khung giờ đã có người đặt*  
<br>

**2. Thanh toán**
<img width="1853" height="950" alt="image" src="https://github.com/user-attachments/assets/c7d623e0-bd31-4fc3-83f2-1611004d484b" />
*Giao diện trang thánh toán, gồm các thông tin người đặt, sân, khung giờ, ngày đặt bên trái. Người dùng quét mã QR bên phải để thanh toán.*
<br>

**3. Thanh toán thành công**
<img width="1853" height="950" alt="image" src="https://github.com/user-attachments/assets/36601410-08ab-4e09-aa6a-6a177e67922a" />
*Khi thanh toán thành công hệ thống gửi thông báo trên màn hình*
<br>

**4. Dữ liệu được lưu trữ**
<img width="1910" height="958" alt="image" src="https://github.com/user-attachments/assets/80732861-9642-43a5-b177-f60926a96d6d" />
*Đơn thanh toán thành công sẽ được lưu trữ vào tài khoản admin*
<br>

---
## Hướng dẫn cài đặt hệ thống


