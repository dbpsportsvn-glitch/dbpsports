# Bối Cảnh Hiện Tại

- **Công việc đang tập trung:**
  - Chuan bi cac tinh nang khac (tam thoi khong co task muc tieu cap bach)

- **Các thay đổi gần đây:**
  - **Hoan thanh He thong Thong ke Luot nghe:** Tao model TrackPlayHistory de luu lich su nghe chi tiet, them play_count vao Track/UserTrack, API record-play voi logic 30s/50% va chong spam 5 phut, JS tu dong tracking khi play/pause/switch, admin interface dep voi % hoan thanh mau sac, hien thi luot nghe trong player (icon tai nghe giua thoi gian).
  - Hoan thanh Listening Lock cho Music Player: khoa trinh phat, chan dong/toggle/click ngoai, chan cuon nen; giu trang thai theo tai khoan va tu mo lai khi reload.
  - Hoan thanh Low Power Mode: them toggle trong Settings, tat hieu ung nang, giam update UI, dung class low-power, luu theo tai khoan.
  - Them Album Cover toan dien: User Track/Playlist + Global Track/Playlist; cap nhat MediaSession lock screen; fallback hinh mac dinh; cache-busting khi doi anh.
  - Giam quota upload ca nhan con 369MB va them goi y lien he admin xin mo rong.
  - **Hoàn thành tối ưu Music Player - Mobile Full-Screen & Performance Optimizations:** Đã thực hiện 7 cải tiến lớn cho music player đạt chuẩn 10/10 với performance hoàn hảo, mobile UX như native app (Spotify-like), và đáp ứng tất cả accessibility standards.
  - **Hoàn thành tối ưu hóa toàn diện Music Player với Auto-Play và Keyboard Shortcuts:** Music player giờ professional như Spotify với performance cao, security tốt, UX mượt mà, power-user friendly với full keyboard control.
  - **Hoàn thành tính năng Personal Music - Upload & Manage User Music:** Tính năng KHÁC BIỆT cho phép user upload nhạc riêng với quota 500MB, auto-extract metadata, quản lý playlists cá nhân.
  - **Hoàn thành Organization Shop System với đầy đủ tính năng:** Hệ thống shop riêng cho từng ban tổ chức (BTC) với đầy đủ tính năng frontend và backend, sẵn sàng sử dụng.

- **Các quyết định gần đây:**
  - **Quyết định về CSS Scoping Strategy cho Music Player:** Áp dụng CSS scoping pattern để tránh xung đột global styles. Tất cả selector của music player phải được prefix với `.music-player-popup` để chỉ áp dụng trong phạm vi component.
  - **Quyết định về Shop Search Architecture:** Thiết kế trang tìm kiếm shop BTC với giao diện đồng bộ với trang tìm việc để tạo trải nghiệm nhất quán.
  - **Quyết định về UX Navigation Strategy:** Thiết lập nguyên tắc điều hướng nhất quán trong toàn bộ hệ thống bằng cách loại bỏ `target="_blank"` khỏi tất cả các nút điều hướng chính.
  - **Quyết định về Organization Shop Architecture:** Thiết kế hệ thống shop riêng cho từng BTC với tính độc lập hoàn toàn.
  - **Quyết định về Tournament Discount Logic:** Cập nhật Tournament model để hỗ trợ cả Global Shop và Organization Shop.