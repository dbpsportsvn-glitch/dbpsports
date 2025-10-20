# Bối Cảnh Hiện Tại

- **Công việc đang tập trung:**
  - Tối ưu hóa Memory Bank và dọn dẹp thông tin cũ
  - Chuẩn bị cho các tính năng mới trong tương lai

- **Các thay đổi gần đây:**
  - **Hoàn thành tối ưu Music Player - Mobile Full-Screen & Performance Optimizations:** Đã thực hiện 7 cải tiến lớn cho music player đạt chuẩn 10/10 với performance hoàn hảo, mobile UX như native app (Spotify-like), và đáp ứng tất cả accessibility standards.
  - **Hoàn thành tối ưu hóa toàn diện Music Player với Auto-Play và Keyboard Shortcuts:** Music player giờ professional như Spotify với performance cao, security tốt, UX mượt mà, power-user friendly với full keyboard control.
  - **Hoàn thành tính năng Personal Music - Upload & Manage User Music:** Tính năng KHÁC BIỆT cho phép user upload nhạc riêng với quota 500MB, auto-extract metadata, quản lý playlists cá nhân.
  - **Hoàn thành Organization Shop System với đầy đủ tính năng:** Hệ thống shop riêng cho từng ban tổ chức (BTC) với đầy đủ tính năng frontend và backend, sẵn sàng sử dụng.
  - **Hoàn thành trang tìm kiếm shop BTC:** Giao diện hiện đại đồng bộ với trang tìm việc, bộ lọc thông minh, responsive design cho mọi thiết bị.

- **Các quyết định gần đây:**
  - **Quyết định về CSS Scoping Strategy cho Music Player:** Áp dụng CSS scoping pattern để tránh xung đột global styles. Tất cả selector của music player phải được prefix với `.music-player-popup` để chỉ áp dụng trong phạm vi component.
  - **Quyết định về Shop Search Architecture:** Thiết kế trang tìm kiếm shop BTC với giao diện đồng bộ với trang tìm việc để tạo trải nghiệm nhất quán.
  - **Quyết định về UX Navigation Strategy:** Thiết lập nguyên tắc điều hướng nhất quán trong toàn bộ hệ thống bằng cách loại bỏ `target="_blank"` khỏi tất cả các nút điều hướng chính.
  - **Quyết định về Organization Shop Architecture:** Thiết kế hệ thống shop riêng cho từng BTC với tính độc lập hoàn toàn.
  - **Quyết định về Tournament Discount Logic:** Cập nhật Tournament model để hỗ trợ cả Global Shop và Organization Shop.