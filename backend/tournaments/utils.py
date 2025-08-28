# tournaments/utils.py

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_notification_email(subject, template_name, context):
    """
    Một hàm đa năng để gửi email thông báo.
    """
    try:
        # Dùng render_to_string để tạo nội dung email từ một file template
        html_message = render_to_string(template_name, context)

        send_mail(
            subject=subject,
            message='', # Bỏ trống vì chúng ta gửi dạng HTML
            from_email=settings.EMAIL_HOST_USER, # Email người gửi (sẽ cấu hình sau)
            recipient_list=[settings.ADMIN_EMAIL], # Gửi đến email của Admin
            html_message=html_message,
            fail_silently=False,
        )
        print(f"Đã gửi email thông báo: {subject}")
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")