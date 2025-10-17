"""
Email service for Organization Shop orders
Tương tự như shop chính nhưng gửi cho BTC và khách hàng
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .organization_models import OrganizationOrder
from organizations.models import Organization
import logging

logger = logging.getLogger(__name__)


def send_org_customer_order_email(order_id):
    """
    Gửi email xác nhận đơn hàng cho khách hàng từ Organization Shop
    """
    try:
        order = OrganizationOrder.objects.get(id=order_id)
        
        # Render HTML template
        html_message = render_to_string('shop/organization/emails/customer_order_confirmation.html', {
            'order': order,
            'organization': order.organization,
            'shop_settings': order.organization.shop_settings
        })
        
        # Gửi email
        send_mail(
            subject=f'Xác nhận đơn hàng #{order.order_number} - {order.organization.name}',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[order.customer_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"[OK] Organization customer email sent to {order.customer_email} for order {order.order_number}")
        print(f"[OK] Da gui email xac nhan cho khach hang: {order.customer_email}")
        return True
        
    except OrganizationOrder.DoesNotExist:
        logger.error(f"[ERROR] Organization Order {order_id} not found")
        print(f"[ERROR] Khong tim thay don hang organization {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] Error sending organization customer email for order {order_id}: {str(e)}")
        print(f"[ERROR] Loi gui email cho khach hang organization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def send_org_admin_order_email(order_id):
    """
    Gửi email thông báo đơn hàng mới cho BTC (Organization)
    """
    try:
        order = OrganizationOrder.objects.get(id=order_id)
        organization = order.organization
        
        # Lấy email của các thành viên BTC
        admin_emails = []
        
        # Lấy email từ shop settings nếu có
        if hasattr(organization, 'shop_settings') and organization.shop_settings.contact_email:
            admin_emails.append(organization.shop_settings.contact_email)
        
        # Lấy email từ các thành viên BTC
        for member in organization.members.all():
            if member.email and member.email not in admin_emails:
                admin_emails.append(member.email)
        
        # Fallback nếu không có email nào
        if not admin_emails:
            admin_emails = [settings.EMAIL_HOST_USER]
        
        # Render HTML template
        html_message = render_to_string('shop/organization/emails/admin_order_notification.html', {
            'order': order,
            'organization': organization,
            'shop_settings': organization.shop_settings
        })
        
        # Gửi email
        send_mail(
            subject=f'🔔 Đơn hàng mới #{order.order_number} - {order.customer_name}',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"[OK] Organization admin email sent for order {order.order_number}")
        print(f"[OK] Da gui email thong bao cho BTC")
        return True
        
    except OrganizationOrder.DoesNotExist:
        logger.error(f"[ERROR] Organization Order {order_id} not found")
        print(f"[ERROR] Khong tim thay don hang organization {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] Error sending organization admin email for order {order_id}: {str(e)}")
        print(f"[ERROR] Loi gui email cho BTC: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def send_org_payment_confirmed_email(order_id):
    """
    Gửi email cảm ơn khi BTC xác nhận đã thanh toán
    """
    try:
        order = OrganizationOrder.objects.get(id=order_id)
        
        # Render HTML template
        html_message = render_to_string('shop/organization/emails/payment_confirmed.html', {
            'order': order,
            'organization': order.organization,
            'shop_settings': order.organization.shop_settings
        })
        
        # Gửi email
        send_mail(
            subject=f'Cảm ơn bạn đã mua hàng! #{order.order_number} - {order.organization.name}',
            message='',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[order.customer_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"[OK] Organization payment confirmation email sent for order {order.order_number}")
        print(f"[OK] Da gui email cam on cho khach hang: {order.customer_email}")
        return True
        
    except OrganizationOrder.DoesNotExist:
        logger.error(f"[ERROR] Organization Order {order_id} not found")
        print(f"[ERROR] Khong tim thay don hang organization {order_id}")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] Error sending organization payment confirmation email for order {order_id}: {str(e)}")
        print(f"[ERROR] Loi gui email cam on organization: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def send_org_order_emails(order_id):
    """
    Gửi cả 2 email: cho khách hàng và BTC
    Wrapper function để gọi từ organization views
    """
    try:
        print(f"\n{'='*60}")
        print(f"SENDING ORGANIZATION SHOP EMAILS FOR ORDER {order_id}")
        print(f"{'='*60}\n")
        
        # Gửi cho khách hàng
        print("1. Sending organization customer email...")
        customer_success = send_org_customer_order_email(order_id)
        
        # Gửi cho BTC
        print("\n2. Sending organization admin email...")
        admin_success = send_org_admin_order_email(order_id)
        
        print(f"\n{'='*60}")
        print(f"RESULT: Customer={customer_success}, Admin={admin_success}")
        print(f"{'='*60}\n")
        
        return customer_success and admin_success
        
    except Exception as e:
        logger.error(f"[ERROR] Error in send_org_order_emails: {str(e)}")
        print(f"[ERROR] Loi chung organization emails: {str(e)}")
        # Không raise - để đơn hàng vẫn được tạo thành công
        return False
