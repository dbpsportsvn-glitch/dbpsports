from django.core.management.base import BaseCommand
from shop.models import PaymentMethod, EWalletAccount


class Command(BaseCommand):
    help = 'Setup e-wallet payment method'

    def handle(self, *args, **options):
        print('Creating e-wallet payment method...')
        
        # Create or get payment method for e-wallet
        payment_method, created = PaymentMethod.objects.get_or_create(
            payment_type='e_wallet',
            defaults={
                'name': 'Vi dien tu',
                'description': 'Thanh toan qua Momo, ZaloPay, VNPay',
                'icon': 'fas fa-wallet',
                'is_active': True,
                'order': 2,
            }
        )
        
        if created:
            print(f'[OK] Created payment method: {payment_method.name}')
        else:
            print(f'[INFO] Payment method already exists: {payment_method.name}')
        
        # Create sample e-wallets
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
                print(f'  [OK] Created e-wallet: {ewallet.wallet_name}')
                created_count += 1
            else:
                print(f'  [INFO] E-wallet already exists: {ewallet.wallet_name}')
        
        print(f'\n[DONE] Created {created_count} new e-wallets.')
        print('\nNEXT STEPS:')
        print('  1. Go to Django Admin (/admin/)')
        print('  2. Navigate to Shop > E-Wallet Account')
        print('  3. Upload QR codes for each wallet')
        print('  4. Update account info\n')

