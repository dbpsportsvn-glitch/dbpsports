from django.core.management.base import BaseCommand
from shop.models import PaymentMethod


class Command(BaseCommand):
    help = 'Fix e-wallet payment method name with Vietnamese accents'

    def handle(self, *args, **options):
        try:
            payment_method = PaymentMethod.objects.get(payment_type='e_wallet')
            payment_method.name = 'Ví điện tử'
            payment_method.description = 'Thanh toán qua Momo, ZaloPay, VNPay'
            payment_method.save()
            
            self.stdout.write(self.style.SUCCESS(f'Updated payment method name to: {payment_method.name}'))
        except PaymentMethod.DoesNotExist:
            self.stdout.write(self.style.ERROR('E-wallet payment method not found!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))

