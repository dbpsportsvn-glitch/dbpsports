# File: backend/tournaments/models.py

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Q, Sum
from django.core.exceptions import ValidationError
from django.conf import settings
from organizations.models import Organization
from django.utils import timezone
from colorfield.fields import ColorField

from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from datetime import timedelta
import os

MAX_STARTERS = 11

class Tournament(models.Model):
    class Status(models.TextChoices):
        REGISTRATION_OPEN = 'REGISTRATION_OPEN', 'Đang mở đăng ký'
        IN_PROGRESS = 'IN_PROGRESS', 'Đang diễn ra'
        FINISHED = 'FINISHED', 'Đã kết thúc'

    class Format(models.TextChoices):
        CUP = 'CUP', 'Đá Cúp (loại trực tiếp/vòng bảng + knock-out)'
        LEAGUE = 'LEAGUE', 'Đá League (vòng tròn tính điểm)'

    class Region(models.TextChoices):
        MIEN_BAC = 'MIEN_BAC', 'Miền Bắc'
        MIEN_TRUNG = 'MIEN_TRUNG', 'Miền Trung'
        MIEN_NAM = 'MIEN_NAM', 'Miền Nam'
        KHAC = 'KHAC', 'Khác'

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        related_name='tournaments',
        verbose_name="Đơn vị tổ chức",
        null=True, blank=True
    )
    name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REGISTRATION_OPEN)
    format = models.CharField("Thể thức", max_length=10, choices=Format.choices, default=Format.CUP, help_text="Chọn thể thức thi đấu của giải")
    image = models.ImageField(upload_to='tournament_banners/', null=True, blank=True)
    region = models.CharField("Khu vực", max_length=20, choices=Region.choices, default=Region.KHAC)
    location_detail = models.CharField("Tỉnh/Thành phố", max_length=100, blank=True, help_text="Ví dụ: Hà Nội, Điện Biên, TP.HCM...")
    bank_name = models.CharField("Tên ngân hàng", max_length=100, blank=True)
    bank_account_number = models.CharField("Số tài khoản", max_length=50, blank=True)
    bank_account_name = models.CharField("Tên chủ tài khoản", max_length=100, blank=True)
    payment_qr_code = models.ImageField("Ảnh mã QR", upload_to='qr_codes/', null=True, blank=True)
    registration_fee = models.DecimalField("Phí đăng ký (VNĐ)", max_digits=15, decimal_places=0, default=500000, help_text="Phí đăng ký cho mỗi đội tham gia")
    shop_discount_percentage = models.DecimalField("Phần trăm tiền lãi từ shop (%)", max_digits=5, decimal_places=2, default=0.00, help_text="Phần trăm tiền lãi từ shop được trừ vào phí đăng ký (0-100%)")
    rules = models.TextField("Điều lệ & Thông báo", blank=True, help_text="Nhập các điều lệ, quy định hoặc thông báo của giải đấu tại đây. Bạn có thể sử dụng mã HTML cơ bản để định dạng.")

    gallery_url = models.URLField(
        "Link Album Ảnh Gốc",
        max_length=500,
        blank=True,
        null=True,
        help_text="Dán đường link chia sẻ của album ảnh Google Drive hoặc Google Photos tại đây."
    )
    followers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='followed_tournaments', blank=True, verbose_name="Người theo dõi")
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tournament_detail', kwargs={'pk': self.pk})
    
    def calculate_shop_discount(self, cart_items):
        """
        Tính toán số tiền giảm giá từ tiền lãi của sản phẩm trong cart
        """
        if self.shop_discount_percentage <= 0:
            return 0
        
        total_profit = 0
        for item in cart_items:
            if item.product.cost_price:
                profit_per_item = item.product.profit_amount
                total_profit += profit_per_item * item.quantity
        
        # Tính phần trăm tiền lãi được trừ vào phí đăng ký
        discount_amount = total_profit * (self.shop_discount_percentage / 100)
        # Giới hạn giảm giá tối đa bằng phí đăng ký
        max_discount = self.registration_fee
        return min(discount_amount, max_discount)
    
    def get_final_registration_fee(self, cart_items):
        """
        Tính phí đăng ký cuối cùng sau khi trừ giảm giá từ shop
        """
        discount = self.calculate_shop_discount(cart_items)
        final_fee = self.registration_fee - discount
        return max(final_fee, 0)  # Không âm

class Group(models.Model):
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='groups')
    name = models.CharField(max_length=50)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["tournament", "name"], name="uniq_group_name_in_tournament")]

    def __str__(self):
        return f"{self.name} - {self.tournament.name}"

    def get_standings(self):
        """
        Tính toán và trả về bảng xếp hạng cho bảng đấu này.
        """
        from .models import Team  # Import model Team để tránh lỗi circular import
        standings = {}
        # Lấy danh sách các đội thuộc bảng đấu này thông qua model TeamRegistration
        teams_in_group = Team.objects.filter(registrations__group=self)
        for team in teams_in_group:
            standings[team.id] = {'played': 0, 'wins': 0, 'draws': 0, 'losses': 0, 'gf': 0, 'ga': 0, 'gd': 0, 'points': 0, 'team_obj': team}
        matches_in_group = self.tournament.matches.filter(
            team1__in=teams_in_group, team2__in=teams_in_group,
            team1_score__isnull=False, team2_score__isnull=False
        )
        for match in matches_in_group:
            team1_id, team2_id, score1, score2 = match.team1.id, match.team2.id, match.team1_score, match.team2_score
            if team1_id in standings and team2_id in standings:
                standings[team1_id]['played'] += 1; standings[team2_id]['played'] += 1
                standings[team1_id]['gf'] += score1; standings[team1_id]['ga'] += score2
                standings[team2_id]['gf'] += score2; standings[team2_id]['ga'] += score1
                if score1 > score2:
                    standings[team1_id]['wins'] += 1; standings[team1_id]['points'] += 3
                    standings[team2_id]['losses'] += 1
                elif score2 > score1:
                    standings[team2_id]['wins'] += 1; standings[team2_id]['points'] += 3
                    standings[team1_id]['losses'] += 1
                else:
                    standings[team1_id]['draws'] += 1; standings[team1_id]['points'] += 1
                    standings[team2_id]['draws'] += 1; standings[team2_id]['points'] += 1
        sorted_standings = list(standings.values())
        for stats in sorted_standings:
            stats['gd'] = stats['gf'] - stats['ga']
        sorted_standings.sort(key=lambda x: (x['points'], x['gd'], x['gf']), reverse=True)
        return sorted_standings

