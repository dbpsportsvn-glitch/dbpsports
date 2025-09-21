from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages # <--- THÊM DÒNG NÀY

# === THAY ĐỔI: Thêm "request=None" vào tham số của hàm ===
def send_notification_email(subject, template_name, context, recipient_list, request=None):
    """
    Một hàm đa năng để gửi email thông báo.
    Có thể hiển thị message báo lỗi nếu có request.
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
        # Nếu có request, hiển thị message thành công (tùy chọn)
        # if request:
        #     messages.success(request, f"Đã gửi email '{subject}' thành công.")

    except Exception as e:
        error_message = f"Lỗi nghiêm trọng khi gửi email '{subject}': {e}"
        print(error_message)
        # === THAY ĐỔI: Hiển thị lỗi trên giao diện nếu có request ===
        if request:
            messages.error(request, error_message)