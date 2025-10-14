# Fix Stadium Profile Form Error

## 🐛 Lỗi gặp phải

```
CrispyError at /users/stadium/create/
|as_crispy_field got passed an invalid or inexistent field
```

**Nguyên nhân:** Template `stadium_profile_form.html` đang sử dụng field `field_type` nhưng form `StadiumProfileForm` không bao gồm field này trong `fields`.

## 🔧 Giải pháp

### File đã sửa: `backend/users/forms.py`

**Trước:**
```python
class StadiumProfileForm(forms.ModelForm):
    class Meta:
        model = StadiumProfile
        fields = ['stadium_name', 'address', 'phone_number', 'description', 'logo']
        # ❌ Thiếu field_type và nhiều fields khác
```

**Sau:**
```python
class StadiumProfileForm(forms.ModelForm):
    class Meta:
        model = StadiumProfile
        fields = [
            'stadium_name', 'logo', 'description', 
            'address', 'region', 'location_detail', 
            'phone_number', 'email', 'website',
            'field_type', 'capacity', 'number_of_fields',  # ✅ Thêm field_type
            'amenities', 'rental_price_range',
            'bank_name', 'bank_account_number', 'bank_account_name',
            'payment_qr_code', 'operating_hours'
        ]
        labels = {
            'stadium_name': 'Tên sân bóng',
            'logo': 'Logo/Ảnh sân',
            'description': 'Mô tả sân bóng',
            'address': 'Địa chỉ chi tiết',
            'region': 'Khu vực',
            'location_detail': 'Tỉnh/Thành phố',
            'phone_number': 'Số điện thoại',
            'email': 'Email liên hệ',
            'website': 'Website',
            'field_type': 'Loại sân',  # ✅ Thêm label cho field_type
            'capacity': 'Sức chứa khán giả',
            'number_of_fields': 'Số sân',
            'amenities': 'Tiện ích',
            'rental_price_range': 'Giá thuê (khoảng)',
            'bank_name': 'Tên ngân hàng',
            'bank_account_number': 'Số tài khoản',
            'bank_account_name': 'Tên chủ tài khoản',
            'payment_qr_code': 'Mã QR thanh toán',
            'operating_hours': 'Giờ hoạt động',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'amenities': forms.Textarea(attrs={'rows': 3}),
            'operating_hours': forms.Textarea(attrs={'rows': 3}),
        }
```

## 📋 Các fields đã thêm

### Thông tin cơ bản
- ✅ `field_type` - Loại sân (dropdown với các lựa chọn)
- ✅ `capacity` - Sức chứa khán giả
- ✅ `number_of_fields` - Số sân

### Địa chỉ & Liên hệ  
- ✅ `region` - Khu vực (Miền Bắc/Trung/Nam)
- ✅ `location_detail` - Tỉnh/Thành phố
- ✅ `email` - Email liên hệ
- ✅ `website` - Website

### Dịch vụ & Tiện ích
- ✅ `amenities` - Tiện ích (textarea)
- ✅ `rental_price_range` - Giá thuê

### Thanh toán
- ✅ `bank_name` - Tên ngân hàng
- ✅ `bank_account_number` - Số tài khoản
- ✅ `bank_account_name` - Tên chủ tài khoản
- ✅ `payment_qr_code` - Mã QR thanh toán

### Giờ hoạt động
- ✅ `operating_hours` - Giờ hoạt động (textarea)

## 🎯 Kết quả

✅ **Lỗi CrispyError đã được sửa**
✅ **Form hiện tại bao gồm tất cả fields từ model StadiumProfile**
✅ **Template có thể render đúng tất cả fields**
✅ **Labels và widgets được cấu hình phù hợp**

## 🧪 Test

1. **Truy cập:** `http://127.0.0.1:8000/users/stadium/create/`
2. **Kết quả mong muốn:** Form tạo hồ sơ sân bóng hiển thị đầy đủ các fields
3. **Không còn lỗi:** CrispyError

## 📝 Notes

- Form hiện tại bao gồm **tất cả** fields từ model `StadiumProfile`
- Tất cả fields đều có labels tiếng Việt phù hợp
- Textarea fields được cấu hình với số dòng phù hợp
- Form có thể tạo và cập nhật hồ sơ sân bóng đầy đủ

---

**Status:** ✅ **FIXED**  
**Date:** 14/10/2025  
**Files changed:** `backend/users/forms.py`
