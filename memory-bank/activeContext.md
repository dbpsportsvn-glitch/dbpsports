# Bối Cảnh Hiện Tại

- **Công việc đang tập trung:**
  - (Sẽ được cập nhật khi có task mới)

- **Các thay đổi gần đây:**
  - Đã nâng cấp template trang Lưu trữ Giải đấu (archive.html) với giao diện hiện đại: gradient styling, responsive grid layout, animation effects, và màu sắc tím để phân biệt với trang giải đấu chính.
  - Đã cập nhật quy tắc update-memory-bank-agent để bỏ bước hỏi xác nhận.
  - Đã soát xét và cập nhật toàn bộ Memory Bank để phản ánh đúng thực tế dự án.
  - **Sửa lỗi cập nhật mã QR nhà tài trợ:** Khắc phục lỗi form không lưu được mã QR do conflict 2 model SponsorProfile. Đã migrate database và chuyển sang model mới từ users.models.
  - **Tối ưu UI hiển thị vai trò:** Làm gọn gàng hơn khu vực hiển thị thông tin Coach, Stadium, Sponsor với layout compact và CSS effects.

- **Các quyết định gần đây:**
  - Quyết định sử dụng màu tím (purple/violet) cho trang Lưu trữ thay vì xanh dương để phân biệt rõ ràng với trang Giải đấu đang hoạt động.
  - Quyết định không yêu cầu xác nhận khi cập nhật Memory Bank để tăng tốc workflow.
  - **Quyết định về SponsorProfile:** Xóa model cũ trong sponsors.models, chuyển toàn bộ sang users.models.SponsorProfile để tránh conflict và có đầy đủ fields.
  - **Quyết định về UI:** Sử dụng layout compact cho profile cards với small text, ít padding, và rating badges để tiết kiệm không gian hiển thị.