from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages # <--- THÊM DÒNG NÀY
from .models import Notification
from django.urls import reverse
import math
from django.contrib.auth.models import User  

# === THAY ĐỔI: Thêm "request=None" vào tham số của hàm ===
def send_notification_email(subject, template_name, context, recipient_list, request=None):
    """
    Một hàm đa năng để gửi email thông báo.
    Có thể hiển thị message báo lỗi nếu có request.
    Trả về True nếu gửi thành công, False nếu có lỗi.
    """
    try:
        html_message = render_to_string(template_name, context)

        send_mail(
            subject=subject,
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Email notification sent: '{subject}' to {recipient_list}")
        return True # <-- THÊM DÒNG NÀY: Báo hiệu thành công

    except Exception as e:
        error_message = f"Critical error sending email '{subject}': {e}"
        print(error_message)
        if request:
            # Làm cho thông báo lỗi cụ thể và hữu ích hơn
            messages.error(request, f"Cannot send email to {recipient_list}. Error: {e}")
        return False # <-- THÊM DÒNG NÀY: Báo hiệu thất bại


def send_schedule_notification(tournament, notification_type, title, message, url_name):
    """
    Gửi thông báo liên quan đến lịch thi đấu hoặc bốc thăm đến người dùng.
    """
    # Xác định người dùng cần nhận thông báo dựa trên tùy chọn của họ
    if notification_type == Notification.NotificationType.DRAW_COMPLETE:
        users_to_notify = tournament.followers.filter(profile__notify_draw_results=True)
    elif notification_type == Notification.NotificationType.SCHEDULE_CREATED:
        users_to_notify = tournament.followers.filter(profile__notify_schedule_updates=True)
    else:
        return  # Không gửi nếu không đúng loại

    if not users_to_notify.exists():
        return

    # Xác định tab cần trỏ đến trên trang chi tiết giải đấu
    tab = 'schedule' if notification_type == Notification.NotificationType.SCHEDULE_CREATED else 'teams'
    url = reverse(url_name, kwargs={'pk': tournament.pk}) + f'?tab={tab}#{tab}'

    notifications_to_create = [
        Notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            related_url=url
        )
        for user in users_to_notify
    ]
    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create, ignore_conflicts=True)
        

# Tính giá trị của một phiếu bầu dựa trên công thức logarit để tăng trưởng mượt mà
def get_current_vote_value():
    """
    Tính giá trị của một phiếu bầu dựa trên công thức logarit để tăng trưởng mượt mà.
    """
    user_count = User.objects.count()

    # Tránh lỗi log(0) hoặc log(1)
    if user_count < 2:
        user_count = 2

    # --- CÔNG THỨC LOGARIT ---
    # Bạn có thể điều chỉnh 2 con số này để thay đổi "nền kinh tế"
    base_value = 5000  # Giá trị khởi điểm
    scaling_factor = 2500  # Hệ số ảnh hưởng, số càng lớn giá trị tăng càng nhanh

    # Công thức: vote = base + factor * log(số người dùng)
    vote_value = base_value + (scaling_factor * math.log(user_count))
    
    # Làm tròn đến hàng trăm gần nhất cho số đẹp
    return round(vote_value / 100) * 100


def user_can_manage_team(user, team):
    """
    Kiểm tra xem user có quyền quản lý đội không (captain hoặc coach).
    
    Args:
        user: User object
        team: Team object
    
    Returns:
        bool: True nếu user là captain hoặc coach của đội, False otherwise
    """
    if not user or not user.is_authenticated:
        return False
    
    # Kiểm tra nếu là đội trưởng
    if team.captain == user:
        return True
    
    # Kiểm tra nếu là huấn luyện viên
    if team.coach and team.coach.user == user:
        return True
    
    return False