# 🌟 Hệ Thống Đánh Giá HLV & Sân Bóng - Hoàn Thành

## ✅ Tính Năng Mới

### Hệ thống đánh giá và review cho Huấn luyện viên và Sân bóng, tương tự như hệ thống bình chọn của nhà tài trợ.

---

## 🎯 Mục Tiêu

### Tăng độ uy tín và tin tưởng:
- ✅ **HLV:** Hiển thị lịch sử thành tích và đánh giá từ các đội bóng
- ✅ **Sân bóng:** Hiển thị chất lượng dịch vụ từ các đội và BTC
- ✅ **Người dùng:** Có thể đánh giá và xem reviews để quyết định hợp tác

---

## 🏗️ Kiến Trúc Hệ Thống

### 1. **Models**

#### CoachReview Model:
```python
class CoachReview(models.Model):
    coach_profile = models.ForeignKey(CoachProfile, ...)
    reviewer = models.ForeignKey(User, ...)
    team = models.ForeignKey(Team, ...)  # Đội đã huấn luyện
    tournament = models.ForeignKey(Tournament, ...)  # Giải đấu liên quan
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} sao") for i in range(1, 6)])
    comment = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=True)  # HLV có thể ẩn/hiện
    created_at = models.DateTimeField(auto_now_add=True)
```

#### StadiumReview Model:
```python
class StadiumReview(models.Model):
    stadium_profile = models.ForeignKey(StadiumProfile, ...)
    reviewer = models.ForeignKey(User, ...)
    team = models.ForeignKey(Team, ...)  # Đội đã sử dụng sân
    tournament = models.ForeignKey(Tournament, ...)  # Giải đấu tổ chức
    rating = models.PositiveSmallIntegerField(choices=[(i, f"{i} sao") for i in range(1, 6)])
    comment = models.TextField(max_length=1000)
    is_approved = models.BooleanField(default=True)  # Sân có thể ẩn/hiện
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. **Forms**

#### CoachReviewForm:
```python
class CoachReviewForm(forms.ModelForm):
    fields = ['rating', 'comment', 'team', 'tournament']
    widgets = {
        'rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
        'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': '...'}),
    }
```

#### StadiumReviewForm:
```python
class StadiumReviewForm(forms.ModelForm):
    fields = ['rating', 'comment', 'team', 'tournament']
    widgets = {
        'rating': forms.RadioSelect(attrs={'class': 'star-rating'}),
        'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': '...'}),
    }
```

### 3. **Views**

#### Profile Detail Views:
```python
def coach_profile_detail(request, pk):
    # Lấy reviews và tính rating trung bình
    reviews = CoachReview.objects.filter(
        coach_profile=coach_profile,
        is_approved=True
    ).select_related('reviewer', 'team', 'tournament')
    
    avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
    avg_rating = round(avg_rating, 1) if avg_rating else 0
    
    # Kiểm tra user đã đánh giá chưa
    user_reviewed = CoachReview.objects.filter(
        coach_profile=coach_profile,
        reviewer=request.user
    ).exists()
```

#### Create Review Views:
```python
def create_coach_review(request, coach_pk):
    # Kiểm tra đã đánh giá chưa
    existing_review = CoachReview.objects.filter(
        coach_profile=coach_profile,
        reviewer=request.user
    ).first()
    
    if existing_review:
        messages.warning(request, "Bạn đã đánh giá HLV này rồi!")
        return redirect('coach_profile_detail', coach_pk=coach_pk)
```

---

## 🎨 UI/UX Features

### 1. **Profile Detail Pages**

#### Coach Profile:
```
┌─────────────────────────────────────┐
│ 👤 HLV Name                    ⭐4.5│
│ 📍 Region                       5 sao│
├─────────────────────────────────────┤
│ 📝 Giới thiệu                     │
│ 🏆 Kinh nghiệm & Thành tích        │
│ ⭐ Đánh giá (4.5/5)              │
│   ├── Review 1: ⭐⭐⭐⭐⭐        │
│   ├── Review 2: ⭐⭐⭐⭐          │
│   └── [Đánh giá HLV này]          │
└─────────────────────────────────────┘
```

#### Stadium Profile:
```
┌─────────────────────────────────────┐
│ 🏟️ Stadium Name               ⭐4.2│
│ 📍 Region                       4 sao│
├─────────────────────────────────────┤
│ 📝 Mô tả                          │
│ 🏟️ Thông tin sân                  │
│ ⭐ Đánh giá (4.2/5)              │
│   ├── Review 1: ⭐⭐⭐⭐⭐        │
│   ├── Review 2: ⭐⭐⭐⭐          │
│   └── [Đánh giá sân bóng này]      │
└─────────────────────────────────────┘
```

### 2. **Review Form**

#### Star Rating Input:
```html
<div class="star-rating-input">
    <div class="form-check form-check-inline">
        <input type="radio" name="rating" value="1" id="id_rating_1">
        <label for="id_rating_1">⭐</label>
    </div>
    <!-- ... 2,3,4,5 stars ... -->
