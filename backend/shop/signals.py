"""
Shop signals - Tự động gửi email khi có thay đổi
"""

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Order
from .email_service import send_payment_confirmed_email
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Order)
def order_payment_status_changed(sender, instance, **kwargs):
    """
    Signal: Gửi email cảm ơn khi admin xác nhận đã thanh toán
    Chỉ gửi khi payment_status thay đổi từ 'pending' -> 'paid'
    """
    if instance.pk:  # Chỉ check nếu đơn hàng đã tồn tại (update, không phải create)
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            
            # Kiểm tra xem payment_status có thay đổi thành 'paid' không
            if old_instance.payment_status != 'paid' and instance.payment_status == 'paid':
                logger.info(f"Payment status changed to 'paid' for order {instance.order_number}")
                
                # Gửi email cảm ơn cho khách hàng
                try:
                    send_payment_confirmed_email(instance.id)
                    logger.info(f"Payment confirmation email sent for order {instance.order_number}")
                except Exception as e:
                    logger.error(f"Error sending payment confirmation email: {str(e)}")
                    # Không raise để không ảnh hưởng đến việc lưu đơn hàng
                    
        except Order.DoesNotExist:
            # Đơn hàng mới, không làm gì
            pass

