# Lịch Sử Thay Đổi Dự Án

*File này lưu trữ lịch sử các thay đổi cũ đã được di chuyển khỏi activeContext.md để duy trì tính gọn gàng.*

## Thay Đổi Đã Hoàn Thành (Lịch Sử)

### Admin & Quản Lý
- **Việt hóa và sắp xếp lại trang quản trị admin:** Hoàn thành việt hóa toàn bộ trang quản trị Django admin với tiêu đề "DBP Sports - Trung tâm Quản trị", sắp xếp lại thứ tự các app theo logic nghiệp vụ (Giải đấu → Tổ chức → Người dùng → Nhà tài trợ → Cửa hàng → Tin tức), việt hóa tên hiển thị tất cả các models trong mỗi app, thêm emoji icons để phân biệt các model, và di chuyển action "Xóa" xuống cuối cùng trong dropdown actions để tránh nhầm lẫn.

### SEO & Structured Data
- **SEO Optimization - Structured Data Event:** Hoàn thành việc khắc phục các vấn đề Structured Data Event mà Google Analytics báo cáo cho dbpsports.com. Đã thêm đầy đủ các trường bắt buộc (offers, image, endDate, organizer, performer) vào các template quan trọng: tournament_detail.html, match_detail.html, home.html, active_list.html, archive.html. Sử dụng Schema.org Event với JSON-LD format để cải thiện SEO và hiển thị rich results trên Google Search.

### UI/UX Design
- **Thiết kế lại tab tổng quan:** Hoàn thành việc thiết kế lại tab tổng quan với các thẻ thông tin đồng bộ và đẹp mắt. Bao gồm Bio Card, Personal Info Card với role badges có icon đẹp mắt, Professional Summary Card, Achievements Card và Reviews Card. Sắp xếp lại thứ tự thẻ để thông tin cá nhân và chuyên môn hiển thị trước thành tích và đánh giá.
- **Thêm QR code vào Stadium Profile:** Tích hợp mã QR thanh toán vào Stadium Profile Card trong tab chuyên môn với thiết kế center alignment, kích thước 120px và styling đẹp mắt với background và border.
- **Thiết kế lại trang hồ sơ công khai:** Đã hoàn thành việc thiết kế lại giao diện trang hồ sơ công khai với phong cách theme giống các tab trong trang chi tiết giải đấu. Bao gồm modern navigation với gradient tím, backdrop blur, responsive design và đồng bộ desktop/mobile.
- **Redesign tab chuyên môn:** Thiết kế lại hoàn toàn tab chuyên môn với các thẻ thông tin đồng bộ và đẹp mắt cho tất cả vai trò (Coach, Sponsor, Stadium, Commentator, Media, Referee). Mỗi thẻ có avatar với gradient, info grid, status badges, và responsive design.

### Templates & Pages
- **Nâng cấp template trang Lưu trữ Giải đấu:** Đã nâng cấp template trang Lưu trữ Giải đấu (archive.html) với giao diện hiện đại: gradient styling, responsive grid layout, animation effects, và màu sắc tím để phân biệt với trang giải đấu chính.

### System Updates
- **Cập nhật quy tắc update-memory-bank-agent:** Đã cập nhật quy tắc update-memory-bank-agent để bỏ bước hỏi xác nhận.
- **Soát xét và cập nhật toàn bộ Memory Bank:** Đã soát xét và cập nhật toàn bộ Memory Bank để phản ánh đúng thực tế dự án.