class Team(models.Model):
    PAYMENT_STATUS_CHOICES = [('UNPAID', 'Chưa thanh toán'), ('PENDING', 'Chờ xác nhận'), ('PAID', 'Đã thanh toán'), ('REJECTED', 'Từ chối')]
    name = models.CharField(max_length=100)
    coach_name = models.CharField(max_length=100, blank=True, help_text="Tên HLV (sử dụng cho dữ liệu cũ, nên dùng trường 'coach' bên dưới)")
    coach = models.ForeignKey(
        'users.CoachProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='team_coaching',
        verbose_name="Huấn luyện viên"
    )
    captain = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teams')
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    main_photo = models.ImageField("Ảnh đại diện đội", upload_to='team_main_photos/', null=True, blank=True, help_text="Ảnh toàn đội sẽ hiển thị ở Phòng Truyền thống.")
    kit_home_color = ColorField(verbose_name="Màu áo sân nhà", default='#FFFFFF')
    kit_away_color = ColorField(verbose_name="Màu áo sân khách", default='#1E293B')
    transfer_value = models.PositiveIntegerField("Giá trị đội bóng (VNĐ)", default=0, help_text="Giá trị nền của đội bóng, không bao gồm phiếu bầu.")
    votes = models.PositiveIntegerField("Số phiếu bình chọn", default=0)    
    budget = models.BigIntegerField("Ngân sách (VNĐ)", default=50000000, help_text="Ngân sách dùng để thực hiện chuyển nhượng.")

    # Trường mới: liên kết tới nhiều giải đấu thông qua "Sổ Đăng Ký"
    tournaments = models.ManyToManyField(Tournament, through='TeamRegistration', related_name='teams_registered', blank=True)

    class Meta:
        constraints = [
            # Xóa ràng buộc cũ liên quan đến tournament
            models.UniqueConstraint(fields=["captain", "name"], name="unique_team_name_per_captain"),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from .utils import get_current_vote_value 
        # Tự động tính toán giá trị nền khi tạo đội mới và giá trị chưa được đặt
        if self._state.adding and self.transfer_value == 0:
            # Giá trị nền = 10 lần giá trị 1 phiếu bầu của cầu thủ tại thời điểm hiện tại
            self.transfer_value = get_current_vote_value() * 10

        # Giữ nguyên logic nén ảnh
        if self.logo:
            self.logo = self.compress_image(self.logo)
        
        super().save(*args, **kwargs)

    def compress_image(self, image_field):
        if not image_field._file: return image_field
        img = Image.open(image_field)
        if img.format == 'GIF': return image_field
        if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
        buffer = BytesIO()
        if img.height > 1280 or img.width > 1280:
            img.thumbnail((1280, 1280))
        img.save(buffer, format='JPEG', quality=85, optimize=True)

        file_name = os.path.basename(image_field.name)
        new_image = ContentFile(buffer.getvalue(), name=file_name)
        return new_image

class Player(models.Model):
    FOOT_CHOICES = [('RIGHT', 'Phải'), ('LEFT', 'Trái'), ('BOTH', 'Cả hai')]
    POSITION_CHOICES = [('GK', 'Thủ môn'), ('DF', 'Hậu vệ'), ('MF', 'Tiền vệ'), ('FW', 'Tiền đạo')]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='player_profile')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, related_name='players', null=True, blank=True)
    full_name = models.CharField(max_length=100)
    jersey_number = models.PositiveIntegerField()
    position = models.CharField(max_length=10, choices=POSITION_CHOICES)
    avatar = models.ImageField(upload_to='player_avatars/', null=True, blank=True)
    transfer_value = models.PositiveIntegerField("Giá trị chuyển nhượng (VNĐ)", default=0, help_text="Để 0 nếu chưa có định giá.")
    height = models.PositiveIntegerField("Chiều cao (cm)", null=True, blank=True)
    weight = models.PositiveIntegerField("Cân nặng (kg)", null=True, blank=True)
    preferred_foot = models.CharField("Chân thuận", max_length=5, choices=FOOT_CHOICES, blank=True)
    date_of_birth = models.DateField("Ngày sinh", null=True, blank=True)
    specialty_position = models.CharField("Vị trí sở trường", max_length=100, blank=True, help_text="Ví dụ: Tiền đạo cắm, Hậu vệ cánh trái...")
    agent_contact = models.CharField("Thông tin liên hệ (đại diện)", max_length=200, blank=True, help_text="Số điện thoại hoặc email của người đại diện.")
    votes = models.PositiveIntegerField("Số phiếu bình chọn", default=0)
    edit_count = models.PositiveIntegerField("Số lần chỉnh sửa", default=0, editable=False)

    # === THÊM 2 TRƯỜNG MỚI VÀO ĐÂY ===
    region = models.CharField(
        "Khu vực", 
        max_length=20, 
        choices=Tournament.Region.choices, 
        default=Tournament.Region.KHAC,
        help_text="Khu vực hoạt động chính của cầu thủ."
    )
    location_detail = models.CharField(
        "Tỉnh / Thành phố", 
        max_length=100, 
        blank=True, 
        help_text="Ví dụ: Hà Nội, Điện Biên, TP.HCM..."
    )
    is_looking_for_club = models.BooleanField(
        "Đang tìm CLB", 
        default=False, 
        help_text="Đánh dấu nếu cầu thủ này là cầu thủ tự do hoặc muốn tìm một bến đỗ mới."
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    donation_qr_code = models.ImageField(
        "Mã QR ủng hộ", 
        upload_to='player_qrcodes/', 
        null=True, 
        blank=True, 
        help_text="Tải lên ảnh mã QR cá nhân (Momo, VNPAY,...) để nhận donate từ người hâm mộ."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["team", "jersey_number"], name="uniq_jersey_per_team"),
            models.CheckConstraint(check=Q(jersey_number__gte=1) & Q(jersey_number__lte=99), name="jersey_between_1_99"),
        ]

    def __str__(self):
        return f"{self.full_name} (#{self.jersey_number})"
    
    def save(self, *args, **kwargs):
        if self.avatar and self.avatar._file:
            img = Image.open(self.avatar)
            if img.format != 'GIF':
                if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
                buffer = BytesIO()
                if img.height > 800 or img.width > 800:
                    img.thumbnail((800, 800))
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                
                # === SỬA LỖI TẠI ĐÂY ===
                file_name = os.path.basename(self.avatar.name)
                self.avatar = ContentFile(buffer.getvalue(), name=file_name)
        
        super().save(*args, **kwargs)

    def clean(self):
        if self.team_id and self.jersey_number is not None:
            exists = Player.objects.filter(team_id=self.team_id, jersey_number=self.jersey_number)
            if self.pk: exists = exists.exclude(pk=self.pk)
            if exists.exists():
                raise ValidationError({'jersey_number': 'Số áo đã tồn tại trong đội.'})


