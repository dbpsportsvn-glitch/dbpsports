# ⚡ QUICK START - Vai Trò HLV & Sân Bóng

## 🚀 Chạy Ngay (3 Bước)

### 1. Migrate
```bash
cd backend
venv\Scripts\python.exe manage.py migrate
```

### 2. Tạo Dữ Liệu Mẫu (Admin)
```bash
# Mở browser: http://localhost:8000/admin/

# Tạo CoachProfile:
Admin → Users → Hồ sơ Huấn luyện viên → Thêm mới
- Chọn user
- Điền thông tin
- ☑️ Đánh dấu "Đang tìm đội"

# Tạo StadiumProfile:
Admin → Users → Hồ sơ Sân bóng → Thêm mới
```

### 3. Test URLs

#### Đội Trưởng Chiêu Mộ HLV:
```
http://localhost:8000/team/1/recruit-coach/
```

#### HLV Dashboard:
```
http://localhost:8000/coach/dashboard/
```

#### Sân Bóng Dashboard:
```
http://localhost:8000/stadium/dashboard/
```

---

## 📍 Lối Vào Chức Năng

### Đội Trưởng → Tìm HLV
1. Vào `/team/<team_id>/`
2. Click "Chiêu mộ HLV" (cần thêm button vào template)
3. Hoặc trực tiếp: `/team/<team_id>/recruit-coach/`

### HLV → Quản Lý Lời Mời
1. Tạo hồ sơ: `/coach/create/`
2. Dashboard: `/coach/dashboard/`
3. Accept lời mời: Click button trong dashboard

### Sân Bóng → Đăng Tin
1. Tạo hồ sơ: `/stadium/create/`
2. Dashboard: `/stadium/dashboard/`
3. Đăng tin: `/stadium/job/create/`

---

## 📝 Templates Cần Thêm

### Vào team_detail.html:
```html
<!-- Thêm section này -->
{% if team.coach %}
  <div class="card">
    <div class="card-header">HLV: {{ team.coach.full_name }}</div>
    {% if user == team.captain %}
      <button onclick="removeCoach()">Loại bỏ</button>
    {% endif %}
  </div>
{% else %}
  {% if user == team.captain %}
    <a href="{% url 'recruit_coach_list' team.pk %}">
      Tìm HLV
    </a>
  {% endif %}
{% endif %}
```

### Code Templates Đầy Đủ:
👉 Xem file **`HUONG_DAN_SU_DUNG.md`** - Có code HTML/JS hoàn chỉnh!

---

## 🔑 Quick Access

| Vai Trò | URL | Mô Tả |
|---------|-----|-------|
| Đội Trưởng | `/team/<id>/recruit-coach/` | Tìm HLV |
| HLV | `/coach/dashboard/` | Dashboard |
| HLV | `/coach/create/` | Tạo hồ sơ |
| Sân Bóng | `/stadium/dashboard/` | Dashboard |
| Sân Bóng | `/stadium/create/` | Tạo hồ sơ |

---

## 📚 Docs

- **TONG_KET_HOAN_THANH.md** → Tổng quan đầy đủ
- **HUONG_DAN_SU_DUNG.md** → Code templates ⭐
- **CAU_HINH_CUOI_CUNG.md** → Routes & configs

---

**✅ Backend sẵn sàng 100%!**

