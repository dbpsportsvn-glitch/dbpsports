from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Test gửi email với template mới'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='thienhamedia2024@gmail.com',
            help='Email địa chỉ nhận (mặc định: thienhamedia2024@gmail.com)'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['shop', 'tournament', 'payment', 'organization', 'all'],
            default='all',
            help='Loại email cần test (mặc định: all)'
        )

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        
        self.stdout.write(
            self.style.SUCCESS(f'Bat dau test gui email den: {email}')
        )
        
        if email_type in ['shop', 'all']:
            self.test_shop_customer_email(email)
            
        if email_type in ['tournament', 'all']:
            self.test_tournament_announcement(email)
            
        if email_type in ['payment', 'all']:
            self.test_payment_confirmed(email)
            
        if email_type in ['organization', 'all']:
            self.test_organization_approved(email)

    def test_shop_customer_email(self, email):
        """Test email xác nhận đơn hàng cho khách hàng"""
        
        # Mock data cho đơn hàng
        order_data = {
            'order': {
                'order_number': 'DBP2025001',
                'customer_name': 'Nguyễn Văn A',
                'customer_email': email,
                'customer_phone': '0123456789',
                'created_at': timezone.now(),
                'get_status_display': 'Đang xử lý',
                'get_payment_method_display': 'Chuyển khoản',
                'shipping_address': '123 Đường ABC',
                'shipping_district': 'Quận 1',
                'shipping_city': 'TP.HCM',
                'shipping_fee': 30000,
                'total_amount': 450000,
                'subtotal': 420000,
                'items': [
                    {
                        'product': {'name': 'Giày bóng đá Nike'},
                        'quantity': 1,
                        'price': 420000,
                        'total_price': 420000
                    }
                ]
            }
        }
        
        # Render template
        html_message = render_to_string('shop/emails/customer_order_confirmation.html', order_data)
        
        # Gửi email
        try:
            send_mail(
                subject='✅ Xác nhận đơn hàng #DBP2025001 - DBP Sports',
                message='',
                from_email='DBP Sports <noreply@dbpsports.com>',
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS('Da gui email xac nhan don hang thanh cong!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Loi gui email: {e}')
            )

    def test_tournament_announcement(self, email):
        """Test email thông báo giải đấu"""
        
        # Mock data cho thông báo
        announcement_data = {
            'announcement': {
                'title': 'Thông báo quan trọng về lịch thi đấu',
                'content': 'Kính gửi các đội trưởng,\n\nBan tổ chức xin thông báo lịch thi đấu vòng loại sẽ được cập nhật vào ngày mai.\n\nVui lòng theo dõi website để cập nhật thông tin mới nhất.\n\nTrân trọng.',
                'tournament': {'name': 'Giải bóng đá phong trào 2025'},
                'created_at': timezone.now()
            }
        }
        
        # Render template
        html_message = render_to_string('tournaments/emails/announcement_notification.html', announcement_data)
        
        # Gửi email
        try:
            send_mail(
                subject='📢 Thông báo mới từ giải Giải bóng đá phong trào 2025 - DBP Sports',
                message='',
                from_email='DBP Sports <noreply@dbpsports.com>',
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS('Da gui email thông báo giải đấu thành công!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Loi gui email: {e}')
            )

    def test_payment_confirmed(self, email):
        """Test email xác nhận thanh toán"""
        
        # Mock data cho đội bóng
        team_data = {
            'team': {
                'name': 'Đội bóng ABC',
                'tournament': {
                    'name': 'Giải bóng đá phong trào 2025',
                    'registration_fee': 500000
                },
                'payment_proof_uploaded_at': timezone.now()
            }
        }
        
        # Render template
        html_message = render_to_string('tournaments/emails/payment_confirmed.html', team_data)
        
        # Gửi email
        try:
            send_mail(
                subject='🎉 Xác nhận thanh toán thành công - Giải bóng đá phong trào 2025 - DBP Sports',
                message='',
                from_email='DBP Sports <noreply@dbpsports.com>',
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS('Da gui email xác nhận thanh toán thành công!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Loi gui email: {e}')
            )

    def test_organization_approved(self, email):
        """Test email đơn vị được duyệt"""
        
        # Mock data cho đơn vị
        org_data = {
            'organization': {
                'name': 'CLB Thể thao ABC',
                'approved_at': timezone.now()
            },
            'owner': {
                'get_full_name': 'Nguyễn Văn B',
                'username': 'nguyenvanb',
                'email': email
            }
        }
        
        # Render template
        html_message = render_to_string('organizations/emails/organization_approved.html', org_data)
        
        # Gửi email
        try:
            send_mail(
                subject='🎉 Đơn vị tổ chức đã được duyệt - DBP Sports',
                message='',
                from_email='DBP Sports <noreply@dbpsports.com>',
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            self.stdout.write(
                self.style.SUCCESS('Da gui email đơn vị được duyệt thành công!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Loi gui email: {e}')
            )