class Match(models.Model):
    ROUND_CHOICES = [
        ('LEAGUE', 'League'),
        ('GROUP', 'Vòng bảng'),
        ('QUARTER', 'Tứ kết'),
        ('SEMI', 'Bán kết'),
        ('THIRD_PLACE', 'Tranh Hạng Ba'), # <-- DÒNG MỚI
        ('FINAL', 'Chung kết'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    match_round = models.CharField(max_length=20, choices=ROUND_CHOICES, default='GROUP') # Tăng max_length
    team1 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team1')
    team2 = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='matches_as_team2')
    match_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    team1_score = models.PositiveIntegerField(null=True, blank=True)
    team2_score = models.PositiveIntegerField(null=True, blank=True)
    team1_penalty_score = models.PositiveIntegerField("Tỉ số penalty đội 1", null=True, blank=True)
    team2_penalty_score = models.PositiveIntegerField("Tỉ số penalty đội 2", null=True, blank=True)
    livestream_url = models.URLField(max_length=500, null=True, blank=True)
    referee = models.CharField(max_length=100, null=True, blank=True)
    commentator = models.CharField(max_length=100, null=True, blank=True)
    ticker_text = models.CharField(max_length=255, blank=True, help_text="Dòng chữ chạy trên màn hình livestream. Nếu để trống, hệ thống sẽ dùng thông báo mặc định.")
    # League metadata
    round_number = models.PositiveIntegerField("Vòng", null=True, blank=True)
    leg = models.PositiveSmallIntegerField("Lượt", null=True, blank=True, help_text="1 = lượt đi, 2 = lượt về")
    # === BẮT ĐẦU THÊM 2 TRƯỜNG MỚI TẠI ĐÂY ===
    cover_photo = models.ImageField(
        "Ảnh bìa trận đấu",
        upload_to='match_covers/',
        null=True,
        blank=True,
        help_text="Ảnh đại diện hiển thị cho trận đấu trong thư viện ảnh."
    )
    gallery_url = models.URLField(
        "Link Album ảnh của trận đấu",
        max_length=500,
        null=True,
        blank=True,
        help_text="Dán đường link album ảnh (Google Photos, Facebook,...) của riêng trận đấu này."
    )
    def get_absolute_url(self):
        return reverse("match_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.team1.name} vs {self.team2.name}"

    @property
    def winner(self):
        if self.team1_score is not None and self.team2_score is not None:
            if self.team1_score > self.team2_score:
                return self.team1
            elif self.team2_score > self.team1_score:
                return self.team2
            # Xử lý trường hợp hòa và có tỉ số penalty
            elif self.team1_penalty_score is not None and self.team2_penalty_score is not None:
                if self.team1_penalty_score > self.team2_penalty_score:
                    return self.team1
                elif self.team2_penalty_score > self.team1_penalty_score:
                    return self.team2
        return None

    @property
    def loser(self):
        if self.winner is not None:
            return self.team2 if self.winner == self.team1 else self.team1
        return None

    # Điều kiện đồng hồ
    @property
    def is_live(self):
        """Kiểm tra xem trận đấu có đang diễn ra không."""
        now = timezone.now()
        # Giả sử một trận đấu kéo dài 2 tiếng (120 phút)
        return self.match_time <= now < self.match_time + timedelta(minutes=120)

class Lineup(models.Model):
    STATUS_CHOICES = [('STARTER', 'Đá chính'), ('SUBSTITUTE', 'Dự bị')]
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='lineups')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='lineups')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='+')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player.full_name} ({self.status}) for {self.match}"

    def clean(self):
        if self.team_id not in [self.match.team1_id, self.match.team2_id]: raise ValidationError("Đội không thuộc trận này.")
        if self.player.team_id != self.team_id: raise ValidationError("Cầu thủ không thuộc đội này.")
        if self.status == "STARTER":
            qs = Lineup.objects.filter(match=self.match, team=self.team, status="STARTER")
            if self.pk: qs = qs.exclude(pk=self.pk)
            if qs.count() >= MAX_STARTERS: raise ValidationError(f"Tối đa {MAX_STARTERS} cầu thủ đá chính cho mỗi đội.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

class Goal(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='goals')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='goals')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='goals')
    minute = models.PositiveIntegerField(null=True, blank=True)
    # --- THÊM DÒNG MỚI NÀY VÀO ---
    is_own_goal = models.BooleanField("Bàn phản lưới?", default=False)
    created_at = models.DateTimeField(default=timezone.now)
    # -----------------------------
    class Meta:
        constraints = [models.CheckConstraint(check=Q(minute__gte=0) & Q(minute__lte=150), name="goal_minute_range")]
    def clean(self):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        if hasattr(self, 'match'):
            if self.team_id not in [self.match.team1_id, self.match.team2_id]: raise ValidationError("Đội ghi bàn không thuộc trận.")
            if self.player_id and self.player.team_id != self.team_id: raise ValidationError("Cầu thủ ghi bàn không thuộc đội.")
    def save(self, *args, **kwargs):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        self.full_clean()
        return super().save(*args, **kwargs)
    def __str__(self):
        return f"Goal by {self.player.full_name} in {self.match}"

