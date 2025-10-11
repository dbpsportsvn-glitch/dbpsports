"""
Email service for shop orders - Simple and reliable
Learning from tournaments email system that works perfectly
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Order
import logging

logger = logging.getLogger(__name__)


def send_customer_order_email(order_id):
    """
    Gửi email xác nhận đơn hàng cho khách hàng
    Sử dụng phương pháp giống tournament email (hoạt động tốt)
    """
    try:
        order = Order.objects.get(id=order_id)
        
        # Render HTML template
        html_message = render_to_string('shop/emails/customer_order_confirmation.html', {
            'order': order
        })
        
        # Gửi email - ĐÚNG NHƯ TOURNAMENT
        send_mail(
            subject=f'Xác nhận đơn hàng #{order.order_number} - DBP Sports',
            message='',  # Plain text empty - giống tournament
            from_email=settings.EMAIL_HOST_USER,  # Dùng EMAIL_HOST_USER - giống tournament
            recipient_list=[order.customer_email],
            html_message=html_message,
            fail_silently=False,  # Không im lặng - để thấy lỗi
        )
        
        logger.info(f"[OK] Customer email sent to {order.customer_email} for order {order.order_number}")
        print(f"[OK] Da gui email xac nhan cho khach hang: {order.customer_email}")
        return True
        
    except Order.DoesNotExist:
        logger.error(f"[ERROR] Order {order_id} not found")
        print(f"[ERROR] Khong tim thay don hang {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] Error sending customer email for order {order_id}: {str(e)}")
        print(f"[ERROR] Loi gui email cho khach hang: {str(e)}")
        import traceback
        traceback.print_exc()
        raise  # Raise để thấy lỗi rõ ràng


def send_admin_order_email(order_id):
    """
    Gửi email thông báo đơn hàng mới cho admin
    Sử dụng phương pháp giống tournament email
    """
    try:
        order = Order.objects.get(id=order_id)
        
        # Get admin emails
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.ADMIN_EMAIL])
        if not admin_emails or admin_emails == ['admin@example.com']:
            # Nếu không có admin email, dùng EMAIL_HOST_USER
            admin_emails = [settings.EMAIL_HOST_USER]
        
        # Render HTML template
        html_message = render_to_string('shop/emails/admin_order_notification.html', {
            'order': order
        })
        
        # Gửi email - ĐÚNG NHƯ TOURNAMENT
        send_mail(
            subject=f'🔔 Đơn hàng mới #{order.order_number} - {order.customer_name}',
            message='',  # Plain text empty
            from_email=settings.EMAIL_HOST_USER,  # Dùng EMAIL_HOST_USER
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"[OK] Admin email sent for order {order.order_number}")
        print(f"[OK] Da gui email thong bao cho admin")
        return True
        
    except Order.DoesNotExist:
        logger.error(f"[ERROR] Order {order_id} not found")
        print(f"[ERROR] Khong tim thay don hang {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] Error sending admin email for order {order_id}: {str(e)}")
        print(f"[ERROR] Loi gui email cho admin: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def send_payment_confirmed_email(order_id):
    """
    Gửi email cảm ơn khi admin xác nhận đã thanh toán
    """
    try:
        order = Order.objects.get(id=order_id)
        
        # Render HTML template
        html_message = render_to_string('shop/emails/payment_confirmed.html', {
            'order': order
        })
        
        # Gửi email - ĐÚNG NHƯ TOURNAMENT
        send_mail(
            subject=f'✓ Xác nhận thanh toán #{order.order_number} - DBP Sports',
            message='',  # Plain text empty
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[order.customer_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"[OK] Payment confirmation email sent to {order.customer_email} for order {order.order_number}")
        print(f"[OK] Da gui email cam on cho khach hang: {order.customer_email}")
        return True
        
    except Order.DoesNotExist:
        logger.error(f"[ERROR] Order {order_id} not found")
        print(f"[ERROR] Khong tim thay don hang {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] Error sending payment confirmation email for order {order_id}: {str(e)}")
        print(f"[ERROR] Loi gui email cam on: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def send_order_emails(order_id):
    """
    Gửi cả 2 email: cho khách hàng và admin
    Wrapper function để gọi từ views
    """
    try:
        print(f"\n{'='*60}")
        print(f"SENDING EMAILS FOR ORDER {order_id}")
        print(f"{'='*60}\n")
        
        # Gửi cho khách hàng
        print("1. Sending customer email...")
        customer_success = send_customer_order_email(order_id)
        
        # Gửi cho admin
        print("\n2. Sending admin email...")
        admin_success = send_admin_order_email(order_id)
        
        print(f"\n{'='*60}")
        print(f"RESULT: Customer={customer_success}, Admin={admin_success}")
        print(f"{'='*60}\n")
        
        return customer_success and admin_success
        
    except Exception as e:
        logger.error(f"[ERROR] Error in send_order_emails: {str(e)}")
        print(f"[ERROR] Loi chung: {str(e)}")
        # Không raise - để đơn hàng vẫn được tạo thành công
        return False

