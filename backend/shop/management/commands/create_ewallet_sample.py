from django.core.management.base import BaseCommand
from shop.models import PaymentMethod, EWalletAccount


class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho ví điện tử'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Đang tạo dữ liệu mẫu cho ví điện tử...'))
        
        # Tạo hoặc lấy payment method cho ví điện tử
        payment_method, created = PaymentMethod.objects.get_or_create(
            payment_type='e_wallet',
            defaults={
                'name': 'Ví điện tử',
                'description': 'Thanh toán qua Momo, ZaloPay, VNPay',
                'icon': 'fas fa-wallet',
                'is_active': True,
                'order': 2,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Đã tạo payment method: {payment_method.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'⚠ Payment method đã tồn tại: {payment_method.name}'))
        
        # Tạo các ví điện tử mẫu
        ewallets_data = [
            {
                'wallet_name': 'Momo',
                'account_info': '0901234567',
                'order': 1,
            },
            {
                'wallet_name': 'ZaloPay',
                'account_info': '0901234567',
                'order': 2,
            },
            {
                'wallet_name': 'VNPay',
                'account_info': '0901234567',
                'order': 3,
            },
        ]
        
        created_count = 0
        for ewallet_data in ewallets_data:
            ewallet, created = EWalletAccount.objects.get_or_create(
                payment_method=payment_method,
                wallet_name=ewallet_data['wallet_name'],
                defaults=ewallet_data
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Đã tạo ví điện tử: {ewallet.wallet_name}'))
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING(f'  ⚠ Ví điện tử đã tồn tại: {ewallet.wallet_name}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Hoàn thành! Đã tạo {created_count} ví điện tử mới.'))
        self.stdout.write(self.style.WARNING('\n⚠ LƯU Ý:'))
        self.stdout.write('  1. Vào Django Admin (/admin/) để cập nhật thông tin tài khoản chính xác')
        self.stdout.write('  2. Upload mã QR cho từng ví điện tử')
        self.stdout.write('  3. Đường dẫn: Admin > Shop > Ví điện tử (E-Wallet Account)\n')