class Card(models.Model):
    CARD_CHOICES = [('YELLOW', 'Thẻ vàng'), ('RED', 'Thẻ đỏ')]
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='cards')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='cards')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=10, choices=CARD_CHOICES)
    minute = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        constraints = [models.CheckConstraint(check=Q(minute__gte=0) & Q(minute__lte=150), name="card_minute_range")]
    def clean(self):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        if hasattr(self, 'match'):
            if self.team_id not in [self.match.team1_id, self.match.team2_id]: raise ValidationError("Đội nhận thẻ không thuộc trận.")
            if self.player_id and self.player.team_id != self.team_id: raise ValidationError("Cầu thủ nhận thẻ không thuộc đội.")
    def save(self, *args, **kwargs):
        if self.team_id is None and self.player_id: self.team_id = self.player.team_id
        self.full_clean()
        return super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.get_card_type_display()} for {self.player.full_name} in {self.match}"

class HomeBanner(models.Model):
    title = models.CharField(max_length=120)
    subtitle = models.CharField(max_length=200, blank=True)
    button_text = models.CharField(max_length=40, blank=True)
    button_url = models.URLField(blank=True)
    image = models.ImageField(upload_to='banners/')
    order = models.PositiveIntegerField(default=0, help_text="Thứ tự hiển thị, nhỏ trước")
    is_active = models.BooleanField(default=True)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ("order", "id")
    def __str__(self):
        return f"{self.title} (#{self.order})"

class Comment(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return f'Comment by {self.user.username} on {self.match}'

class Announcement(models.Model):
    AUDIENCE_CHOICES = [('PUBLIC', 'Gửi cho Mọi người (Cầu thủ & Đội trưởng)'), ('CAPTAINS_ONLY', 'Chỉ gửi cho Đội trưởng')]
    audience = models.CharField("Đối tượng", max_length=15, choices=AUDIENCE_CHOICES, default='PUBLIC', help_text="Chọn nhóm người dùng sẽ thấy thông báo này.")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='announcements')
    title = models.CharField("Tiêu đề", max_length=200)
    content = models.TextField("Nội dung")
    created_at = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField("Công khai", default=True, help_text="Bỏ chọn nếu đây là bản nháp.")
    read_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='read_announcements', blank=True, verbose_name="Đã đọc bởi")
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.title

# === BẮT ĐẦU THÊM MODEL MỚI TẠI ĐÂY ===
class TournamentPhoto(models.Model):
    """Lưu trữ một ảnh trong thư viện của giải đấu."""
    tournament = models.ForeignKey(
        Tournament, 
        on_delete=models.CASCADE, 
        related_name='photos',
        verbose_name="Giải đấu"
    )
    image = models.ImageField("Ảnh", upload_to='tournament_photos/')
    caption = models.CharField("Chú thích", max_length=200, blank=True)
    uploaded_at = models.DateTimeField("Ngày tải lên", auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Ảnh Giải đấu"
        verbose_name_plural = "Thư viện ảnh Giải đấu"

    def __str__(self):
        return f"Ảnh của giải {self.tournament.name} - {self.pk}"

    def save(self, *args, **kwargs):
        # Tối ưu ảnh trước khi lưu (giống như model Player/Team)
        if self.image and self.image._file:
            img = Image.open(self.image)
            if img.format != 'GIF':
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                buffer = BytesIO()
                # Giảm kích thước ảnh lớn hơn 2K
                if img.height > 1920 or img.width > 1920:
                    img.thumbnail((1920, 1920))
                
                img.save(buffer, format='JPEG', quality=85, optimize=True)
                
                file_name = os.path.basename(self.image.name)
                self.image = ContentFile(buffer.getvalue(), name=file_name)

        super().save(*args, **kwargs)

# === BẮT ĐẦU THÊM MODEL MỚI ===
class Notification(models.Model):
    """
    Lưu trữ các thông báo tự động được tạo bởi hệ thống.
    """
    # Các loại thông báo, có thể mở rộng sau này
    class NotificationType(models.TextChoices):
        MATCH_RESULT = 'MATCH_RESULT', 'Kết quả trận đấu'
        NEW_TEAM = 'NEW_TEAM', 'Đội mới đăng ký'
        DRAW_COMPLETE = 'DRAW_COMPLETE', 'Bốc thăm hoàn tất'  
        SCHEDULE_CREATED = 'SCHEDULE_CREATED', 'Lịch thi đấu mới' 
        VOTE_AWARDED = 'VOTE_AWARDED', 'Nhận phiếu bầu'
        PLAYER_CLAIM_REQUEST = 'player_claim_request', 'Yêu cầu liên kết cầu thủ'
        PLAYER_CLAIM_CONFIRMED = 'player_claim_confirmed', 'Liên kết cầu thủ thành công'
        PLAYER_CLAIM_REJECTED = 'player_claim_rejected', 'Yêu cầu liên kết bị từ chối'
        GENERIC = 'GENERIC', 'Thông báo chung'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField("Tiêu đề", max_length=255)
    message = models.TextField("Nội dung")
    notification_type = models.CharField(
        "Loại thông báo",
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.GENERIC
    )
    is_read = models.BooleanField("Đã đọc", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_url = models.URLField("Link liên quan", max_length=500, null=True, blank=True)
    # Thêm các trường để lưu thông tin yêu cầu liên kết cầu thủ
    related_player = models.ForeignKey('Player', on_delete=models.CASCADE, null=True, blank=True, related_name='claim_notifications')
    related_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='claim_request_notifications')

    class Meta:
        ordering = ['-created_at']
        # === BẮT ĐẦU THÊM MỚI ===
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
        # === KẾT THÚC THÊM MỚI ===

    def __str__(self):
        return f"Thông báo cho {self.user.username}: {self.title}"

# === THÊM MODEL MỚI VÀO CUỐI FILE ===
class TeamAchievement(models.Model):
    """
    Lưu trữ một thành tích mà một đội bóng đạt được trong một giải đấu.
    """
    ACHIEVEMENT_CHOICES = [
        ('CHAMPION', 'Vô địch'),
        ('RUNNER_UP', 'Á quân'),
        ('THIRD_PLACE', 'Hạng ba'),
        ('FAIR_PLAY', 'Giải Phong cách / Fair Play'),
        ('OTHER', 'Khác'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='achievements', verbose_name="Đội bóng")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='team_achievements', verbose_name="Giải đấu")
    achievement_type = models.CharField("Loại danh hiệu", max_length=20, choices=ACHIEVEMENT_CHOICES)
    description = models.CharField("Mô tả (tùy chọn)", max_length=255, blank=True, help_text="Ghi rõ hơn về danh hiệu, ví dụ: 'Vô địch mùa giải 2025'")
    achieved_at = models.DateField("Ngày đạt được", default=timezone.now)

    class Meta:
        ordering = ['-achieved_at']
        verbose_name = "Thành tích Đội bóng"
        verbose_name_plural = "Thành tích Đội bóng"
        unique_together = ('team', 'tournament', 'achievement_type') # Đảm bảo mỗi đội chỉ có 1 danh hiệu/giải

    def __str__(self):
        return f"{self.team.name} - {self.get_achievement_type_display()} tại {self.tournament.name}"

# === THÊM MODEL MỚI VÀO CUỐI FILE ===
class Substitution(models.Model):
    """Lưu trữ một sự kiện thay người trong trận đấu."""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='substitutions', verbose_name="Trận đấu")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='substitutions', verbose_name="Đội")
    player_in = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='substitutions_in', verbose_name="Cầu thủ vào sân")
    player_out = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='substitutions_out', verbose_name="Cầu thủ ra sân")
    minute = models.PositiveIntegerField("Phút", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['minute']
        verbose_name = "Lượt thay người"
        verbose_name_plural = "Các lượt thay người"

    def __str__(self):
        return f"{self.player_in.full_name} vào thay {self.player_out.full_name} ở phút {self.minute}'"

    def clean(self):
        # Tự động gán đội dựa trên cầu thủ vào sân
        if self.player_in_id and not self.team_id:
            self.team = self.player_in.team
        
        # Kiểm tra tính hợp lệ
        if self.player_in and self.player_out and self.player_in.team != self.player_out.team:
            raise ValidationError("Cầu thủ vào và ra phải cùng một đội.")
        if self.player_in == self.player_out:
            raise ValidationError("Cầu thủ vào và ra không được là một.")
            
        # === SỬA LỖI TẠI ĐÂY ===
        # Chỉ kiểm tra khi đối tượng match đã được gán
        if hasattr(self, 'match'):
            if self.team_id not in [self.match.team1_id, self.match.team2_id]:
                raise ValidationError("Đội thay người không thuộc trận đấu này.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# === Sự kiện các mốc thời gian ===
class MatchEvent(models.Model):
    """Lưu trữ các sự kiện mốc thời gian của trận đấu."""
    class EventType(models.TextChoices):
        MATCH_START = 'MATCH_START', 'Trận đấu bắt đầu'
        HALF_TIME = 'HALF_TIME', 'Hết hiệp 1'
        MATCH_END = 'MATCH_END', 'Trận đấu kết thúc'
        EXTRA_TIME_START = 'EXTRA_TIME_START', 'Hiệp phụ bắt đầu'
        PENALTY_SHOOTOUT_START = 'PENALTY_SHOOTOUT_START', 'Loạt sút luân lưu'

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField("Loại sự kiện", max_length=30, choices=EventType.choices)
    text = models.CharField("Nội dung hiển thị", max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Sự kiện trận đấu"
        verbose_name_plural = "Các sự kiện trận đấu"

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.match}"        

class VoteRecord(models.Model):
    """Lưu lại lịch sử một lượt bỏ phiếu để đảm bảo minh bạch và chống gian lận."""
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes_cast', verbose_name="Người bỏ phiếu")
    voted_for = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='votes_received', verbose_name="Cầu thủ được vote")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, verbose_name="Giải đấu")
    weight = models.PositiveIntegerField("Số phiếu", default=1)
    voted_at = models.DateTimeField("Thời gian vote", auto_now_add=True)

    class Meta:
        # Mỗi người chỉ được bầu cho 1 cầu thủ trong 1 giải đấu
        unique_together = ('voter', 'voted_for', 'tournament')
        ordering = ['-voted_at']

    def __str__(self):
        return f"{self.voter.username} voted for {self.voted_for.full_name} in {self.tournament.name}"        

