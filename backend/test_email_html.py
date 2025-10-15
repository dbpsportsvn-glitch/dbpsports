#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script test để tạo file HTML email template
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')

django.setup()

from django.template.loader import render_to_string
from django.utils import timezone

def create_shop_customer_email():
    """Tạo email xác nhận đơn hàng cho khách hàng"""
    
    # Mock data cho đơn hàng
    order_data = {
        'order': {
            'order_number': 'DBP2025001',
            'customer_name': 'Nguyễn Văn A',
            'customer_email': 'thienhamedia2024@gmail.com',
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
    
    # Lưu vào file
    with open('shop_customer_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: shop_customer_email.html")
    return True

def create_tournament_announcement():
    """Tạo email thông báo giải đấu"""
    
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
    
    # Lưu vào file
    with open('tournament_announcement_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: tournament_announcement_email.html")
    return True

def create_payment_confirmed():
    """Tạo email xác nhận thanh toán"""
    
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
    
    # Lưu vào file
    with open('payment_confirmed_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: payment_confirmed_email.html")
    return True

def create_organization_approved():
    """Tạo email đơn vị được duyệt"""
    
    # Mock data cho đơn vị
    org_data = {
        'organization': {
            'name': 'CLB Thể thao ABC',
            'approved_at': timezone.now()
        },
        'owner': {
            'get_full_name': 'Nguyễn Văn B',
            'username': 'nguyenvanb',
            'email': 'thienhamedia2024@gmail.com'
        }
    }
    
    # Render template
    html_message = render_to_string('organizations/emails/organization_approved.html', org_data)
    
    # Lưu vào file
    with open('organization_approved_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: organization_approved_email.html")
    return True

def create_account_registration():
    """Tạo email xác nhận đăng ký tài khoản"""
    
    # Mock data cho đăng ký
    registration_data = {
        'activate_url': 'http://localhost:8000/accounts/confirm-email/MQ:1abc123def456ghi789/'
    }
    
    # Render template
    html_message = render_to_string('account/email/email_confirmation_message.html', registration_data)
    
    # Lưu vào file
    with open('account_registration_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: account_registration_email.html")
    return True

def create_email_confirmed():
    """Tạo email xác nhận email thành công"""
    
    # Mock data cho xác nhận email
    confirmation_data = {
        'email': 'thienhamedia2024@gmail.com'
    }
    
    # Render template
    html_message = render_to_string('account/email/email_confirmed.html', confirmation_data)
    
    # Lưu vào file
    with open('email_confirmed.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: email_confirmed.html")
    return True

def create_new_team_registration():
    """Tạo email thông báo đội mới đăng ký cho admin"""
    
    # Mock data cho đội mới
    team_data = {
        'team': {
            'name': 'Đội bóng XYZ',
            'captain': {
                'get_full_name': 'Nguyễn Văn C',
                'username': 'nguyenvanc',
                'email': 'captain@example.com'
            },
            'players': {'count': 15},
            'address': '123 Đường DEF, Quận 2',
            'phone': '0987654321'
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 500000,
            'get_format_display': 'Vòng tròn',
            'get_region_display': 'TP.HCM'
        },
        'registration': {
            'registered_at': timezone.now()
        }
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/new_team_registration.html', team_data)
    
    # Lưu vào file
    with open('new_team_registration_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: new_team_registration_email.html")
    return True

def create_new_team_joined():
    """Tạo email thông báo đội mới tham gia cho followers"""
    
    # Mock data cho đội mới tham gia
    team_data = {
        'team': {
            'name': 'Đội bóng XYZ',
            'captain': {
                'get_full_name': 'Nguyễn Văn C',
                'username': 'nguyenvanc',
                'email': 'captain@example.com'
            },
            'players': {'count': 15}
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'get_format_display': 'Vòng tròn',
            'get_region_display': 'TP.HCM',
            'total_teams': 8
        }
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/new_team_joined.html', team_data)
    
    # Lưu vào file
    with open('new_team_joined_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: new_team_joined_email.html")
    return True

def create_payment_rejected():
    """Tạo email thông báo thanh toán bị từ chối"""
    
    # Mock data cho thanh toán bị từ chối
    payment_data = {
        'team': {
            'name': 'Đội bóng ABC',
            'tournament': {
                'name': 'Giải bóng đá phong trào 2025',
                'registration_fee': 500000
            }
        },
        'rejection_reason': 'Hóa đơn không rõ ràng, số tiền không khớp với lệ phí tham gia. Vui lòng kiểm tra lại thông tin chuyển khoản.'
    }
    
    # Render template
    html_message = render_to_string('tournaments/emails/payment_rejected.html', payment_data)
    
    # Lưu vào file
    with open('payment_rejected_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: payment_rejected_email.html")
    return True

def create_transfer_invitation():
    """Tạo email lời mời chuyển nhượng mới"""
    
    # Mock data cho lời mời chuyển nhượng
    transfer_data = {
        'inviting_team': {'name': 'Đội bóng XYZ'},
        'current_team': {'name': 'Đội bóng ABC'},
        'player': {
            'full_name': 'Nguyễn Văn A',
            'get_position_display': 'Tiền đạo',
            'age': 25,
            'market_value': 10000000
        },
        'transfer': {
            'get_transfer_type_display': 'Mua đứt',
            'offer_amount': 15000000,
            'loan_end_date': None,
            'created_at': timezone.now()
        }
    }
    
    # Render template
    html_message = render_to_string('organizations/emails/new_transfer_invitation.html', transfer_data)
    
    # Lưu vào file
    with open('transfer_invitation_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: transfer_invitation_email.html")
    return True

def create_transfer_accepted():
    """Tạo email chuyển nhượng được chấp nhận"""
    
    # Mock data cho chuyển nhượng được chấp nhận
    transfer_data = {
        'inviting_team': {'name': 'Đội bóng XYZ'},
        'current_team': {'name': 'Đội bóng ABC'},
        'player': {
            'full_name': 'Nguyễn Văn A',
            'get_position_display': 'Tiền đạo',
            'age': 25,
            'market_value': 10000000
        },
        'transfer': {
            'get_transfer_type_display': 'Mua đứt',
            'offer_amount': 15000000,
            'loan_end_date': None
        }
    }
    
    # Render template
    html_message = render_to_string('organizations/emails/transfer_accepted_notification.html', transfer_data)
    
    # Lưu vào file
    with open('transfer_accepted_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: transfer_accepted_email.html")
    return True

def create_transfer_rejected():
    """Tạo email chuyển nhượng bị từ chối"""
    
    # Mock data cho chuyển nhượng bị từ chối
    transfer_data = {
        'inviting_team': {'name': 'Đội bóng XYZ'},
        'current_team': {'name': 'Đội bóng ABC'},
        'player': {
            'full_name': 'Nguyễn Văn A',
            'get_position_display': 'Tiền đạo',
            'age': 25,
            'market_value': 10000000
        },
        'transfer': {
            'get_transfer_type_display': 'Mua đứt',
            'offer_amount': 15000000,
            'loan_end_date': None
        }
    }
    
    # Render template
    html_message = render_to_string('organizations/emails/transfer_rejected_notification.html', transfer_data)
    
    # Lưu vào file
    with open('transfer_rejected_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: transfer_rejected_email.html")
    return True

def create_job_status_update():
    """Tạo email cập nhật trạng thái ứng tuyển"""
    
    # Mock data cho cập nhật trạng thái ứng tuyển
    job_data = {
        'job': {
            'title': 'Trọng tài chính',
            'tournament': {'name': 'Giải bóng đá phong trào 2025'}
        },
        'applicant': {
            'get_full_name': 'Nguyễn Văn B',
            'username': 'nguyenvanb',
            'email': 'nguyenvanb@example.com'
        },
        'application': {
            'status': 'APPROVED',
            'get_status_display': 'Được chấp thuận',
            'created_at': timezone.now()
        }
    }
    
    # Render template
    html_message = render_to_string('organizations/emails/application_status_update.html', job_data)
    
    # Lưu vào file
    with open('job_status_update_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: job_status_update_email.html")
    return True

def create_payment_pending_confirmation():
    """Tạo email xác nhận đã nhận hóa đơn thanh toán"""
    
    # Mock data cho xác nhận đã nhận hóa đơn
    payment_data = {
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
    html_message = render_to_string('tournaments/emails/payment_pending_confirmation.html', payment_data)
    
    # Lưu vào file
    with open('payment_pending_confirmation_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("Da tao file: payment_pending_confirmation_email.html")
    return True

def main():
    """Tạo tất cả file HTML email"""
    print("Bat dau tao file HTML email template...")
    print("Cac file se duoc luu trong thu muc hien tai")
    print("-" * 60)
    
    # Tạo các file email
    tests = [
        ("Email xac nhan don hang Shop", create_shop_customer_email),
        ("Email thong bao giai dau", create_tournament_announcement),
        ("Email xac nhan thanh toan", create_payment_confirmed),
        ("Email don vi duoc duyet", create_organization_approved),
        ("Email xac nhan dang ky tai khoan", create_account_registration),
        ("Email xac nhan email thanh cong", create_email_confirmed),
        ("Email thong bao doi moi dang ky", create_new_team_registration),
        ("Email thong bao doi moi tham gia", create_new_team_joined),
        ("Email thanh toan bi tu choi", create_payment_rejected),
        ("Email xac nhan da nhan hoa don", create_payment_pending_confirmation),
        ("Email loi moi chuyen nhuong", create_transfer_invitation),
        ("Email chuyen nhuong duoc chap nhan", create_transfer_accepted),
        ("Email chuyen nhuong bi tu choi", create_transfer_rejected),
        ("Email cap nhat trang thai ung tuyen", create_job_status_update),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nDang tao: {test_name}")
        if test_func():
            success_count += 1
        print("-" * 40)
    
    print(f"\nKet qua: {success_count}/{total_count} file duoc tao thanh cong")
    
    if success_count == total_count:
        print("Tat ca file HTML da duoc tao thanh cong!")
        print("Cac file HTML da duoc luu trong thu muc hien tai")
        print("Ban co the mo cac file nay bang trinh duyet de xem")
    else:
        print("Mot so file gap loi, vui long kiem tra template")

if __name__ == '__main__':
    main()
