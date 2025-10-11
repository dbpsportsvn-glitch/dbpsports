from django.core.management.base import BaseCommand
from shop.models import Order
from shop.tasks import send_order_confirmation_email, send_order_notification_admin_email
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test gửi email cho đơn hàng mới nhất'

    def handle(self, *args, **options):
        print("=" * 70)
        print("TEST EMAIL DON HANG - CODE MOI")
        print("=" * 70)
        
        # Lay don hang moi nhat
        latest_order = Order.objects.order_by('-created_at').first()
        
        if not latest_order:
            print('[ERROR] Khong tim thay don hang nao')
            return
        
        print(f"\nDon hang: {latest_order.order_number}")
        print(f"Khach hang: {latest_order.customer_name}")
        print(f"Email: {latest_order.customer_email}")
        print(f"Tong tien: {latest_order.total_amount:,.0f}d")
        
        print("\n" + "-" * 70)
        print("Dang gui email cho KHACH HANG...")
        print("-" * 70)
        
        try:
            send_order_confirmation_email(latest_order.id)
            print('\n[SUCCESS] DA GUI EMAIL CHO KHACH HANG!')
            print(f"   -> Gui den: {latest_order.customer_email}")
        except Exception as e:
            print(f'\n[ERROR] LOI: {str(e)}')
            import traceback
            traceback.print_exc()
        
        print("\n" + "-" * 70)
        print("Dang gui email cho ADMIN...")
        print("-" * 70)
        
        try:
            send_order_notification_admin_email(latest_order.id)
            print('\n[SUCCESS] DA GUI EMAIL CHO ADMIN!')
        except Exception as e:
            print(f'\n[ERROR] LOI: {str(e)}')
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 70)
        print("Kiem tra:")
        print("   1. Hop thu den cua khach hang")
        print("   2. Thu muc Spam/Junk")
        print("   3. Email co ca plain text va HTML")
        print("=" * 70)