# === THÊM MODEL MỚI VÀO CUỐI FILE ===
class TournamentStaff(models.Model):
    """
    Liên kết một User với vai trò chuyên môn trong một Giải đấu cụ thể.
    """
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='staff',
        verbose_name="Giải đấu"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_assignments',
        verbose_name="Thành viên"
    )
    role = models.ForeignKey(
        'users.Role', # Dùng chuỗi để tránh lỗi import vòng
        on_delete=models.CASCADE,
        verbose_name="Vai trò chuyên môn"
    )

    class Meta:
        ordering = ['role']
        verbose_name = "Thành viên chuyên môn"
        verbose_name_plural = "Đội ngũ chuyên môn"
        unique_together = ('tournament', 'user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.name} for {self.tournament.name}"        

class MatchNote(models.Model):
    """Lưu trữ các ghi chú chuẩn bị cho trận đấu của BLV và Đội trưởng."""
    class NoteType(models.TextChoices):
        COMMENTATOR = 'COMMENTATOR', 'Ghi chú của Bình luận viên'
        CAPTAIN = 'CAPTAIN', 'Ghi chú của Đội trưởng'

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='notes', verbose_name="Trận đấu")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Tác giả")
    note_type = models.CharField("Loại ghi chú", max_length=20, choices=NoteType.choices)

    # Dành riêng cho ghi chú của BLV (chia 2 cột)
    commentator_notes_team1 = models.TextField("Ghi chú về Đội 1", blank=True)
    commentator_notes_team2 = models.TextField("Ghi chú về Đội 2", blank=True)

    # Dành riêng cho ghi chú của Đội trưởng (chỉ có 1 nội dung)
    # Thêm related_name để tránh xung đột
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notes', verbose_name="Đội của Đội trưởng")
    captain_note = models.TextField("Ghi chú gửi BLV", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        # Đảm bảo mỗi người chỉ có 1 loại ghi chú cho 1 trận đấu
        # Ví dụ: 1 BLV chỉ có 1 bộ ghi chú 2 cột cho trận X
        # 1 Đội trưởng chỉ có 1 ghi chú gửi BLV cho trận X
        unique_together = ('match', 'author', 'note_type', 'team')
        verbose_name = "Ghi chú Trận đấu"
        verbose_name_plural = "Ghi chú Trận đấu"

    def __str__(self):
        return f"Ghi chú của {self.author.username} cho trận {self.match.pk}"        

class TeamRegistration(models.Model):
    """Lưu trữ một bản ghi đăng ký của một Đội vào một Giải đấu."""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='registrations', verbose_name="Đội")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='registrations', verbose_name="Giải đấu")
    payment_status = models.CharField("Trạng thái thanh toán", max_length=10, choices=Team.PAYMENT_STATUS_CHOICES, default='UNPAID')
    payment_proof = models.ImageField("Bằng chứng thanh toán", upload_to='payment_proofs/', null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='registrations', verbose_name="Bảng đấu")
    registered_at = models.DateTimeField("Ngày đăng ký", auto_now_add=True)

    class Meta:
        unique_together = ('team', 'tournament') # Đảm bảo một đội chỉ đăng ký 1 lần/giải
        verbose_name = "Đơn đăng ký của Đội"
        verbose_name_plural = "Các đơn đăng ký của Đội"

    def __str__(self):
        return f"{self.team.name} @ {self.tournament.name}"

    def save(self, *args, **kwargs):
        # Tái sử dụng logic nén ảnh từ model Team
        if self.payment_proof and hasattr(self.payment_proof, 'file'):
            # Cần một instance tạm thời của Team để gọi hàm compress_image
            temp_team_instance = Team()
            self.payment_proof = temp_team_instance.compress_image(self.payment_proof)
        super().save(*args, **kwargs)        

