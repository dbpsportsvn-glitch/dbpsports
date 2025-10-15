#!/usr/bin/env python
"""
Test tất cả email templates và tạo file HTML để kiểm tra
"""

import os
import sys
import django
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dbpsports_core.settings')
django.setup()

def create_shop_customer_email():
    """Test email xác nhận đơn hàng cho khách hàng"""
    
    mock_data = {
        'order': {
            'order_number': 'ORD-2025-001',
            'customer_name': 'Nguyen Van A',
            'customer_email': 'customer@example.com',
            'customer_phone': '0901234567',
            'total_amount': 500000,
            'created_at': timezone.now(),
            'items': [
                {'product_name': 'Giày bóng đá Nike', 'quantity': 1, 'price': 300000},
                {'product_name': 'Áo đấu Barcelona', 'quantity': 2, 'price': 200000}
            ]
        }
    }
    
    html_message = render_to_string('shop/emails/customer_order_confirmation.html', mock_data)
    
    with open('shop_customer_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao shop_customer_email.html")
    return True

def create_shop_admin_email():
    """Test email thông báo đơn hàng mới cho admin"""
    
    mock_data = {
        'order': {
            'order_number': 'ORD-2025-001',
            'customer_name': 'Nguyen Van A',
            'customer_email': 'customer@example.com',
            'customer_phone': '0901234567',
            'total_amount': 500000,
            'created_at': timezone.now(),
            'items': [
                {'product_name': 'Giày bóng đá Nike', 'quantity': 1, 'price': 300000},
                {'product_name': 'Áo đấu Barcelona', 'quantity': 2, 'price': 200000}
            ]
        }
    }
    
    html_message = render_to_string('shop/emails/admin_order_notification.html', mock_data)
    
    with open('shop_admin_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao shop_admin_email.html")
    return True

def create_shop_payment_confirmed():
    """Test email cảm ơn sau khi thanh toán"""
    
    mock_data = {
        'order': {
            'order_number': 'ORD-2025-001',
            'customer_name': 'Nguyen Van A',
            'total_amount': 500000,
            'created_at': timezone.now()
        }
    }
    
    html_message = render_to_string('shop/emails/payment_confirmed.html', mock_data)
    
    with open('shop_payment_confirmed_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao shop_payment_confirmed_email.html")
    return True

def create_tournament_announcement():
    """Test email thông báo giải đấu"""
    
    mock_data = {
        'announcement': {
            'title': 'Thông báo quan trọng về lịch thi đấu',
            'content': 'Kính gửi các đội trưởng,\n\nBan tổ chức xin thông báo lịch thi đấu vòng loại sẽ được cập nhật vào ngày mai.\n\nVui lòng theo dõi website để cập nhật thông tin mới nhất.\n\nTrân trọng.',
            'tournament': {'name': 'Giải bóng đá phong trào 2025'},
            'created_at': timezone.now()
        }
    }
    
    html_message = render_to_string('tournaments/emails/announcement_notification.html', mock_data)
    
    with open('tournament_announcement_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao tournament_announcement_email.html")
    return True

def create_payment_confirmed():
    """Test email xác nhận thanh toán thành công"""
    
    mock_data = {
        'team': {
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana',
                'email': 'captain@manutd.com'
            }
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 2000000
        }
    }
    
    html_message = render_to_string('tournaments/emails/payment_confirmed.html', mock_data)
    
    with open('payment_confirmed_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao payment_confirmed_email.html")
    return True

def create_new_payment_proof():
    """Test email thông báo thanh toán mới cho admin"""
    
    mock_data = {
        'team': {
            'id': 1,
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana',
                'email': 'captain@manutd.com'
            },
            'payment_proof_uploaded_at': timezone.now()
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 2000000
        },
        'use_shop_discount': True,
        'cart_total': 500000
    }
    
    html_message = render_to_string('tournaments/emails/new_payment_proof.html', mock_data)
    
    with open('new_payment_proof_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao new_payment_proof_email.html")
    return True

def create_payment_pending_confirmation():
    """Test email xác nhận đã nhận hóa đơn thanh toán"""
    
    mock_data = {
        'team': {
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana',
                'email': 'captain@manutd.com'
            }
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 2000000
        },
        'use_shop_discount': True,
        'cart_total': 500000
    }
    
    html_message = render_to_string('tournaments/emails/payment_pending_confirmation.html', mock_data)
    
    with open('payment_pending_confirmation_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao payment_pending_confirmation_email.html")
    return True

def create_payment_rejected():
    """Test email thông báo thanh toán bị từ chối"""
    
    mock_data = {
        'team': {
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana',
                'email': 'captain@manutd.com'
            }
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 2000000
        },
        'rejection_reason': 'Hóa đơn không rõ ràng, vui lòng tải lại hóa đơn có chữ ký và con dấu rõ ràng.'
    }
    
    html_message = render_to_string('tournaments/emails/payment_rejected.html', mock_data)
    
    with open('payment_rejected_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao payment_rejected_email.html")
    return True

def create_new_team_registration():
    """Test email thông báo đội mới đăng ký cho admin"""
    
    mock_data = {
        'team': {
            'id': 1,
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana',
                'email': 'captain@manutd.com'
            },
            'players': {'count': 15},
            'address': '123 Đường ABC, Quận 1, TP.HCM',
            'phone': '0901234567',
            'tournament': {
                'name': 'Giải bóng đá phong trào 2025',
                'registration_fee': 2000000
            }
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'registration_fee': 2000000
        },
        'registration': {
            'registered_at': timezone.now()
        }
    }
    
    html_message = render_to_string('tournaments/emails/new_team_registration.html', mock_data)
    
    with open('new_team_registration_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao new_team_registration_email.html")
    return True

def create_new_team_joined():
    """Test email thông báo đội mới tham gia cho followers"""
    
    mock_data = {
        'team': {
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana'
            }
        },
        'tournament': {
            'name': 'Giải bóng đá phong trào 2025',
            'total_teams': 12
        }
    }
    
    html_message = render_to_string('tournaments/emails/new_team_joined.html', mock_data)
    
    with open('new_team_joined_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao new_team_joined_email.html")
    return True

def create_organization_approved():
    """Test email thông báo đơn vị được duyệt"""
    
    mock_data = {
        'organization': {
            'name': 'Câu lạc bộ bóng đá ABC',
            'description': 'Câu lạc bộ bóng đá chuyên nghiệp tại TP.HCM'
        },
        'owner': {
            'get_full_name': 'Nguyen Van B',
            'username': 'nguyenvanb',
            'email': 'owner@abc.com'
        }
    }
    
    html_message = render_to_string('organizations/emails/organization_approved.html', mock_data)
    
    with open('organization_approved_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao organization_approved_email.html")
    return True

def create_new_organization_notification():
    """Test email thông báo đơn vị mới đăng ký cho admin"""
    
    mock_data = {
        'organization': {
            'name': 'Câu lạc bộ bóng đá ABC',
            'description': 'Câu lạc bộ bóng đá chuyên nghiệp tại TP.HCM',
            'owner': {
                'get_full_name': 'Nguyen Van B',
                'username': 'nguyenvanb',
                'email': 'owner@abc.com'
            }
        }
    }
    
    html_message = render_to_string('organizations/emails/new_organization_notification.html', mock_data)
    
    with open('new_organization_notification_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao new_organization_notification_email.html")
    return True

def create_new_job_application():
    """Test email thông báo đơn ứng tuyển mới"""
    
    mock_data = {
        'applicant': {
            'get_full_name': 'Nguyen Van C',
            'username': 'nguyenvanc',
            'email': 'applicant@example.com'
        },
        'job': {
            'id': 1,
            'title': 'Trong tai chinh',
            'tournament': {
                'id': 1,
                'name': 'Giai bong da phong trao 2025'
            }
        },
        'application': {
            'created_at': timezone.now(),
            'message': 'Toi co kinh nghiem 5 nam lam trong tai va rat mong muon tham gia giai dau nay.'
        }
    }
    
    html_message = render_to_string('organizations/emails/new_job_application.html', mock_data)
    
    with open('new_job_application_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao new_job_application_email.html")
    return True

def create_application_status_update():
    """Test email cập nhật trạng thái ứng tuyển"""
    
    mock_data = {
        'applicant': {
            'get_full_name': 'Nguyen Van C',
            'username': 'nguyenvanc',
            'email': 'applicant@example.com'
        },
        'job': {
            'title': 'Trong tai chinh',
            'tournament': {'name': 'Giai bong da phong trao 2025'}
        },
        'application': {
            'status': 'APPROVED',
            'updated_at': timezone.now()
        }
    }
    
    html_message = render_to_string('organizations/emails/application_status_update.html', mock_data)
    
    with open('application_status_update_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao application_status_update_email.html")
    return True

def create_new_transfer_invitation():
    """Test email lời mời chuyển nhượng"""
    
    mock_data = {
        'inviting_team': {
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana'
            }
        },
        'current_team': {
            'name': 'Chelsea FC',
            'captain': {
                'get_full_name': 'Nguyen Van B',
                'username': 'nguyenvanb'
            }
        },
        'player': {
            'full_name': 'Nguyen Van D',
            'position': 'Tiền đạo'
        }
    }
    
    html_message = render_to_string('organizations/emails/new_transfer_invitation.html', mock_data)
    
    with open('new_transfer_invitation_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao new_transfer_invitation_email.html")
    return True

def create_transfer_accepted():
    """Test email thông báo chuyển nhượng được chấp nhận"""
    
    mock_data = {
        'inviting_team': {
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana'
            }
        },
        'current_team': {
            'name': 'Chelsea FC',
            'captain': {
                'get_full_name': 'Nguyen Van B',
                'username': 'nguyenvanb'
            }
        },
        'player': {
            'full_name': 'Nguyen Van D',
            'position': 'Tiền đạo'
        }
    }
    
    html_message = render_to_string('organizations/emails/transfer_accepted_notification.html', mock_data)
    
    with open('transfer_accepted_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao transfer_accepted_email.html")
    return True

def create_transfer_rejected():
    """Test email thông báo chuyển nhượng bị từ chối"""
    
    mock_data = {
        'inviting_team': {
            'name': 'Manchester United FC',
            'captain': {
                'get_full_name': 'Nguyen Van A',
                'username': 'nguyenvana'
            }
        },
        'current_team': {
            'name': 'Chelsea FC',
            'captain': {
                'get_full_name': 'Nguyen Van B',
                'username': 'nguyenvanb'
            }
        },
        'player': {
            'full_name': 'Nguyen Van D',
            'position': 'Tiền đạo'
        }
    }
    
    html_message = render_to_string('organizations/emails/transfer_rejected_notification.html', mock_data)
    
    with open('transfer_rejected_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao transfer_rejected_email.html")
    return True

def create_account_registration():
    """Test email xác nhận đăng ký tài khoản"""
    
    mock_data = {
        'user': {
            'get_full_name': 'Nguyen Van E',
            'username': 'nguyenvane',
            'email': 'user@example.com'
        },
        'activate_url': 'http://localhost:8000/account/confirm-email/abc123/'
    }
    
    html_message = render_to_string('account/email/email_confirmation_message.html', mock_data)
    
    with open('account_registration_email.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao account_registration_email.html")
    return True

def create_email_confirmed():
    """Test email xác nhận email thành công"""
    
    mock_data = {
        'user': {
            'get_full_name': 'Nguyen Van E',
            'username': 'nguyenvane',
            'email': 'user@example.com'
        }
    }
    
    html_message = render_to_string('account/email/email_confirmed.html', mock_data)
    
    with open('email_confirmed.html', 'w', encoding='utf-8') as f:
        f.write(html_message)
    
    print("SUCCESS: Da tao email_confirmed.html")
    return True

def main():
    """Chạy tất cả test email"""
    
    print("=== BAT DAU TEST TAT CA EMAIL TEMPLATES ===")
    
    # Shop emails
    create_shop_customer_email()
    create_shop_admin_email()
    create_shop_payment_confirmed()
    
    # Tournament emails
    create_tournament_announcement()
    create_payment_confirmed()
    create_new_payment_proof()
    create_payment_pending_confirmation()
    create_payment_rejected()
    create_new_team_registration()
    create_new_team_joined()
    
    # Organization emails
    create_organization_approved()
    create_new_organization_notification()
    create_new_job_application()
    create_application_status_update()
    create_new_transfer_invitation()
    create_transfer_accepted()
    create_transfer_rejected()
    
    # Account emails
    create_account_registration()
    create_email_confirmed()
    
    print("\n=== HOAN THANH TEST TAT CA EMAIL TEMPLATES ===")
    print("Da tao 18 file HTML de kiem tra:")
    print("1. shop_customer_email.html")
    print("2. shop_admin_email.html")
    print("3. shop_payment_confirmed_email.html")
    print("4. tournament_announcement_email.html")
    print("5. payment_confirmed_email.html")
    print("6. new_payment_proof_email.html")
    print("7. payment_pending_confirmation_email.html")
    print("8. payment_rejected_email.html")
    print("9. new_team_registration_email.html")
    print("10. new_team_joined_email.html")
    print("11. organization_approved_email.html")
    print("12. new_organization_notification_email.html")
    print("13. new_job_application_email.html")
    print("14. application_status_update_email.html")
    print("15. new_transfer_invitation_email.html")
    print("16. transfer_accepted_email.html")
    print("17. transfer_rejected_email.html")
    print("18. account_registration_email.html")
    print("19. email_confirmed.html")
    print("\nMo cac file nay trong browser de kiem tra!")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
