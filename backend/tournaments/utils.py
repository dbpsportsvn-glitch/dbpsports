# tournaments/utils.py

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string


def send_notification_email(subject, template_name, context, recipient_list):
    """
    Một hàm đa năng để gửi email thông báo.
    Giờ có thể gửi đến một danh sách người nhận tùy chỉnh.
    """
    try:
        html_message = render_to_string(template_name, context)

        send_mail(
            subject=subject,
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_list, # <-- Sử dụng danh sách người nhận mới
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Đã gửi email thông báo: '{subject}' đến {recipient_list}")
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")