class TeamVoteRecord(models.Model):
    """Lưu lại lịch sử một lượt bỏ phiếu cho ĐỘI BÓNG."""
    voter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_votes_cast', verbose_name="Người bỏ phiếu")
    voted_for = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='votes_received', verbose_name="Đội được vote")
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, verbose_name="Giải đấu")
    weight = models.PositiveIntegerField("Số phiếu", default=1)
    voted_at = models.DateTimeField("Thời gian vote", auto_now_add=True)

    class Meta:
        # Mỗi người chỉ được bầu cho 1 đội trong 1 giải đấu
        unique_together = ('voter', 'voted_for', 'tournament')
        ordering = ['-voted_at']
        verbose_name = "Phiếu bầu cho Đội"
        verbose_name_plural = "Các phiếu bầu cho Đội"

    def __str__(self):
        return f"{self.voter.username} voted for {self.voted_for.name} in {self.tournament.name}"        

# Chuyển nhượng
class PlayerTransfer(models.Model):
    """Lưu trữ một lời mời chuyển nhượng cầu thủ giữa hai đội."""
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Đang chờ'
        ACCEPTED = 'ACCEPTED', 'Đã chấp nhận'
        REJECTED = 'REJECTED', 'Đã từ chối'
        CANCELED = 'CANCELED', 'Đã hủy'

    class TransferType(models.TextChoices):
        PERMANENT = 'PERMANENT', 'Mua đứt'
        LOAN = 'LOAN', 'Cho mượn'

    inviting_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='sent_transfers',
        verbose_name="Đội mời"
    )
    current_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='received_transfers',
        verbose_name="Đội hiện tại",
        null=True,
        blank=True
    )
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='transfer_requests',
        verbose_name="Cầu thủ"
    )
    status = models.CharField(
        "Trạng thái",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    transfer_type = models.CharField(
        "Loại hình chuyển nhượng",
        max_length=10,
        choices=TransferType.choices,
        default=TransferType.PERMANENT
    )
    loan_end_date = models.DateField("Ngày hết hạn cho mượn", null=True, blank=True)
    
    offer_amount = models.BigIntegerField("Số tiền đề nghị (VNĐ)", default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lời mời Chuyển nhượng"
        verbose_name_plural = "Các lời mời Chuyển nhượng"

    def __str__(self):
        current_team_name = self.current_team.name if self.current_team else "Cầu thủ tự do"
        return f"{self.inviting_team.name} mời {self.player.full_name} từ {current_team_name}"


# === THÊM MODEL MỚI VÀO CUỐI TỆP ===
class ScoutingList(models.Model):
    """Lưu trữ một bản ghi khi một đội theo dõi một cầu thủ."""
    team = models.ForeignKey(
        Team, 
        on_delete=models.CASCADE, 
        related_name='scouting_list',
        verbose_name="Đội bóng theo dõi"
    )
    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE, 
        related_name='scouted_by',
        verbose_name="Cầu thủ được theo dõi"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        # Đảm bảo một đội không thể theo dõi cùng một cầu thủ nhiều lần
        unique_together = ('team', 'player')
        verbose_name = "Danh sách Theo dõi"
        verbose_name_plural = "Danh sách Theo dõi"

    def __str__(self):
        return f"Đội {self.team.name} đang theo dõi {self.player.full_name}"        


# nhà tài trợ
# Model 1: Để BTC quản lý các gói tài trợ (như đã đề xuất)
class SponsorshipPackage(models.Model):
    """
    Đại diện cho một gói tài trợ mà BTC có thể định nghĩa cho giải đấu.
    Ví dụ: 'Nhà tài trợ Vàng', 'Nhà tài trợ Bạc'...
    """
    tournament = models.ForeignKey(
        'Tournament', 
        on_delete=models.CASCADE,
        related_name='sponsorship_packages',
        verbose_name="Giải đấu"
    )
    name = models.CharField("Tên gói", max_length=100)
    price = models.DecimalField("Mức tài trợ (VNĐ)", max_digits=12, decimal_places=0, null=True, blank=True)
    description = models.TextField("Mô tả quyền lợi", blank=True)
    order = models.PositiveIntegerField(
        "Thứ tự ưu tiên",
        default=0,
        help_text="Số nhỏ hơn sẽ hiển thị trước (Vàng: 0, Bạc: 1, ...)."
    )

    benefits = models.TextField(
        "Danh sách quyền lợi",
        blank=True,
        help_text="Nhập mỗi quyền lợi trên một dòng. Ví dụ: Treo banner tại sân, Nhắc tên trên livestream..."
    )

    class Meta:
        verbose_name = "Gói tài trợ"
        verbose_name_plural = "Các gói tài trợ"
        ordering = ['order', '-price'] 

    def __str__(self):
        return f"{self.name} ({self.tournament.name})"


# Model 2: Liên kết Nhà tài trợ với Giải đấu (đã sửa đổi)
class Sponsorship(models.Model):
    """Liên kết một Nhà tài trợ với một Giải đấu thông qua một Gói tài trợ."""

    class SponsorshipStatus(models.TextChoices):
        POTENTIAL = 'POTENTIAL', 'Tiềm năng'
        CONTACTED = 'CONTACTED', 'Đã liên hệ'
        CONFIRMED = 'CONFIRMED', 'Đã chốt'
        PAID = 'PAID', 'Đã thanh toán'
        COMPLETED = 'COMPLETED', 'Hoàn thành'

    class Meta:
        verbose_name = "Nhà tài trợ Giải đấu"
        verbose_name_plural = "Các nhà tài trợ Giải đấu"
        # Sắp xếp theo thứ tự gói, rồi đến thứ tự tùy chỉnh của NTT
        ordering = ['package__order', 'order']

    tournament = models.ForeignKey(
        'Tournament', # Giữ lại 'Tournament' nếu class Tournament ở dưới
        on_delete=models.CASCADE,
        related_name='sponsorships',
        verbose_name="Giải đấu"
    )
    # --- PHẦN KẾT HỢP ---
    # Thay 'package_name' bằng ForeignKey đến model SponsorshipPackage
    package = models.ForeignKey(
        SponsorshipPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=False, # Yêu cầu BTC phải chọn một gói
        verbose_name="Gói tài trợ"
    )
    # === THÊM TRƯỜNG MỚI VÀO ĐÂY ===
    status = models.CharField(
        "Trạng thái",
        max_length=20,
        choices=SponsorshipStatus.choices,
        default=SponsorshipStatus.POTENTIAL,
        db_index=True
    )
    # === THÊM TRƯỜNG JSONFIELD VÀO ĐÂY ===
    benefits_checklist = models.JSONField(
        "Checklist Quyền lợi",
        default=list, # Mặc định là một danh sách rỗng
        blank=True
    )
    # Giữ nguyên phần linh hoạt của bạn
    sponsor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sponsorships',
        verbose_name="Tài khoản Nhà tài trợ (nếu có)",
        limit_choices_to={'profile__roles__id': 'SPONSOR'},
        null=True,
        blank=True
    )
    sponsor_name = models.CharField(
        "Tên Nhà tài trợ (nhập tay)",
        max_length=150,
        blank=True,
        help_text="Chỉ điền nếu NTT không có tài khoản trên hệ thống."
    )
    logo = models.ImageField(
        "Logo",
        upload_to='sponsor_logos/',
        blank=True,
        null=True
    )
    website_url = models.URLField(
        "Link trang web",
        blank=True
    )
    
    order = models.PositiveIntegerField("Thứ tự trong gói", default=0, help_text="Số nhỏ hơn hiển thị trước.")
    is_active = models.BooleanField("Hiển thị công khai", default=True)

    def __str__(self):
        display_name = self.sponsor_name or (self.sponsor.username if self.sponsor else "Chưa xác định")
        return f"{display_name} tài trợ cho {self.tournament.name}"

    def clean(self):
        if self.sponsor and self.sponsor_name:
            raise ValidationError("Chỉ chọn 'Tài khoản' hoặc điền 'Tên nhập tay', không được cả hai.")
        if not self.sponsor and not self.sponsor_name:
            raise ValidationError("Phải chọn 'Tài khoản' hoặc điền 'Tên nhập tay'.")


class SponsorClick(models.Model):
    """Ghi lại mỗi lượt click vào link của nhà tài trợ."""
    class Meta:
        verbose_name = "Lượt click của Nhà tài trợ"
        verbose_name_plural = "Các lượt click của Nhà tài trợ"
        ordering = ['-timestamp']

    sponsorship = models.ForeignKey(Sponsorship, on_delete=models.CASCADE, related_name='clicks')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Click for {self.sponsorship.sponsor.username} at {self.timestamp}"


# ===== HỆ THỐNG QUẢN LÝ TÀI CHÍNH GIẢI ĐẤU =====

class TournamentBudget(models.Model):
    """Ngân sách và quản lý tài chính giải đấu"""
    tournament = models.OneToOneField(Tournament, on_delete=models.CASCADE, related_name='budget')
    initial_budget = models.DecimalField(max_digits=15, decimal_places=0, default=0, verbose_name="Ngân sách ban đầu")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Ngân sách giải đấu"
        verbose_name_plural = "Ngân sách giải đấu"
    
    def __str__(self):
        return f"Ngân sách {self.tournament.name}"
    
    def get_total_revenue(self):
        """Tính tổng thu"""
        return self.revenue_items.aggregate(total=Sum('amount'))['total'] or 0
    
    def get_total_expenses(self):
        """Tính tổng chi"""
        return self.expense_items.aggregate(total=Sum('amount'))['total'] or 0
    
    def get_profit_loss(self):
        """Tính lời/lỗ"""
        return self.get_total_revenue() - self.get_total_expenses()
    
    def get_budget_status(self):
        """Trạng thái ngân sách"""
        profit_loss = self.get_profit_loss()
        if profit_loss > 0:
            return 'PROFIT'
        elif profit_loss < 0:
            return 'LOSS'
        else:
            return 'BREAK_EVEN'
    
    def get_budget_status_display(self):
        """Hiển thị trạng thái ngân sách"""
        status = self.get_budget_status()
        if status == 'PROFIT':
            return 'Có lời'
        elif status == 'LOSS':
            return 'Bị lỗ'
        else:
            return 'Hòa vốn'


class RevenueItem(models.Model):
    """Khoản thu"""
    REVENUE_CATEGORIES = [
        ('TEAM_FEES', 'Phí đăng ký đội'),
        ('SPONSORSHIP', 'Tài trợ'),
        ('PENALTIES', 'Tiền phạt'),
        ('TICKETS', 'Bán vé'),
        ('MERCHANDISE', 'Bán hàng hóa'),
        ('OTHER', 'Khác'),
    ]
    
    budget = models.ForeignKey(TournamentBudget, on_delete=models.CASCADE, related_name='revenue_items')
    category = models.CharField(max_length=20, choices=REVENUE_CATEGORIES, verbose_name="Danh mục")
    description = models.CharField(max_length=200, verbose_name="Mô tả")
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Số tiền")
    date = models.DateField(verbose_name="Ngày")
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    is_auto_calculated = models.BooleanField(default=False, verbose_name="Tự động tính")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Khoản thu"
        verbose_name_plural = "Khoản thu"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.description}: {self.amount:,} VNĐ"