</div>
```

#### Form Fields:
- ⭐ **Rating:** 1-5 sao (Radio buttons)
- 📝 **Comment:** Textarea với placeholder
- ⚽ **Team:** Dropdown (chỉ đội của user)
- 🏆 **Tournament:** Dropdown (chỉ giải của user)

---

## 🔧 Technical Implementation

### 1. **Database Schema**

#### CoachReview Table:
```sql
CREATE TABLE users_coachreview (
    id INTEGER PRIMARY KEY,
    coach_profile_id INTEGER REFERENCES users_coachprofile(id),
    reviewer_id INTEGER REFERENCES auth_user(id),
    team_id INTEGER REFERENCES tournaments_team(id),
    tournament_id INTEGER REFERENCES tournaments_tournament(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(coach_profile_id, reviewer_id, team_id)
);
```

#### StadiumReview Table:
```sql
CREATE TABLE users_stadiumreview (
    id INTEGER PRIMARY KEY,
    stadium_profile_id INTEGER REFERENCES users_stadiumprofile(id),
    reviewer_id INTEGER REFERENCES auth_user(id),
    team_id INTEGER REFERENCES tournaments_team(id),
    tournament_id INTEGER REFERENCES tournaments_tournament(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stadium_profile_id, reviewer_id, team_id)
);
```

### 2. **URL Patterns**

```python
# users/urls.py
path('coach/<int:coach_pk>/review/', views.create_coach_review, name='create_coach_review'),
path('stadium/<int:stadium_pk>/review/', views.create_stadium_review, name='create_stadium_review'),
path('stadium/<int:pk>/', views.stadium_profile_detail, name='stadium_profile_detail'),
```

### 3. **Admin Interface**

#### CoachReviewAdmin:
```python
@admin.register(CoachReview)
class CoachReviewAdmin(admin.ModelAdmin):
    list_display = ('coach_profile', 'reviewer', 'rating', 'team', 'tournament', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('coach_profile__full_name', 'reviewer__username', 'comment')
    list_editable = ('is_approved',)
```

---

## 🧪 Test Cases

### Test 1: Create Coach Review
```bash
# 1. Login với user có team
# 2. Vào coach profile: /users/coach/1/
# 3. Click "Đánh giá HLV này"
# 4. Fill form: Rating=5, Comment="Tuyệt vời", Team=MyTeam
# 5. Submit
# ✅ Review được tạo và hiển thị trên profile
# ✅ Rating trung bình được cập nhật
```

### Test 2: Create Stadium Review
```bash
# 1. Login với user có team
# 2. Vào stadium profile: /users/stadium/1/
# 3. Click "Đánh giá sân bóng này"
# 4. Fill form: Rating=4, Comment="Sân đẹp", Team=MyTeam
# 5. Submit
# ✅ Review được tạo và hiển thị trên profile
# ✅ Rating trung bình được cập nhật
```

### Test 3: Duplicate Review Prevention
```bash
# 1. User đã đánh giá HLV
# 2. Vào lại coach profile
# 3. Click "Đánh giá HLV này"
# ✅ Redirect về profile với message "Bạn đã đánh giá HLV này rồi!"
# ✅ Không hiển thị nút đánh giá nữa
```

### Test 4: Review Approval System
```bash
# 1. Admin vào Django Admin
# 2. Vào CoachReview hoặc StadiumReview
# 3. Uncheck "is_approved" cho một review
# 4. Vào profile page
# ✅ Review không hiển thị trên profile
# ✅ Rating trung bình được tính lại
```

---

## 📊 Business Logic

### 1. **Review Rules**

#### Who Can Review:
- ✅ **Coach Reviews:** Team captains (đội đã thuê HLV)
- ✅ **Stadium Reviews:** Team captains hoặc BTC (đã sử dụng sân)
- ❌ **Self Review:** Không thể đánh giá chính mình
- ❌ **Duplicate Review:** Mỗi user chỉ đánh giá 1 lần cho mỗi HLV/sân

#### Review Content:
- ⭐ **Rating:** Bắt buộc (1-5 sao)
- 📝 **Comment:** Tùy chọn (max 1000 chars)
- ⚽ **Team:** Tùy chọn (để context)
- 🏆 **Tournament:** Tùy chọn (để context)

### 2. **Rating Calculation**

#### Average Rating:
```python
avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
avg_rating = round(avg_rating, 1) if avg_rating else 0
```

#### Display Logic:
- **No Reviews:** "Chưa có đánh giá nào"
- **With Reviews:** "4.5/5" với stars display
- **Star Display:** Filled stars cho rating, empty stars cho remaining

### 3. **Approval System**

#### Review Visibility:
- ✅ **Default:** `is_approved = True` (hiển thị ngay)
- 🔒 **Admin Control:** Admin có thể ẩn reviews không phù hợp
- 👤 **Profile Owner:** Có thể yêu cầu admin ẩn reviews

---

## 🎨 Visual Design

### 1. **Star Rating Display**

#### Profile Header:
```html
<div class="d-flex align-items-center">
    <span class="badge bg-warning text-dark me-2">4.5/5</span>
    <div class="star-rating">
        <i class="bi bi-star-fill text-warning"></i>  <!-- Filled -->
        <i class="bi bi-star-fill text-warning"></i>  <!-- Filled -->
        <i class="bi bi-star-fill text-warning"></i>  <!-- Filled -->
        <i class="bi bi-star-fill text-warning"></i>  <!-- Filled -->
        <i class="bi bi-star text-muted"></i>         <!-- Empty -->
    </div>
</div>
```

#### Review Cards:
```html
<div class="border rounded p-3">
    <div class="d-flex justify-content-between align-items-start mb-2">
        <div>
            <strong>Nguyễn Văn A</strong>
            <small class="text-muted">- Đội ABC</small>
        </div>
        <div class="star-rating">
            <i class="bi bi-star-fill text-warning"></i>
            <i class="bi bi-star-fill text-warning"></i>
            <i class="bi bi-star-fill text-warning"></i>
            <i class="bi bi-star-fill text-warning"></i>
            <i class="bi bi-star-fill text-warning"></i>
        </div>
    </div>
    <p class="mb-0 small">HLV rất chuyên nghiệp và nhiệt tình...</p>
    <small class="text-muted">15/10/2025</small>
</div>
```

### 2. **Form Styling**

#### Star Rating Input:
```css
.star-rating-input .form-check-input {
    display: none;
}

.star-rating-input .form-check-label {
    cursor: pointer;
    font-size: 1.5rem;
    color: #ddd;
    transition: color 0.2s;
}

.star-rating-input .form-check-input:checked + .form-check-label,
.star-rating-input .form-check-label:hover {
    color: #ffc107;
}
```

---

## 🚀 Kết Quả

### Trước:
- ❌ Không có hệ thống đánh giá HLV/sân bóng
- ❌ Khó đánh giá chất lượng dịch vụ
- ❌ Thiếu minh bạch trong hợp tác

### Sau:
- ✅ **Hệ thống đánh giá hoàn chỉnh** cho HLV và sân bóng
- ✅ **Rating trung bình** hiển thị trên profile
- ✅ **Review cards** với thông tin chi tiết
- ✅ **Form đánh giá** user-friendly với star rating
- ✅ **Admin quản lý** reviews và approval system
- ✅ **Duplicate prevention** và business rules
- ✅ **Responsive design** cho mọi device

---

## 🔄 Integration với Hệ Thống Hiện Tại

### 1. **Tương Thích với Sponsor System**
- ✅ **Same Rating Logic:** 1-5 sao như Testimonial
- ✅ **Same Approval System:** `is_approved` field
- ✅ **Same UI Pattern:** Star display và review cards

### 2. **Profile Integration**
- ✅ **Coach Profile:** Hiển thị reviews trong profile detail
- ✅ **Stadium Profile:** Hiển thị reviews trong profile detail
- ✅ **Public Access:** Ai cũng có thể xem reviews

### 3. **User Experience**
- ✅ **Easy Access:** Nút "Đánh giá" ngay trên profile
- ✅ **Context Aware:** Form chỉ hiển thị teams/tournaments của user
- ✅ **Feedback:** Messages khi tạo/sửa reviews

---

**Hoàn thành! Hệ thống đánh giá HLV và sân bóng đã sẵn sàng để tăng độ uy tín và tin tưởng trong cộng đồng!** ✨

**Test ngay:**
1. Tạo coach/stadium profile
2. Vào profile detail để xem reviews section
3. Click "Đánh giá" để test form
4. Kiểm tra admin interface để quản lý reviews
