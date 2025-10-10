# backend/dbpsports_core/admin_custom.py

from django.contrib import admin
from django.contrib.admin import AdminSite

# Tùy chỉnh tiêu đề admin
admin.site.site_header = "DBP Sports - Quản trị hệ thống"
admin.site.site_title = "DBP Sports Admin"
admin.site.index_title = "Trang quản trị DBP Sports"

# Override get_app_list để sắp xếp lại thứ tự
original_get_app_list = admin.AdminSite.get_app_list

def custom_get_app_list(self, request, app_label=None):
    """
    Sắp xếp lại thứ tự các app trong admin
    """
    app_list = original_get_app_list(self, request, app_label)
    
    # Định nghĩa thứ tự ưu tiên cho các app
    app_order = {
        'tournaments': 1,      # Tournament và điều hành giải đấu - ưu tiên cao nhất
        'organizations': 2,    # Tổ chức
        'users': 3,            # Người dùng
        'sponsors': 4,         # Nhà tài trợ
        'auth': 5,             # Authentication
        'sites': 6,            # Sites
        'admin_interface': 7,  # Admin Interface
        'colorfield': 8,       # Color Field
    }
    
    # Sắp xếp theo thứ tự ưu tiên
    def get_app_priority(app):
        return app_order.get(app['app_label'], 999)
    
    app_list.sort(key=get_app_priority)
    
    # Tùy chỉnh thứ tự các model trong từng app
    for app in app_list:
        if app['app_label'] == 'tournaments':
            # Sắp xếp lại thứ tự models trong tournaments
            model_order = {
                'tournament': 1,           # Giải đấu
                'teamregistration': 2,    # Đăng ký đội
                'team': 3,                 # Đội bóng
                'player': 4,               # Cầu thủ
                'match': 5,                # Trận đấu
                'group': 6,                # Bảng đấu
                'lineup': 7,               # Đội hình
                'goal': 8,                 # Bàn thắng
                'card': 9,                 # Thẻ phạt
                'announcement': 10,        # Thông báo
                'tournamentphoto': 11,     # Ảnh giải đấu
                'teamachievement': 12,     # Thành tích đội
                'homebanner': 13,          # Banner trang chủ
                'notification': 14,        # Thông báo hệ thống
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
        elif app['app_label'] == 'organizations':
            # Sắp xếp lại thứ tự models trong organizations
            model_order = {
                'organization': 1,        # Tổ chức
                'membership': 2,           # Thành viên
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
        elif app['app_label'] == 'users':
            # Sắp xếp lại thứ tự models trong users
            model_order = {
                'user': 1,                 # Người dùng
                'profile': 2,              # Hồ sơ
                'role': 3,                 # Vai trò
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
    
    return app_list

# Monkey patch để áp dụng custom get_app_list
admin.AdminSite.get_app_list = custom_get_app_list