class ExpenseItem(models.Model):
    """Khoản chi"""
    EXPENSE_CATEGORIES = [
        ('VENUE', 'Tiền sân bãi'),
        ('REFEREE', 'Trọng tài'),
        ('LIVESTREAM', 'Livestream'),
        ('PHOTOGRAPHY', 'Chụp ảnh'),
        ('TROPHIES', 'Cờ cúp, huy chương'),
        ('REFRESHMENTS', 'Nước uống'),
        ('TRANSPORTATION', 'Đi lại'),
        ('EQUIPMENT', 'Thiết bị'),
        ('MARKETING', 'Marketing'),
        ('OTHER', 'Khác'),
    ]
    
    budget = models.ForeignKey(TournamentBudget, on_delete=models.CASCADE, related_name='expense_items')
    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES, verbose_name="Danh mục")
    description = models.CharField(max_length=200, verbose_name="Mô tả")
    amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="Số tiền")
    date = models.DateField(verbose_name="Ngày")
    notes = models.TextField(blank=True, verbose_name="Ghi chú")
    receipt_image = models.ImageField(upload_to='expense_receipts/', blank=True, null=True, verbose_name="Hóa đơn")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Khoản chi"
        verbose_name_plural = "Khoản chi"
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.description}: {self.amount:,} VNĐ"


