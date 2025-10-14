# Tóm Tắt Dự Án: DBP Sports - Nền tảng Quản lý Thể thao

- **Mục tiêu chính:** Xây dựng một nền tảng web toàn diện để quản lý các giải đấu thể thao, kết nối cộng đồng cầu thủ, đội bóng, nhà tài trợ, và người hâm mộ.
- **Phạm vi:** Nền tảng cung cấp các công cụ để tổ chức giải đấu, quản lý đội bóng, theo dõi lịch thi đấu, cập nhật kết quả, và tạo một hệ sinh thái thể thao chuyên nghiệp và bán chuyên.

- **Các module chính:**
  - **Core (dbpsports_core):** Lõi hệ thống Django, cấu hình settings, URLs chính.
  - **Users:** Quản lý người dùng và hệ thống vai trò đa dạng.
  - **Tournaments:** Quản lý giải đấu, đội bóng, cầu thủ, lịch thi đấu, kết quả, ngân sách.
  - **Organizations:** Dành cho các đơn vị/tổ chức đứng ra tạo giải đấu.
  - **Sponsors:** Quản lý các nhà tài trợ và các gói tài trợ.
  - **Shop:** Cửa hàng trực tuyến bán các sản phẩm thể thao.
  - **Blog:** Kênh tin tức, bài viết về các giải đấu và sự kiện.

- **Các vai trò người dùng:**
  - **ORGANIZER (Ban Tổ chức):** Đăng cai và quản lý giải đấu, công cụ quản lý chuyên nghiệp.
  - **PLAYER (Cầu thủ):** Tham gia đội bóng, ghi nhận thành tích, nhận phiếu bầu.
  - **COACH (Huấn luyện viên):** Dẫn dắt đội bóng, quản lý đội hình.
  - **REFEREE (Trọng tài):** Điều hành trận đấu.
  - **COMMENTATOR (Bình luận viên):** Bình luận trận đấu, truy cập livestream control.
  - **MEDIA (Đơn vị Truyền thông):** Đăng tải video, quản lý thư viện media.
  - **PHOTOGRAPHER (Nhiếp ảnh gia):** Tác nghiệp, đăng tải album ảnh.
  - **STADIUM (Sân bóng):** Cung cấp địa điểm tổ chức giải đấu.
  - **SPONSOR (Nhà tài trợ):** Tài trợ giải đấu, tiếp cận khán giả.
  - **COLLABORATOR (Cộng tác viên):** Hỗ trợ BTC (y tế, an ninh, hậu cần).
  - **TOURNAMENT_MANAGER (Quản lý giải đấu):** Quản lý giải đấu cụ thể, phân quyền cao hơn Organizer thường.

- **Tính năng nổi bật:**
  - Hệ thống chuyển nhượng cầu thủ với ngân sách đội
  - Bình chọn cầu thủ/đội bóng (tăng giá trị chuyển nhượng)
  - Quản lý ngân sách giải đấu (thu chi tự động)
  - Phòng điều khiển trận đấu real-time cho BTC
  - Hệ thống thông báo và theo dõi giải đấu
  - Tuyển dụng HLV và chuyển nhượng cầu thủ
  - Tích hợp thanh toán với QR code