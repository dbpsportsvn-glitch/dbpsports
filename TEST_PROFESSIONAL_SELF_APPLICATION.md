# Test: Chuyên gia không thể tự ứng tuyển

## 🎯 Mục tiêu
Kiểm tra xem chuyên gia có thể tự ứng tuyển vào chính tin đăng tìm việc của mình hay không.

## ✅ Những gì đã sửa
1. **Template logic** - Thêm kiểm tra `job.professional_user == user`
2. **Backend validation** - Thêm `professional_user` vào logic `is_organizer`
3. **Error messages** - Thêm thông báo lỗi cụ thể

## 🧪 Test Cases

### Test Case 1: Chuyên gia xem tin đăng của mình
1. **Đăng tin tìm việc** (đã test thành công)
2. **Vào trang chi tiết tin đăng** của chính mình
3. **Kiểm tra giao diện:**
   - ❌ Không hiển thị form ứng tuyển
   - ✅ Hiển thị thông báo: "Đây là tin đăng tìm việc của bạn. Bạn không thể ứng tuyển vào chính tin đăng của mình."

### Test Case 2: Chuyên gia cố gắng ứng tuyển (nếu có cách nào đó)
1. **Nếu có cách bypass frontend** (thông qua URL trực tiếp, script, etc.)
2. **Backend sẽ chặn** và hiển thị thông báo lỗi

### Test Case 3: User khác ứng tuyển vào tin của chuyên gia
1. **Đăng nhập user khác** (không phải người đăng tin)
2. **Vào trang chi tiết tin đăng** của chuyên gia
3. **Kiểm tra giao diện:**
   - ✅ Hiển thị form ứng tuyển bình thường
   - ✅ Có thể submit thành công

## 🔍 Cách kiểm tra

### Bước 1: Tạo tin đăng
1. Đăng nhập với user có vai trò chuyên gia
2. Vào "Đăng tin tìm việc"
3. Điền form và submit thành công

### Bước 2: Kiểm tra self-application prevention
1. **Từ trang professional dashboard**, click vào tin đăng vừa tạo
2. **Hoặc từ job market**, tìm tin đăng của mình
3. **Kiểm tra:** Không có form ứng tuyển, có thông báo thông tin

### Bước 3: Test với user khác
1. **Đăng nhập user khác** (có thể là chuyên gia khác hoặc user thường)
2. **Vào trang chi tiết tin đăng** của chuyên gia đầu tiên
3. **Kiểm tra:** Có form ứng tuyển bình thường

## 🎯 Kỳ vọng
- ✅ Chuyên gia **KHÔNG THỂ** tự ứng tuyển vào tin của mình
- ✅ User khác **CÓ THỂ** ứng tuyển vào tin của chuyên gia
- ✅ Thông báo lỗi rõ ràng và thân thiện

## 📋 Báo cáo kết quả
Hãy test và báo cáo:
1. **Có thấy thông báo** "Đây là tin đăng tìm việc của bạn..." không?
2. **Form ứng tuyển có bị ẩn** không?
3. **User khác có thể ứng tuyển** bình thường không?
