from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages # <--- THÊM DÒNG NÀY

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