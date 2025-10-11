# Hướng Dẫn Quản Lý Ví Điện Tử

## Tổng Quan

Dự án đã được cập nhật để hỗ trợ đầy đủ phương thức thanh toán qua ví điện tử, bao gồm:
- ✅ Model `EWalletAccount` để lưu thông tin ví điện tử
- ✅ Trường `qr_code` để upload mã QR cho từng ví
- ✅ Trang admin để quản lý ví điện tử
- ✅ Hiển thị thông tin ví điện tử trên trang thanh toán
- ✅ Upload hóa đơn thanh toán cho ví điện tử

## Cách Sử Dụng

### 1. Tạo Dữ Liệu Mẫu (Lần Đầu)

Chạy lệnh sau để tạo dữ liệu mẫu:

```bash
cd backend
python manage.py create_ewallet_sample
```

Lệnh này sẽ tạo:
- 1 Payment Method: "Ví điện tử"
- 3 Ví điện tử mẫu: Momo, ZaloPay, VNPay

### 2. Cập Nhật Thông Tin Trong Admin

1. Truy cập Django Admin: `http://localhost:8000/admin/`
2. Vào mục **Shop > Ví điện tử (E-Wallet Account)**
3. Chỉnh sửa từng ví điện tử:
   - **Wallet Name**: Tên ví (VD: Momo, ZaloPay, VNPay)
   - **Account Info**: Số điện thoại hoặc ID tài khoản
   - **QR Code**: Upload mã QR thanh toán
   - **Order**: Thứ tự hiển thị
   - **Is Active**: Kích hoạt/Tắt ví

### 3. Upload Mã QR

#### Cách 1: Qua Admin
1. Vào **Shop > Ví điện tử**
2. Chọn ví cần cập nhật
3. Click vào "Choose File" ở trường **QR Code**
4. Chọn file ảnh QR code (JPG, PNG)
5. Click **Save**

#### Cách 2: Qua Payment Method
1. Vào **Shop > Payment Method**
2. Chọn "Ví điện tử"
3. Trong phần **E-Wallet Accounts** ở dưới, cập nhật QR code
4. Click **Save**

### 4. Cách Khách Hàng Sử Dụng

Khi khách hàng thanh toán:
1. Chọn phương thức **"Ví điện tử"**
2. Click nút **"Xem thông tin ví điện tử"**
3. Hiển thị danh sách ví với:
   - Tên ví
   - Thông tin tài khoản (có nút copy)
   - Mã QR để quét
4. Khách hàng có thể:
   - Quét mã QR để thanh toán
   - Hoặc copy thông tin tài khoản để chuyển thủ công
5. Upload hóa đơn thanh toán để xác nhận nhanh hơn

## Cấu Trúc Database

### Model: EWalletAccount

```python
class EWalletAccount(models.Model):
    payment_method = ForeignKey(PaymentMethod)  # Liên kết với payment method
    wallet_name = CharField                      # Tên ví (Momo, ZaloPay, etc)
    account_info = CharField                     # Số điện thoại/ID
    qr_code = ImageField                         # Mã QR
    is_active = BooleanField                     # Kích hoạt
    order = PositiveIntegerField                 # Thứ tự hiển thị
```

## So Sánh với Chuyển Khoản Ngân Hàng

| Tính năng | Ngân hàng | Ví điện tử |
|-----------|-----------|------------|
| Model | `BankAccount` | `EWalletAccount` |
| Thông tin chính | Tên NH, STK, Chủ TK, Chi nhánh | Tên ví, Thông tin TK |
| QR Code | ✅ Có | ✅ Có |
| Upload hóa đơn | ✅ Có | ✅ Có |
| Nút copy | ✅ Số TK | ✅ Thông tin TK |

## Lưu Ý Quan Trọng

1. **Bảo mật thông tin**
   - Không để lộ thông tin tài khoản thật trên môi trường test
   - Sử dụng thông tin demo khi dev

2. **Upload QR Code**
   - File ảnh nên < 2MB
   - Format: JPG, PNG
   - Kích thước khuyến nghị: 500x500px trở lên

3. **Quản lý ví**
   - Chỉ active các ví đang sử dụng
   - Cập nhật order để sắp xếp thứ tự hiển thị

4. **Kiểm tra**
   - Sau khi setup, test toàn bộ flow thanh toán
   - Kiểm tra QR code hiển thị đúng
   - Test upload hóa đơn

## Troubleshooting

### Không thấy ví điện tử trên trang thanh toán?
- Kiểm tra Payment Method "Ví điện tử" có `is_active=True`
- Kiểm tra có ít nhất 1 EWalletAccount với `is_active=True`

### QR code không hiển thị?
- Kiểm tra file QR đã upload chưa
- Kiểm tra đường dẫn media đã config đúng chưa
- Xem console log có lỗi không

### Không upload được hóa đơn?
- Kiểm tra settings.py: `MEDIA_URL` và `MEDIA_ROOT`
- Kiểm tra quyền ghi vào thư mục media
- Kiểm tra dung lượng file (max: 10MB)

## Update Log

**2025-10-11**: 
- Thêm phần hiển thị ví điện tử trong checkout.html
- Thêm xử lý show/hide cho e_wallet info
- Thêm upload hóa đơn cho ví điện tử
- Thêm script tạo dữ liệu mẫu
- Thêm tài liệu hướng dẫn

## Liên Hệ

Nếu có vấn đề hoặc câu hỏi, vui lòng liên hệ team dev.

