from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation_email_task(order_id):
    """Celery task để gửi email xác nhận đơn hàng cho khách hàng"""
    try:
        order = Order.objects.get(id=order_id)
        
        # Render email template
        html_content = render_to_string('shop/emails/order_confirmation.html', {
            'order': order,
            'request': type('obj', (object,), {
                'scheme': 'http',
                'get_host': lambda: 'localhost:8000'
            })
        })
        
        # Create email
        subject = f'Xác nhận đơn hàng #{order.order_number} - DBP Sports'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [order.customer_email]
        
        # Create plain text version
        text_content = f"""
Xin chào {order.customer_name},

Cảm ơn bạn đã đặt hàng tại DBP Sports!

Thông tin đơn hàng:
- Mã đơn hàng: {order.order_number}
- Ngày đặt: {order.created_at.strftime('%d/%m/%Y %H:%M')}
- Tổng tiền: {order.total_amount:,.0f}đ
- Trạng thái: {order.get_status_display()}

Chúng tôi sẽ xử lý đơn hàng của bạn trong thời gian sớm nhất.

Trân trọng,
Đội ngũ DBP Sports
        """
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Order confirmation email sent to {order.customer_email} for order {order.order_number}")
        return f"Email sent to {order.customer_email}"
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return f"Order {order_id} not found"
    except Exception as e:
        logger.error(f"Error sending order confirmation email: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_order_notification_admin_email_task(order_id):
    """Celery task để gửi email thông báo đơn hàng mới cho admin"""
    try:
        order = Order.objects.get(id=order_id)
        
        # Get admin emails from settings or use default
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.DEFAULT_FROM_EMAIL])
        
        # Render email template
        html_content = render_to_string('shop/emails/order_notification_admin.html', {
            'order': order,
            'request': type('obj', (object,), {
                'scheme': 'http',
                'get_host': lambda: 'localhost:8000'
            })
        })
        
        # Create email
        subject = f'🔔 Đơn hàng mới #{order.order_number} - {order.customer_name}'
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = admin_emails
        
        # Create plain text version
        text_content = f"""
Đơn hàng mới cần xử lý!

Thông tin đơn hàng:
- Mã đơn hàng: {order.order_number}
- Khách hàng: {order.customer_name}
- Email: {order.customer_email}
- Số điện thoại: {order.customer_phone}
- Tổng tiền: {order.total_amount:,.0f}đ
- Phương thức thanh toán: {order.payment_method}
- Ngày đặt: {order.created_at.strftime('%d/%m/%Y %H:%M')}

Vui lòng truy cập admin để xử lý đơn hàng.
        """
        
        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        
        logger.info(f"Admin notification email sent for order {order.order_number}")
        return f"Admin email sent for order {order.order_number}"
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return f"Order {order_id} not found"
    except Exception as e:
        logger.error(f"Error sending admin notification email: {str(e)}")
        return f"Error: {str(e)}"
