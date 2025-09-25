from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages # <--- THÊM DÒNG NÀY
from .models import Notification
from django.urls import reverse

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
        print(f"Đã gửi email thông báo: '{subject}' đến {recipient_list}")
        return True # <-- THÊM DÒNG NÀY: Báo hiệu thành công

    except Exception as e:
        error_message = f"Lỗi nghiêm trọng khi gửi email '{subject}': {e}"
        print(error_message)
        if request:
            # Làm cho thông báo lỗi cụ thể và hữu ích hơn
            messages.error(request, f"Không thể gửi email đến {recipient_list}. Lỗi: {e}")
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