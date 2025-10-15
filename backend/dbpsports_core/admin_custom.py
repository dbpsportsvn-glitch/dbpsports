# backend/dbpsports_core/admin_custom.py

from django.contrib import admin
from django.contrib.admin import AdminSite

# Tùy chỉnh tiêu đề admin
admin.site.site_header = "🏆 DBP Sports - Trung tâm Quản trị"
admin.site.site_title = "DBP Sports Admin"
admin.site.index_title = "Chào mừng đến với Trung tâm Quản trị DBP Sports"

# Override get_app_list để sắp xếp lại thứ tự và Việt hóa
original_get_app_list = admin.AdminSite.get_app_list

def custom_get_app_list(self, request, app_label=None):
    """
    Sắp xếp lại thứ tự các app trong admin và Việt hóa tên hiển thị
    """
    app_list = original_get_app_list(self, request, app_label)
    
    # Định nghĩa thứ tự ưu tiên cho các app
    app_order = {
        'tournaments': 1,      # Giải đấu - ưu tiên cao nhất
        'organizations': 2,    # Tổ chức
        'users': 3,            # Người dùng
        'sponsors': 4,         # Nhà tài trợ
        'shop': 5,             # Cửa hàng
        'blog': 6,             # Tin tức
        'auth': 7,             # Xác thực
        'sites': 8,            # Sites
        'admin_interface': 9,  # Giao diện Admin
        'colorfield': 10,      # Trường màu
    }
    
    # Tên hiển thị tiếng Việt cho các app
    app_names = {
        'tournaments': '🏆 Giải đấu',
        'organizations': '🏢 Tổ chức',
        'users': '👥 Người dùng',
        'sponsors': '💰 Nhà tài trợ',
        'shop': '🛒 Cửa hàng',
        'blog': '📰 Tin tức',
        'auth': '🔐 Xác thực',
        'sites': '🌐 Sites',
        'admin_interface': '🎨 Giao diện Admin',
        'colorfield': '🎨 Trường màu',
    }
    
    # Sắp xếp theo thứ tự ưu tiên
    def get_app_priority(app):
        return app_order.get(app['app_label'], 999)
    
    app_list.sort(key=get_app_priority)
    
    # Tùy chỉnh tên hiển thị và thứ tự các model trong từng app
    for app in app_list:
        # Cập nhật tên hiển thị app
        if app['app_label'] in app_names:
            app['name'] = app_names[app['app_label']]
        
        if app['app_label'] == 'tournaments':
            # Sắp xếp lại thứ tự models trong tournaments
            model_order = {
                'tournament': 1,           # Giải đấu
                'teamregistration': 2,     # Đăng ký đội
                'team': 3,                 # Đội bóng
                'player': 4,               # Cầu thủ
                'match': 5,                # Trận đấu
                'group': 6,                # Bảng đấu
                'lineup': 7,              # Đội hình
                'goal': 8,                 # Bàn thắng
                'card': 9,                 # Thẻ phạt
                'announcement': 10,        # Thông báo
                'tournamentphoto': 11,     # Ảnh giải đấu
                'teamachievement': 12,     # Thành tích đội
                'homebanner': 13,          # Banner trang chủ
                'notification': 14,        # Thông báo hệ thống
                'tournamentbudget': 15,    # Ngân sách giải đấu
                'revenueitem': 16,         # Khoản thu
                'expenseitem': 17,         # Khoản chi
                'budgethistory': 18,       # Lịch sử ngân sách
                'tournamentstaff': 19,      # Nhân sự giải đấu
                'matchnote': 20,           # Ghi chú trận đấu
                'coachrecruitment': 21,    # Tuyển dụng HLV
            }
            
            # Tên hiển thị tiếng Việt cho models tournaments
            model_names = {
                'tournament': '🏆 Giải đấu',
                'teamregistration': '📝 Đăng ký đội',
                'team': '⚽ Đội bóng',
                'player': '👤 Cầu thủ',
                'match': '⚽ Trận đấu',
                'group': '📊 Bảng đấu',
                'lineup': '📋 Đội hình',
                'goal': '⚽ Bàn thắng',
                'card': '🟨 Thẻ phạt',
                'announcement': '📢 Thông báo',
                'tournamentphoto': '📸 Ảnh giải đấu',
                'teamachievement': '🏅 Thành tích đội',
                'homebanner': '🖼️ Banner trang chủ',
                'notification': '🔔 Thông báo hệ thống',
                'tournamentbudget': '💰 Ngân sách giải đấu',
                'revenueitem': '💵 Khoản thu',
                'expenseitem': '💸 Khoản chi',
                'budgethistory': '📈 Lịch sử ngân sách',
                'tournamentstaff': '👨‍💼 Nhân sự giải đấu',
                'matchnote': '📝 Ghi chú trận đấu',
                'coachrecruitment': '👨‍🏫 Tuyển dụng HLV',
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
            # Cập nhật tên hiển thị models
            for model in app['models']:
                if model['object_name'].lower() in model_names:
                    model['name'] = model_names[model['object_name'].lower()]
            
        elif app['app_label'] == 'organizations':
            # Sắp xếp lại thứ tự models trong organizations
            model_order = {
                'organization': 1,        # Tổ chức
                'membership': 2,           # Thành viên
                'jobposting': 3,           # Tin tuyển dụng
                'jobapplication': 4,       # Đơn ứng tuyển
            }
            
            # Tên hiển thị tiếng Việt cho models organizations
            model_names = {
                'organization': '🏢 Tổ chức',
                'membership': '👥 Thành viên',
                'jobposting': '📋 Tin tuyển dụng',
                'jobapplication': '📄 Đơn ứng tuyển',
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
            # Cập nhật tên hiển thị models
            for model in app['models']:
                if model['object_name'].lower() in model_names:
                    model['name'] = model_names[model['object_name'].lower()]
            
        elif app['app_label'] == 'users':
            # Sắp xếp lại thứ tự models trong users
            model_order = {
                'user': 1,                 # Người dùng
                'profile': 2,              # Hồ sơ
                'role': 3,                 # Vai trò
                'coachprofile': 4,         # Hồ sơ HLV
                'stadiumprofile': 5,       # Hồ sơ sân bóng
                'coachreview': 6,          # Đánh giá HLV
                'stadiumreview': 7,         # Đánh giá sân bóng
            }
            
            # Tên hiển thị tiếng Việt cho models users
            model_names = {
                'user': '👤 Người dùng',
                'profile': '📋 Hồ sơ',
                'role': '🎭 Vai trò',
                'coachprofile': '👨‍🏫 Hồ sơ HLV',
                'stadiumprofile': '🏟️ Hồ sơ sân bóng',
                'coachreview': '⭐ Đánh giá HLV',
                'stadiumreview': '⭐ Đánh giá sân bóng',
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
            # Cập nhật tên hiển thị models
            for model in app['models']:
                if model['object_name'].lower() in model_names:
                    model['name'] = model_names[model['object_name'].lower()]
            
        elif app['app_label'] == 'sponsors':
            # Sắp xếp lại thứ tự models trong sponsors
            model_order = {
                'sponsorprofile': 1,       # Hồ sơ nhà tài trợ
                'testimonial': 2,          # Lời chứng thực
            }
            
            # Tên hiển thị tiếng Việt cho models sponsors
            model_names = {
                'sponsorprofile': '💰 Hồ sơ nhà tài trợ',
                'testimonial': '💬 Lời chứng thực',
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
            # Cập nhật tên hiển thị models
            for model in app['models']:
                if model['object_name'].lower() in model_names:
                    model['name'] = model_names[model['object_name'].lower()]
            
        elif app['app_label'] == 'shop':
            # Sắp xếp lại thứ tự models trong shop
            model_order = {
                'category': 1,             # Danh mục
                'product': 2,             # Sản phẩm
                'productimage': 3,         # Ảnh sản phẩm
                'productvariant': 4,       # Biến thể sản phẩm
                'productsize': 5,          # Kích thước sản phẩm
                'cart': 6,                 # Giỏ hàng
                'cartitem': 7,             # Mục giỏ hàng
                'order': 8,                # Đơn hàng
                'orderitem': 9,            # Mục đơn hàng
                'shopbanner': 10,          # Banner cửa hàng
                'productimport': 11,       # Nhập sản phẩm
                'paymentmethod': 12,       # Phương thức thanh toán
                'bankaccount': 13,         # Tài khoản ngân hàng
                'ewalletaccount': 14,      # Tài khoản ví điện tử
                'paymentstep': 15,         # Bước thanh toán
                'contactinfo': 16,         # Thông tin liên hệ
                'paymentpolicy': 17,       # Chính sách thanh toán
                'customershippinginfo': 18, # Thông tin giao hàng
                'contactsettings': 19,    # Cài đặt liên hệ
            }
            
            # Tên hiển thị tiếng Việt cho models shop
            model_names = {
                'category': '📂 Danh mục',
                'product': '🛍️ Sản phẩm',
                'productimage': '📸 Ảnh sản phẩm',
                'productvariant': '🔧 Biến thể sản phẩm',
                'productsize': '📏 Kích thước sản phẩm',
                'cart': '🛒 Giỏ hàng',
                'cartitem': '📦 Mục giỏ hàng',
                'order': '📋 Đơn hàng',
                'orderitem': '📄 Mục đơn hàng',
                'shopbanner': '🖼️ Banner cửa hàng',
                'productimport': '📥 Nhập sản phẩm',
                'paymentmethod': '💳 Phương thức thanh toán',
                'bankaccount': '🏦 Tài khoản ngân hàng',
                'ewalletaccount': '📱 Tài khoản ví điện tử',
                'paymentstep': '⚡ Bước thanh toán',
                'contactinfo': '📞 Thông tin liên hệ',
                'paymentpolicy': '📋 Chính sách thanh toán',
                'customershippinginfo': '🚚 Thông tin giao hàng',
                'contactsettings': '⚙️ Cài đặt liên hệ',
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
            # Cập nhật tên hiển thị models
            for model in app['models']:
                if model['object_name'].lower() in model_names:
                    model['name'] = model_names[model['object_name'].lower()]
            
        elif app['app_label'] == 'blog':
            # Sắp xếp lại thứ tự models trong blog
            model_order = {
                'blogcategory': 1,         # Danh mục blog
                'blogpost': 2,            # Bài viết blog
                'blogcomment': 3,         # Bình luận blog
                'blogtag': 4,             # Thẻ blog
            }
            
            # Tên hiển thị tiếng Việt cho models blog
            model_names = {
                'blogcategory': '📂 Danh mục tin tức',
                'blogpost': '📰 Bài viết',
                'blogcomment': '💬 Bình luận',
                'blogtag': '🏷️ Thẻ',
            }
            
            def get_model_priority(model):
                return model_order.get(model['object_name'].lower(), 999)
            
            app['models'].sort(key=get_model_priority)
            
            # Cập nhật tên hiển thị models
            for model in app['models']:
                if model['object_name'].lower() in model_names:
                    model['name'] = model_names[model['object_name'].lower()]
    
    return app_list

# Monkey patch để áp dụng custom get_app_list
admin.AdminSite.get_app_list = custom_get_app_list

# Override get_actions để sắp xếp lại thứ tự actions
original_get_actions = admin.ModelAdmin.get_actions

def custom_get_actions(self, request):
    """
    Sắp xếp lại thứ tự actions, đưa delete action xuống cuối cùng
    """
    actions = original_get_actions(self, request)
    
    # Lấy delete action và xóa khỏi dict
    delete_action = actions.pop('delete_selected', None)
    
    # Thêm delete action vào cuối cùng nếu có
    if delete_action:
        actions['delete_selected'] = delete_action
    
    return actions

# Monkey patch để áp dụng custom get_actions
admin.ModelAdmin.get_actions = custom_get_actions