### Bug Fixes
- **Sửa lỗi cập nhật mã QR nhà tài trợ:** Khắc phục lỗi form không lưu được mã QR do conflict 2 model SponsorProfile. Đã migrate database và chuyển sang model mới từ users.models.
- **Tối ưu UI hiển thị vai trò:** Làm gọn gàng hơn khu vực hiển thị thông tin Coach, Stadium, Sponsor với layout compact và CSS effects.
- **Test và xác nhận hệ thống email hoàn hảo:** Đã test toàn bộ 19 email templates và xác nhận hệ thống email backend hoạt động hoàn hảo. SMTP server mail.dbpsports.com:465 hoạt động ổn định, tất cả templates render đúng và đẹp mắt với thiết kế purple gradient chuyên nghiệp. Đã dọn dẹp tất cả file test và template cũ, workspace backend giờ đã sạch sẽ và chuyên nghiệp.
- **Hoàn thành tích hợp payment_rejected.html:** Đã thêm trạng thái "Từ chối" vào dropdown payment_status trong admin, tạo migration để cập nhật database, thêm admin action "reject_payments" để từ chối hàng loạt, cập nhật template team_detail.html để hiển thị badge "Từ chối" và nút "Tải lại hóa đơn", và xóa tất cả debug statements. Email từ chối hoạt động hoàn hảo.
- **Thêm nút đăng ký ngay vào trang chi tiết giải đấu:** Đã thêm nút "Đăng ký ngay" vào header trang chi tiết giải đấu bên cạnh status badge, với styling gradient tím đồng bộ với thiết kế trang, responsive trên mobile, và chỉ hiển thị khi giải đấu đang mở đăng ký và người dùng đã đăng nhập.

## Quyết Định Kỹ Thuật (Lịch Sử)

### Admin Interface
- **Quyết định về Admin Interface:** Quyết định việt hóa toàn bộ trang quản trị Django admin để dễ dàng sử dụng hơn cho người dùng Việt Nam. Sắp xếp lại thứ tự các app theo logic nghiệp vụ với Giải đấu ưu tiên cao nhất, sau đó đến Tổ chức, Người dùng, Nhà tài trợ, Cửa hàng, Tin tức. Thêm emoji icons để phân biệt các model và di chuyển action "Xóa" xuống cuối cùng để tránh nhầm lẫn.

### SEO & Data Structure
- **Quyết định về SEO Structured Data:** Sử dụng Schema.org Event với JSON-LD format để khắc phục các vấn đề Structured Data mà Google Analytics báo cáo. Thêm đầy đủ các trường bắt buộc (offers, image, endDate, organizer, performer) với fallback values và dynamic eventStatus dựa trên trạng thái giải đấu. Sử dụng ItemList cho danh sách giải đấu và SportsEvent cho từng sự kiện cụ thể.
- **Quyết định về Overview Tab Design:** Thiết kế lại tab tổng quan với các thẻ thông tin đồng bộ, sắp xếp lại thứ tự để thông tin cá nhân và chuyên môn hiển thị trước thành tích và đánh giá. Thêm role badges có icon đẹp mắt cho từng vai trò.
- **Quyết định về QR Code Integration:** Tích hợp mã QR thanh toán vào Stadium Profile Card với thiết kế center alignment, kích thước 120px và styling đẹp mắt để người dùng dễ dàng quét và thanh toán.

### Design System
- **Quyết định về Profile Design:** Thiết kế lại trang hồ sơ công khai theo phong cách modern-tournament-nav với gradient tím (#667eea → #764ba2), backdrop blur, và responsive design để đồng bộ với trang chi tiết giải đấu.
- **Quyết định về Professional Cards:** Sử dụng layout grid responsive (col-lg-6 col-xl-4) với các thẻ thông tin đồng bộ cho tất cả vai trò chuyên môn, mỗi thẻ có avatar với gradient, info grid, status badges và hover effects.

### Technical Decisions
- **Quyết định về SponsorProfile:** Xóa model cũ trong sponsors.models, chuyển toàn bộ sang users.models.SponsorProfile để tránh conflict và có đầy đủ fields.
- **Quyết định về UI:** Sử dụng layout compact cho profile cards với small text, ít padding, và rating badges để tiết kiệm không gian hiển thị.
- **Quyết định về URL Reversing:** Để xử lý lỗi `NoReverseMatch`, quyết định sử dụng `user.email` làm giá trị thay thế (fallback) cho `user.username` khi tạo URL cho hồ sơ công khai (`public_profile`).
- **Quyết định không yêu cầu xác nhận khi cập nhật Memory Bank:** Để tăng tốc workflow.

---
*Lần cuối cập nhật: Tháng 1/2025 - Di chuyển từ activeContext.md*
