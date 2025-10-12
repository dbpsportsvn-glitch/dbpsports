/**
 * Dữ liệu tỉnh thành và quận huyện Việt Nam
 */

const vietnamAddress = {
  "Hà Nội": [
    "Quận Ba Đình", "Quận Hoàn Kiếm", "Quận Tây Hồ", "Quận Long Biên",
    "Quận Cầu Giấy", "Quận Đống Đa", "Quận Hai Bà Trưng", "Quận Hoàng Mai",
    "Quận Thanh Xuân", "Quận Hà Đông", "Quận Nam Từ Liêm", "Quận Bắc Từ Liêm",
    "Huyện Ba Vì", "Huyện Chương Mỹ", "Huyện Đan Phượng", "Huyện Đông Anh",
    "Huyện Gia Lâm", "Huyện Hoài Đức", "Huyện Mê Linh", "Huyện Mỹ Đức",
    "Huyện Phú Xuyên", "Huyện Phúc Thọ", "Huyện Quốc Oai", "Huyện Sóc Sơn",
    "Huyện Thạch Thất", "Huyện Thanh Oai", "Huyện Thanh Trì", "Huyện Thường Tín",
    "Huyện Ứng Hòa", "Thị xã Sơn Tây"
  ],
  "TP. Hồ Chí Minh": [
    "Quận 1", "Quận 2", "Quận 3", "Quận 4", "Quận 5", "Quận 6", "Quận 7",
    "Quận 8", "Quận 9", "Quận 10", "Quận 11", "Quận 12", "Quận Thủ Đức",
    "Quận Gò Vấp", "Quận Bình Thạnh", "Quận Tân Bình", "Quận Tân Phú",
    "Quận Phú Nhuận", "Quận Bình Tân", "Huyện Củ Chi", "Huyện Hóc Môn",
    "Huyện Bình Chánh", "Huyện Nhà Bè", "Huyện Cần Giờ"
  ],
  "Đà Nẵng": [
    "Quận Hải Châu", "Quận Thanh Khê", "Quận Sơn Trà", "Quận Ngũ Hành Sơn",
    "Quận Liên Chiểu", "Quận Cẩm Lệ", "Huyện Hòa Vang", "Huyện Hoàng Sa"
  ],
  "Hải Phòng": [
    "Quận Hồng Bàng", "Quận Ngô Quyền", "Quận Lê Chân", "Quận Hải An",
    "Quận Kiến An", "Quận Đồ Sơn", "Quận Dương Kinh", "Huyện Thuỷ Nguyên",
    "Huyện An Dương", "Huyện An Lão", "Huyện Kiến Thuỵ", "Huyện Tiên Lãng",
    "Huyện Vĩnh Bảo", "Huyện Cát Hải", "Huyện Bạch Long Vĩ"
  ],
  "Cần Thơ": [
    "Quận Ninh Kiều", "Quận Ô Môn", "Quận Bình Thuỷ", "Quận Cái Răng",
    "Quận Thốt Nốt", "Huyện Vĩnh Thạnh", "Huyện Cờ Đỏ", "Huyện Phong Điền",
    "Huyện Thới Lai"
  ],
  "Bà Rịa - Vũng Tàu": [
    "Thành phố Vũng Tàu", "Thành phố Bà Rịa", "Huyện Châu Đức", "Huyện Xuyên Mộc",
    "Huyện Long Điền", "Huyện Đất Đỏ", "Huyện Tân Thành", "Huyện Côn Đảo"
  ],
  "Bắc Ninh": [
    "Thành phố Bắc Ninh", "Huyện Yên Phong", "Huyện Quế Võ", "Huyện Tiên Du",
    "Thị xã Từ Sơn", "Huyện Thuận Thành", "Huyện Gia Bình", "Huyện Lương Tài"
  ],
  "Bình Dương": [
    "Thành phố Thủ Dầu Một", "Thành phố Dĩ An", "Thành phố Thuận An",
    "Thị xã Bến Cát", "Huyện Dầu Tiếng", "Huyện Bắc Tân Uyên", "Huyện Phú Giáo"
  ],
  "Đồng Nai": [
    "Thành phố Biên Hòa", "Thành phố Long Khánh", "Huyện Trảng Bom",
    "Huyện Thống Nhất", "Huyện Cẩm Mỹ", "Huyện Long Thành", "Huyện Xuân Lộc",
    "Huyện Nhơn Trạch", "Huyện Vĩnh Cửu", "Huyện Định Quán", "Huyện Tân Phú"
  ],
  "Khánh Hòa": [
    "Thành phố Nha Trang", "Thành phố Cam Ranh", "Thị xã Ninh Hòa",
    "Huyện Khánh Vĩnh", "Huyện Diên Khánh", "Huyện Khánh Sơn", "Huyện Trường Sa",
    "Huyện Cam Lâm", "Huyện Vạn Ninh"
  ],
  // Thêm các tỉnh thành khác với dữ liệu tối thiểu
  "Điện Biên": ["Thành phố Điện Biên Phủ", "Thị xã Mường Lay", "Huyện Mường Chà", "Huyện Tủa Chùa", "Huyện Tuần Giáo", "Huyện Điện Biên", "Huyện Điện Biên Đông", "Huyện Mường Ảng", "Huyện Nậm Pồ", "Huyện Mường Nhé"],
  "Lai Châu": ["Thành phố Lai Châu", "Huyện Tam Đường", "Huyện Mường Tè", "Huyện Sìn Hồ", "Huyện Phong Thổ", "Huyện Than Uyên", "Huyện Tân Uyên", "Huyện Nậm Nhùn"],
  "Sơn La": ["Thành phố Sơn La", "Huyện Quỳnh Nhai", "Huyện Thuận Châu", "Huyện Mường La", "Huyện Bắc Yên", "Huyện Phù Yên", "Huyện Mộc Châu", "Huyện Yên Châu", "Huyện Mai Sơn", "Huyện Sông Mã", "Huyện Sốp Cộp", "Huyện Vân Hồ"],
  "Yên Bái": ["Thành phố Yên Bái", "Thị xã Nghĩa Lộ", "Huyện Lục Yên", "Huyện Văn Yên", "Huyện Mù Căng Chải", "Huyện Trấn Yên", "Huyện Trạm Tấu", "Huyện Văn Chấn", "Huyện Yên Bình"],
  "Lào Cai": ["Thành phố Lào Cai", "Thị xã Sa Pa", "Huyện Bát Xát", "Huyện Mường Khương", "Huyện Si Ma Cai", "Huyện Bắc Hà", "Huyện Bảo Thắng", "Huyện Bảo Yên", "Huyện Văn Bàn"],
  "Hà Giang": ["Thành phố Hà Giang", "Huyện Đồng Văn", "Huyện Mèo Vạc", "Huyện Yên Minh", "Huyện Quản Bạ", "Huyện Vị Xuyên", "Huyện Bắc Mê", "Huyện Hoàng Su Phì", "Huyện Xín Mần", "Huyện Bắc Quang", "Huyện Quang Bình"],
  "Cao Bằng": ["Thành phố Cao Bằng", "Huyện Bảo Lâm", "Huyện Bảo Lạc", "Huyện Thông Nông", "Huyện Hà Quảng", "Huyện Trà Lĩnh", "Huyện Trùng Khánh", "Huyện Hạ Lang", "Huyện Quảng Uyên", "Huyện Phục Hòa", "Huyện Hoà An", "Huyện Nguyên Bình", "Huyện Thạch An"],
  "Bắc Kạn": ["Thành phố Bắc Kạn", "Huyện Pác Nặm", "Huyện Ba Bể", "Huyện Ngân Sơn", "Huyện Bạch Thông", "Huyện Chợ Đồn", "Huyện Chợ Mới", "Huyện Na Rì"],
  "Tuyên Quang": ["Thành phố Tuyên Quang", "Huyện Lâm Bình", "Huyện Nà Hang", "Huyện Chiêm Hóa", "Huyện Hàm Yên", "Huyện Yên Sơn", "Huyện Sơn Dương"],
  "Thái Nguyên": ["Thành phố Thái Nguyên", "Thành phố Sông Công", "Huyện Định Hóa", "Huyện Phú Lương", "Huyện Đồng Hỷ", "Huyện Võ Nhai", "Huyện Đại Từ", "Huyện Phổ Yên", "Huyện Phú Bình"],
  "Lạng Sơn": ["Thành phố Lạng Sơn", "Huyện Tràng Định", "Huyện Bình Gia", "Huyện Văn Lãng", "Huyện Cao Lộc", "Huyện Văn Quan", "Huyện Bắc Sơn", "Huyện Hữu Lũng", "Huyện Chi Lăng", "Huyện Lộc Bình", "Huyện Đình Lập"],
  "Quảng Ninh": ["Thành phố Hạ Long", "Thành phố Móng Cái", "Thành phố Cẩm Phả", "Thành phố Uông Bí", "Huyện Bình Liêu", "Huyện Tiên Yên", "Huyện Đầm Hà", "Huyện Hải Hà", "Huyện Ba Chẽ", "Huyện Vân Đồn", "Huyện Hoành Bồ", "Thị xã Đông Triều", "Thị xã Quảng Yên", "Huyện Cô Tô"],
  "Bắc Giang": ["Thành phố Bắc Giang", "Huyện Yên Thế", "Huyện Tân Yên", "Huyện Lạng Giang", "Huyện Lục Nam", "Huyện Lục Ngạn", "Huyện Sơn Động", "Huyện Yên Dũng", "Huyện Việt Yên", "Huyện Hiệp Hòa"],
  "Phú Thọ": ["Thành phố Việt Trì", "Thị xã Phú Thọ", "Huyện Đoan Hùng", "Huyện Hạ Hoà", "Huyện Thanh Ba", "Huyện Phù Ninh", "Huyện Yên Lập", "Huyện Cẩm Khê", "Huyện Tam Nông", "Huyện Lâm Thao", "Huyện Thanh Sơn", "Huyện Thanh Thuỷ", "Huyện Tân Sơn"],
  "Vĩnh Phúc": ["Thành phố Vĩnh Yên", "Thành phố Phúc Yên", "Huyện Lập Thạch", "Huyện Tam Dương", "Huyện Tam Đảo", "Huyện Bình Xuyên", "Huyện Yên Lạc", "Huyện Vĩnh Tường", "Huyện Sông Lô"],
  "Hà Nam": ["Thành phố Phủ Lý", "Thị xã Duy Tiên", "Huyện Kim Bảng", "Huyện Thanh Liêm", "Huyện Bình Lục", "Huyện Lý Nhân"],
  "Hải Dương": ["Thành phố Hải Dương", "Thành phố Chí Linh", "Huyện Nam Sách", "Huyện Kinh Môn", "Huyện Kim Thành", "Huyện Thanh Hà", "Huyện Cẩm Giàng", "Huyện Bình Giang", "Huyện Gia Lộc", "Huyện Tứ Kỳ", "Huyện Ninh Giang", "Huyện Thanh Miện"],
  "Hưng Yên": ["Thành phố Hưng Yên", "Huyện Văn Lâm", "Huyện Văn Giang", "Huyện Yên Mỹ", "Huyện Mỹ Hào", "Huyện Ân Thi", "Huyện Khoái Châu", "Huyện Kim Động", "Huyện Tiên Lữ", "Huyện Phù Cừ"],
  "Thái Bình": ["Thành phố Thái Bình", "Huyện Quỳnh Phụ", "Huyện Hưng Hà", "Huyện Đông Hưng", "Huyện Thái Thụy", "Huyện Tiền Hải", "Huyện Kiến Xương", "Huyện Vũ Thư"],
  "Nam Định": ["Thành phố Nam Định", "Huyện Mỹ Lộc", "Huyện Vụ Bản", "Huyện Ý Yên", "Huyện Nghĩa Hưng", "Huyện Nam Trực", "Huyện Trực Ninh", "Huyện Xuân Trường", "Huyện Giao Thủy", "Huyện Hải Hậu"],
  "Ninh Bình": ["Thành phố Ninh Bình", "Thành phố Tam Điệp", "Huyện Nho Quan", "Huyện Gia Viễn", "Huyện Hoa Lư", "Huyện Yên Khánh", "Huyện Kim Sơn", "Huyện Yên Mô"],
  "Thanh Hóa": ["Thành phố Thanh Hóa", "Thị xã Bỉm Sơn", "Thị xã Sầm Sơn", "Huyện Mường Lát", "Huyện Quan Hóa", "Huyện Bá Thước", "Huyện Quan Sơn", "Huyện Lang Chánh", "Huyện Ngọc Lặc", "Huyện Cẩm Thủy", "Huyện Thạch Thành", "Huyện Hà Trung", "Huyện Vĩnh Lộc", "Huyện Yên Định", "Huyện Thọ Xuân", "Huyện Thường Xuân", "Huyện Triệu Sơn", "Huyện Thiệu Hóa", "Huyện Hoằng Hóa", "Huyện Hậu Lộc", "Huyện Nga Sơn", "Huyện Như Xuân", "Huyện Như Thanh", "Huyện Nông Cống", "Huyện Đông Sơn", "Huyện Quảng Xương", "Thị xã Nghi Sơn", "Huyện Tĩnh Gia"],
  "Nghệ An": ["Thành phố Vinh", "Thị xã Cửa Lò", "Thị xã Thái Hoà", "Huyện Quế Phong", "Huyện Quỳ Châu", "Huyện Kỳ Sơn", "Huyện Tương Dương", "Huyện Nghĩa Đàn", "Huyện Quỳ Hợp", "Huyện Quỳnh Lưu", "Huyện Con Cuông", "Huyện Tân Kỳ", "Huyện Anh Sơn", "Huyện Diễn Châu", "Huyện Yên Thành", "Huyện Đô Lương", "Huyện Thanh Chương", "Huyện Nghi Lộc", "Huyện Nam Đàn", "Huyện Hưng Nguyên", "Thị xã Hoàng Mai"],
  "Hà Tĩnh": ["Thành phố Hà Tĩnh", "Thị xã Hồng Lĩnh", "Huyện Hương Sơn", "Huyện Đức Thọ", "Huyện Vũ Quang", "Huyện Nghi Xuân", "Huyện Can Lộc", "Huyện Hương Khê", "Huyện Thạch Hà", "Huyện Cẩm Xuyên", "Huyện Kỳ Anh", "Huyện Lộc Hà", "Thị xã Kỳ Anh"],
  "Quảng Bình": ["Thành phố Đồng Hới", "Huyện Minh Hóa", "Huyện Tuyên Hóa", "Huyện Quảng Trạch", "Huyện Bố Trạch", "Huyện Quảng Ninh", "Huyện Lệ Thủy", "Thị xã Ba Đồn"],
  "Quảng Trị": ["Thành phố Đông Hà", "Thị xã Quảng Trị", "Huyện Vĩnh Linh", "Huyện Hướng Hóa", "Huyện Gio Linh", "Huyện Đa Krông", "Huyện Cam Lộ", "Huyện Triệu Phong", "Huyện Hải Lăng", "Huyện Cồn Cỏ"],
  "Thừa Thiên Huế": ["Thành phố Huế", "Huyện Phong Điền", "Huyện Quảng Điền", "Huyện Phú Vang", "Thị xã Hương Thủy", "Thị xã Hương Trà", "Huyện A Lưới", "Huyện Phú Lộc", "Huyện Nam Đông"],
  "Quảng Nam": ["Thành phố Tam Kỳ", "Thành phố Hội An", "Huyện Tây Giang", "Huyện Đông Giang", "Huyện Đại Lộc", "Thị xã Điện Bàn", "Huyện Duy Xuyên", "Huyện Quế Sơn", "Huyện Nam Giang", "Huyện Phước Sơn", "Huyện Hiệp Đức", "Huyện Thăng Bình", "Huyện Tiên Phước", "Huyện Bắc Trà My", "Huyện Nam Trà My", "Huyện Núi Thành", "Huyện Phú Ninh", "Huyện Nông Sơn"],
  "Quảng Ngãi": ["Thành phố Quảng Ngãi", "Huyện Bình Sơn", "Huyện Trà Bồng", "Huyện Tây Trà", "Huyện Sơn Tịnh", "Huyện Tư Nghĩa", "Huyện Sơn Hà", "Huyện Sơn Tây", "Huyện Minh Long", "Huyện Nghĩa Hành", "Huyện Mộ Đức", "Huyện Đức Phổ", "Huyện Ba Tơ", "Huyện Lý Sơn"],
  "Bình Định": ["Thành phố Quy Nhơn", "Huyện An Lão", "Huyện Hoài Nhơn", "Huyện Hoài Ân", "Huyện Phù Mỹ", "Huyện Vĩnh Thạnh", "Huyện Tây Sơn", "Huyện Phù Cát", "Thị xã An Nhơn", "Huyện Tuy Phước", "Huyện Vân Canh"],
  "Phú Yên": ["Thành phố Tuy Hòa", "Thị xã Sông Cầu", "Huyện Đồng Xuân", "Huyện Tuy An", "Huyện Sơn Hòa", "Huyện Sông Hinh", "Huyện Tây Hòa", "Huyện Phú Hòa", "Thị xã Đông Hòa"],
  "Ninh Thuận": ["Thành phố Phan Rang-Tháp Chàm", "Huyện Bác Ái", "Huyện Ninh Sơn", "Huyện Ninh Hải", "Huyện Ninh Phước", "Huyện Thuận Bắc", "Huyện Thuận Nam"],
  "Bình Thuận": ["Thành phố Phan Thiết", "Thị xã La Gí", "Huyện Tuy Phong", "Huyện Bắc Bình", "Huyện Hàm Thuận Bắc", "Huyện Hàm Thuận Nam", "Huyện Tánh Linh", "Huyện Đức Linh", "Huyện Hàm Tân", "Huyện Phú Quý"],
  "Kon Tum": ["Thành phố Kon Tum", "Huyện Đắk Glei", "Huyện Ngọc Hồi", "Huyện Đắk Tô", "Huyện Kon Plông", "Huyện Kon Rẫy", "Huyện Đắk Hà", "Huyện Sa Thầy", "Huyện Tu Mơ Rông", "Huyện Ia H' Drai"],
  "Gia Lai": ["Thành phố Pleiku", "Thị xã An Khê", "Thị xã Ayun Pa", "Huyện KBang", "Huyện Đăk Đoa", "Huyện Chư Păh", "Huyện Ia Grai", "Huyện Mang Yang", "Huyện Kông Chro", "Huyện Đức Cơ", "Huyện Chư Prông", "Huyện Chư Sê", "Huyện Đăk Pơ", "Huyện Ia Pa", "Huyện Krông Pa", "Huyện Phú Thiện", "Huyện Chư Pưh"],
  "Đắk Lắk": ["Thành phố Buôn Ma Thuột", "Thị xã Buôn Hồ", "Huyện Ea H'leo", "Huyện Ea Súp", "Huyện Buôn Đôn", "Huyện Cư M'gar", "Huyện Krông Búk", "Huyện Krông Năng", "Huyện Ea Kar", "Huyện M'Đrắk", "Huyện Krông Bông", "Huyện Krông Pắc", "Huyện Krông A Na", "Huyện Lắk", "Huyện Cư Kuin"],
  "Đắk Nông": ["Thành phố Gia Nghĩa", "Huyện Đăk Glong", "Huyện Cư Jút", "Huyện Đắk Mil", "Huyện Krông Nô", "Huyện Đắk Song", "Huyện Đắk R'Lấp", "Huyện Tuy Đức"],
  "Lâm Đồng": ["Thành phố Đà Lạt", "Thành phố Bảo Lộc", "Huyện Đam Rông", "Huyện Lạc Dương", "Huyện Lâm Hà", "Huyện Đơn Dương", "Huyện Đức Trọng", "Huyện Di Linh", "Huyện Bảo Lâm", "Huyện Đạ Huoai", "Huyện Đạ Tẻh", "Huyện Cát Tiên"],
  "Bình Phước": ["Thị xã Phước Long", "Thành phố Đồng Xoài", "Thị xã Bình Long", "Huyện Bù Gia Mập", "Huyện Lộc Ninh", "Huyện Bù Đốp", "Huyện Hớn Quản", "Huyện Đồng Phú", "Huyện Bù Đăng", "Thị xã Chơn Thành", "Huyện Phú Riềng"],
  "Tây Ninh": ["Thành phố Tây Ninh", "Huyện Tân Biên", "Huyện Tân Châu", "Huyện Dương Minh Châu", "Huyện Châu Thành", "Thị xã Hòa Thành", "Huyện Gò Dầu", "Huyện Bến Cầu", "Thị xã Trảng Bàng"],
  "Long An": ["Thành phố Tân An", "Thị xã Kiến Tường", "Huyện Tân Hưng", "Huyện Vĩnh Hưng", "Huyện Mộc Hóa", "Huyện Tân Thạnh", "Huyện Thạnh Hóa", "Huyện Đức Huệ", "Huyện Đức Hòa", "Huyện Bến Lức", "Huyện Thủ Thừa", "Huyện Tân Trụ", "Huyện Cần Đước", "Huyện Cần Giuộc", "Huyện Châu Thành"],
  "Tiền Giang": ["Thành phố Mỹ Tho", "Thị xã Gò Công", "Thị xã Cai Lậy", "Huyện Tân Phước", "Huyện Cái Bè", "Huyện Cai Lậy", "Huyện Châu Thành", "Huyện Chợ Gạo", "Huyện Gò Công Tây", "Huyện Gò Công Đông", "Huyện Tân Phú Đông"],
  "Bến Tre": ["Thành phố Bến Tre", "Huyện Châu Thành", "Huyện Chợ Lách", "Huyện Mỏ Cày Nam", "Huyện Giồng Trôm", "Huyện Bình Đại", "Huyện Ba Tri", "Huyện Thạnh Phú", "Huyện Mỏ Cày Bắc"],
  "Trà Vinh": ["Thành phố Trà Vinh", "Huyện Càng Long", "Huyện Cầu Kè", "Huyện Tiểu Cần", "Huyện Châu Thành", "Huyện Cầu Ngang", "Huyện Trà Cú", "Huyện Duyên Hải", "Thị xã Duyên Hải"],
  "Vĩnh Long": ["Thành phố Vĩnh Long", "Huyện Long Hồ", "Huyện Mang Thít", "Huyện Vũng Liêm", "Huyện Tam Bình", "Thị xã Bình Minh", "Huyện Trà Ôn", "Huyện Bình Tân"],
  "Đồng Tháp": ["Thành phố Cao Lãnh", "Thành phố Sa Đéc", "Thị xã Hồng Ngự", "Huyện Tân Hồng", "Huyện Hồng Ngự", "Huyện Tam Nông", "Huyện Tháp Mười", "Huyện Cao Lãnh", "Huyện Thanh Bình", "Huyện Lấp Vò", "Huyện Lai Vung", "Huyện Châu Thành"],
  "An Giang": ["Thành phố Long Xuyên", "Thành phố Châu Đốc", "Huyện An Phú", "Thị xã Tân Châu", "Huyện Phú Tân", "Huyện Châu Phú", "Huyện Tịnh Biên", "Huyện Tri Tôn", "Huyện Châu Thành", "Huyện Chợ Mới", "Huyện Thoại Sơn"],
  "Kiên Giang": ["Thành phố Rạch Giá", "Thành phố Hà Tiên", "Huyện Kiên Lương", "Huyện Hòn Đất", "Huyện Tân Hiệp", "Huyện Châu Thành", "Huyện Giồng Riềng", "Huyện Gò Quao", "Huyện An Biên", "Huyện An Minh", "Huyện Vĩnh Thuận", "Huyện Phú Quốc", "Huyện Kiên Hải", "Huyện U Minh Thượng", "Huyện Giang Thành"],
  "Cà Mau": ["Thành phố Cà Mau", "Huyện U Minh", "Huyện Thới Bình", "Huyện Trần Văn Thời", "Huyện Cái Nước", "Huyện Đầm Dơi", "Huyện Năm Căn", "Huyện Phú Tân", "Huyện Ngọc Hiển"],
  "Bạc Liêu": ["Thành phố Bạc Liêu", "Huyện Hồng Dân", "Huyện Phước Long", "Huyện Vĩnh Lợi", "Thị xã Giá Rai", "Huyện Đông Hải", "Huyện Hoà Bình"],
  "Sóc Trăng": ["Thành phố Sóc Trăng", "Huyện Châu Thành", "Huyện Kế Sách", "Huyện Mỹ Tú", "Huyện Cù Lao Dung", "Huyện Long Phú", "Huyện Mỹ Xuyên", "Thị xã Ngã Năm", "Huyện Thạnh Trị", "Thị xã Vĩnh Châu", "Huyện Trần Đề"],
  "Hậu Giang": ["Thành phố Vị Thanh", "Thành phố Ngã Bảy", "Huyện Châu Thành A", "Huyện Châu Thành", "Huyện Phụng Hiệp", "Huyện Vị Thuỷ", "Huyện Long Mỹ", "Thị xã Long Mỹ"]
};

