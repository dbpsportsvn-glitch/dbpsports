from django.core.management.base import BaseCommand
from shop.models import PaymentMethod, BankAccount, EWalletAccount, PaymentStep, ContactInfo, PaymentPolicy

class Command(BaseCommand):
    help = 'Create sample payment data'

    def handle(self, *args, **options):
        self.stdout.write('Creating payment data...')
        
        # 1. Create PaymentMethods
        bank_method, created = PaymentMethod.objects.get_or_create(
            name="Chuyển khoản ngân hàng",
            defaults={
                'payment_type': 'bank_transfer',
                'description': 'Thanh toán qua chuyển khoản ngân hàng - An toàn và nhanh chóng',
                'icon': 'fas fa-university',
                'order': 1,
                'is_active': True
            }
        )
        self.stdout.write(f'PaymentMethod: {bank_method.name} - {"created" if created else "already exists"}')
        
        ewallet_method, created = PaymentMethod.objects.get_or_create(
            name="Ví điện tử",
            defaults={
                'payment_type': 'e_wallet',
                'description': 'Thanh toán qua các ví điện tử phổ biến',
                'icon': 'fas fa-mobile-alt',
                'order': 2,
                'is_active': True
            }
        )
        self.stdout.write(f'PaymentMethod: {ewallet_method.name} - {"created" if created else "already exists"}')
        
        cod_method, created = PaymentMethod.objects.get_or_create(
            name="COD (Thanh toán khi nhận hàng)",
            defaults={
                'payment_type': 'cod',
                'description': 'Thanh toán bằng tiền mặt khi nhận hàng',
                'icon': 'fas fa-truck',
                'order': 3,
                'is_active': True
            }
        )
        self.stdout.write(f'PaymentMethod: {cod_method.name} - {"created" if created else "already exists"}')
        
        # 2. Create BankAccounts
        banks = [
            {'bank_name': 'Vietcombank', 'account_holder': 'DBP Sports', 'account_number': '1234567890', 'branch': 'Hà Nội', 'order': 1},
            {'bank_name': 'Techcombank', 'account_holder': 'DBP Sports', 'account_number': '0987654321', 'branch': 'TP.HCM', 'order': 2},
            {'bank_name': 'BIDV', 'account_holder': 'DBP Sports', 'account_number': '1122334455', 'branch': 'Đà Nẵng', 'order': 3}
        ]
        
        for bank_data in banks:
            bank_account, created = BankAccount.objects.get_or_create(
                payment_method=bank_method,
                bank_name=bank_data['bank_name'],
                defaults={
                    'account_holder': bank_data['account_holder'],
                    'account_number': bank_data['account_number'],
                    'branch': bank_data['branch'],
                    'order': bank_data['order'],
                    'is_active': True
                }
            )
            self.stdout.write(f'BankAccount: {bank_account.bank_name} - {bank_account.account_number} {"(created)" if created else "(already exists)"}')
        
        # 3. Create EWalletAccounts
        ewallets = [
            {'wallet_name': 'PayPal', 'account_info': 'dbpsports@gmail.com', 'order': 1},
            {'wallet_name': 'MoMo', 'account_info': '0901234567', 'order': 2},
            {'wallet_name': 'ZaloPay', 'account_info': '0901234567', 'order': 3}
        ]
        
        for ewallet_data in ewallets:
            ewallet_account, created = EWalletAccount.objects.get_or_create(
                payment_method=ewallet_method,
                wallet_name=ewallet_data['wallet_name'],
                defaults={
                    'account_info': ewallet_data['account_info'],
                    'order': ewallet_data['order'],
                    'is_active': True
                }
            )
            self.stdout.write(f'EWalletAccount: {ewallet_account.wallet_name} - {ewallet_account.account_info} {"(created)" if created else "(already exists)"}')
        
        # 4. Create PaymentSteps
        steps = [
            {'title': 'Chọn sản phẩm', 'description': 'Duyệt và chọn sản phẩm bạn muốn mua từ cửa hàng', 'order': 1},
            {'title': 'Thêm vào giỏ hàng', 'description': 'Thêm sản phẩm vào giỏ hàng và kiểm tra thông tin', 'order': 2},
            {'title': 'Chọn phương thức thanh toán', 'description': 'Chọn phương thức thanh toán phù hợp với bạn', 'order': 3},
            {'title': 'Xác nhận đơn hàng', 'description': 'Kiểm tra và xác nhận thông tin đơn hàng', 'order': 4},
            {'title': 'Thanh toán', 'description': 'Thực hiện thanh toán theo phương thức đã chọn', 'order': 5},
            {'title': 'Nhận hàng', 'description': 'Nhận hàng và kiểm tra chất lượng sản phẩm', 'order': 6}
        ]
        
        for step_data in steps:
            step, created = PaymentStep.objects.get_or_create(
                title=step_data['title'],
                defaults={
                    'description': step_data['description'],
                    'order': step_data['order'],
                    'is_active': True
                }
            )
            self.stdout.write(f'PaymentStep: {step.order}. {step.title} {"(created)" if created else "(already exists)"}')
        
        # 5. Create ContactInfo
        contacts = [
            {'contact_type': 'phone', 'name': 'Hotline', 'value': '1900 1234', 'description': '8:00 - 22:00 (Tất cả các ngày)', 'icon': 'fas fa-phone', 'order': 1},
            {'contact_type': 'messenger', 'name': 'Facebook Messenger', 'value': 'm.me/dbpsports', 'description': 'Trong vòng 5 phút', 'icon': 'fab fa-facebook-messenger', 'order': 2},
            {'contact_type': 'email', 'name': 'Email', 'value': 'support@dbpsports.com', 'description': 'Trong vòng 24 giờ', 'icon': 'fas fa-envelope', 'order': 3},
            {'contact_type': 'zalo', 'name': 'Zalo', 'value': '0901234567', 'description': 'Trong vòng 10 phút', 'icon': 'fab fa-zalo', 'order': 4}
        ]
        
        for contact_data in contacts:
            contact, created = ContactInfo.objects.get_or_create(
                contact_type=contact_data['contact_type'],
                name=contact_data['name'],
                defaults={
                    'value': contact_data['value'],
                    'description': contact_data['description'],
                    'icon': contact_data['icon'],
                    'order': contact_data['order'],
                    'is_active': True
                }
            )
            self.stdout.write(f'ContactInfo: {contact.name} - {contact.value} {"(created)" if created else "(already exists)"}')
        
        # 6. Create PaymentPolicy
        policies = [
            {
                'title': 'Lưu Ý Quan Trọng',
                'content': '''• Vui lòng chuyển khoản đúng số tiền và ghi rõ nội dung chuyển khoản
• Sau khi chuyển khoản, vui lòng gửi ảnh biên lai qua Zalo/Facebook để xác nhận
• Đơn hàng sẽ được xử lý trong vòng 24 giờ sau khi xác nhận thanh toán
• Chúng tôi chỉ giao hàng đến địa chỉ đã đăng ký trong đơn hàng
• Vui lòng kiểm tra hàng trước khi thanh toán (đối với COD)''',
                'policy_type': 'warning',
                'icon': 'fas fa-exclamation-triangle',
                'order': 1
            },
            {
                'title': 'Chính Sách Đổi Trả',
                'content': '''• Đổi trả miễn phí: Trong vòng 7 ngày kể từ ngày nhận hàng
• Điều kiện: Sản phẩm còn nguyên tem, chưa sử dụng
• Hoàn tiền: 100% giá trị sản phẩm (trừ phí vận chuyển)
• Bảo hành: Theo chính sách của từng nhà sản xuất''',
                'policy_type': 'success',
                'icon': 'fas fa-shield-alt',
                'order': 2
            }
        ]
        
        for policy_data in policies:
            policy, created = PaymentPolicy.objects.get_or_create(
                title=policy_data['title'],
                defaults={
                    'content': policy_data['content'],
                    'policy_type': policy_data['policy_type'],
                    'icon': policy_data['icon'],
                    'order': policy_data['order'],
                    'is_active': True
                }
            )
            self.stdout.write(f'PaymentPolicy: {policy.title} {"(created)" if created else "(already exists)"}')
        
        self.stdout.write(self.style.SUCCESS('Hoan thanh! Du lieu thanh toan da duoc tao thanh cong.'))
        self.stdout.write('Ban co the vao Django Admin de chinh sua thong tin.')