class BudgetHistory(models.Model):
    """Lịch sử thay đổi ngân sách"""
    budget = models.ForeignKey(TournamentBudget, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=50, verbose_name="Hành động")  # ADD_REVENUE, ADD_EXPENSE, UPDATE_BUDGET
    description = models.CharField(max_length=200, verbose_name="Mô tả")
    amount = models.DecimalField(max_digits=15, decimal_places=0, null=True, blank=True, verbose_name="Số tiền")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Người thực hiện")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian")
    
    class Meta:
        verbose_name = "Lịch sử ngân sách"
        verbose_name_plural = "Lịch sử ngân sách"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.description} ({self.timestamp})"


class CoachRecruitment(models.Model):
    """Lưu trữ lời mời chiêu mộ huấn luyện viên từ đội bóng."""
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Đang chờ'
        ACCEPTED = 'ACCEPTED', 'Đã chấp nhận'
        REJECTED = 'REJECTED', 'Đã từ chối'
        CANCELED = 'CANCELED', 'Đã hủy'
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='coach_recruitments',
        verbose_name="Đội bóng"
    )
    coach = models.ForeignKey(
        'users.CoachProfile',
        on_delete=models.CASCADE,
        related_name='recruitment_offers',
        verbose_name="Huấn luyện viên"
    )
    status = models.CharField(
        "Trạng thái",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Thông tin đề nghị
    salary_offer = models.DecimalField(
        "Mức lương đề nghị (VNĐ)",
        max_digits=15,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="Mức lương/thù lao cho HLV"
    )
    contract_duration = models.CharField(
        "Thời hạn hợp đồng",
        max_length=100,
        blank=True,
        help_text="Ví dụ: 1 năm, 6 tháng..."
    )
    message = models.TextField(
        "Lời nhắn",
        blank=True,
        help_text="Lời mời từ đội trưởng/ban quản lý"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Chiêu mộ Huấn luyện viên"
        verbose_name_plural = "Chiêu mộ Huấn luyện viên"
    
    def __str__(self):
        return f"{self.team.name} chiêu mộ HLV {self.coach.full_name}"


# === MODEL MỚI: PLAYER TEAM EXIT ===
class PlayerTeamExit(models.Model):
    """
    Lưu trữ yêu cầu rời đội của cầu thủ.
    """
    class ExitType(models.TextChoices):
        IMMEDIATE = 'IMMEDIATE', 'Rời ngay lập tức'
        END_SEASON = 'END_SEASON', 'Rời cuối mùa giải'
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Chờ xác nhận'
        APPROVED = 'APPROVED', 'Đã duyệt'
        REJECTED = 'REJECTED', 'Từ chối'
        CANCELLED = 'CANCELLED', 'Đã hủy'
    
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name='exit_requests',
        verbose_name="Cầu thủ"
    )
    current_team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='exit_requests_received',
        verbose_name="Đội hiện tại"
    )
    exit_type = models.CharField(
        "Loại rời đội",
        max_length=15,
        choices=ExitType.choices,
        default=ExitType.IMMEDIATE
    )
    reason = models.TextField(
        "Lý do rời đội",
        blank=True,
        help_text="Giải thích lý do muốn rời đội (không bắt buộc)"
    )
    status = models.CharField(
        "Trạng thái",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Thông tin xử lý
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_exit_requests',
        verbose_name="Người xử lý"
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(
        "Ghi chú của đội trưởng",
        blank=True,
        help_text="Ghi chú từ đội trưởng về việc xử lý yêu cầu"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Yêu cầu Rời đội"
        verbose_name_plural = "Yêu cầu Rời đội"
        # Một cầu thủ chỉ có thể có 1 yêu cầu rời đội đang chờ xử lý
        constraints = [
            models.UniqueConstraint(
                fields=['player', 'status'],
                condition=models.Q(status='PENDING'),
                name='unique_pending_exit_request_per_player'
            )
        ]
    
    def __str__(self):
        return f"{self.player.full_name} yêu cầu rời {self.current_team.name} ({self.get_status_display()})"
    
    def clean(self):
        """Validation cho model"""
        if self.player.team != self.current_team:
            raise ValidationError("Cầu thủ không thuộc đội này.")
        
        # Kiểm tra không có yêu cầu rời đội đang chờ xử lý
        if self.status == 'PENDING' and not self.pk:
            existing = PlayerTeamExit.objects.filter(
                player=self.player,
                status='PENDING'
            )
            if existing.exists():
                raise ValidationError("Cầu thủ đã có yêu cầu rời đội đang chờ xử lý.")
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)