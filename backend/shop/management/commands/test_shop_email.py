from django.core.management.base import BaseCommand
from shop.models import Order
from shop.email_service import send_order_emails, send_customer_order_email, send_admin_order_email


class Command(BaseCommand):
    help = 'Test email service moi - don gian va hieu qua'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-id',
            type=int,
            help='ID cua don hang can test (neu khong co se lay don hang moi nhat)',
        )
        parser.add_argument(
            '--customer-only',
            action='store_true',
            help='Chi gui email cho khach hang',
        )
        parser.add_argument(
            '--admin-only',
            action='store_true',
            help='Chi gui email cho admin',
        )

    def handle(self, *args, **options):
        print("\n" + "=" * 70)
        print("TEST EMAIL SERVICE MOI - XAY LAI TU DAU")
        print("=" * 70 + "\n")
        
        # Lay don hang
        order_id = options.get('order_id')
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                print(f"[ERROR] Khong tim thay don hang ID {order_id}")
                return
        else:
            order = Order.objects.order_by('-created_at').first()
            if not order:
                print("[ERROR] Khong tim thay don hang nao")
                return
        
        print(f"Don hang: {order.order_number}")
        print(f"Khach hang: {order.customer_name}")
        print(f"Email: {order.customer_email}")
        print(f"Tong tien: {order.total_amount:,.0f}d")
        print(f"Ngay dat: {order.created_at.strftime('%d/%m/%Y %H:%M')}")
        print("")
        
        # Gui email theo option
        if options.get('customer_only'):
            print("CHI GUI EMAIL CHO KHACH HANG...")
            print("-" * 70)
            success = send_customer_order_email(order.id)
            if success:
                print("\n[SUCCESS] Email da duoc gui thanh cong!")
            else:
                print("\n[ERROR] Co loi khi gui email")
                
        elif options.get('admin_only'):
            print("CHI GUI EMAIL CHO ADMIN...")
            print("-" * 70)
            success = send_admin_order_email(order.id)
            if success:
                print("\n[SUCCESS] Email da duoc gui thanh cong!")
            else:
                print("\n[ERROR] Co loi khi gui email")
                
        else:
            print("GUI EMAIL CHO CA KHACH HANG VA ADMIN...")
            print("-" * 70)
            success = send_order_emails(order.id)
            if success:
                print("\n[SUCCESS] Tat ca email da duoc gui thanh cong!")
            else:
                print("\n[ERROR] Co loi khi gui email")
        
        print("\n" + "=" * 70)
        print("KIEM TRA:")
        print("  1. Hop thu den cua khach hang: " + order.customer_email)
        print("  2. Thu muc Spam/Junk")
        print("  3. Email admin")
        print("=" * 70 + "\n")