/**
 * Populate district dropdown based on selected city
 */
function populateDistricts(cityName, districtSelectId = 'shipping_district') {
  const districtSelect = document.getElementById(districtSelectId) || document.querySelector(`select[name="${districtSelectId}"]`);
  
  if (!districtSelect) {
    console.warn(`District select with id/name "${districtSelectId}" not found`);
    return;
  }
  
  // Clear existing options
  districtSelect.innerHTML = '<option value="">Chọn quận/huyện</option>';
  
  // Get districts for selected city
  const districts = vietnamAddress[cityName];
  
  if (districts && districts.length > 0) {
    districts.forEach(district => {
      const option = document.createElement('option');
      option.value = district;
      option.textContent = district;
      districtSelect.appendChild(option);
    });
    
    // Enable district select
    districtSelect.disabled = false;
  } else {
    // No districts found, disable select
    districtSelect.disabled = true;
  }
}

/**
 * Initialize cascading dropdown
 */
function initAddressCascade(citySelectId = 'shipping_city', districtSelectId = 'shipping_district') {
  const citySelect = document.getElementById(citySelectId) || document.querySelector(`select[name="${citySelectId}"]`);
  
  if (!citySelect) {
    console.warn(`City select with id/name "${citySelectId}" not found`);
    return;
  }
  
  // Listen to city change
  citySelect.addEventListener('change', function() {
    const selectedCity = this.value;
    if (selectedCity) {
      populateDistricts(selectedCity, districtSelectId);
    } else {
      // Clear district select if no city selected
      const districtSelect = document.getElementById(districtSelectId) || document.querySelector(`select[name="${districtSelectId}"]`);
      if (districtSelect) {
        districtSelect.innerHTML = '<option value="">Chọn quận/huyện</option>';
        districtSelect.disabled = true;
      }
    }
  });
  
  // If city is already selected (e.g., from saved data), populate districts
  if (citySelect.value) {
    populateDistricts(citySelect.value, districtSelectId);
  }
}

