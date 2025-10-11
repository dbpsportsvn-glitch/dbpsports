from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from blog.models import BlogCategory, BlogPost, BlogTag
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample blog data'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample blog data...')

        # Create categories
        categories_data = [
            {'name': 'Tin Tức Thể Thao', 'description': 'Những tin tức mới nhất về thể thao'},
            {'name': 'Review Sản Phẩm', 'description': 'Đánh giá chi tiết các sản phẩm thể thao'},
            {'name': 'Hướng Dẫn', 'description': 'Hướng dẫn sử dụng và chăm sóc sản phẩm'},
            {'name': 'Mẹo Hay', 'description': 'Những mẹo hay cho người chơi thể thao'},
        ]

        categories = []
        for cat_data in categories_data:
            category, created = BlogCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            categories.append(category)
            if created:
                self.stdout.write('Created category')

        # Create tags
        tags_data = [
            {'name': 'Bóng Đá', 'color': '#dc2626'},
            {'name': 'Pickleball', 'color': '#10b981'},
            {'name': 'Bóng Rổ', 'color': '#f59e0b'},
            {'name': 'Cầu Lông', 'color': '#3b82f6'},
            {'name': 'Chạy Bộ', 'color': '#8b5cf6'},
            {'name': 'Giày Thể Thao', 'color': '#ef4444'},
            {'name': 'Quần Áo', 'color': '#06b6d4'},
            {'name': 'Phụ Kiện', 'color': '#84cc16'},
        ]

        tags = []
        for tag_data in tags_data:
            tag, created = BlogTag.objects.get_or_create(
                name=tag_data['name'],
                defaults={'color': tag_data['color']}
            )
            tags.append(tag)
            if created:
                self.stdout.write('Created tag')

        # Get or create admin user
        try:
            admin_user = User.objects.get(email='admin@dbpsports.com')
        except User.DoesNotExist:
            admin_user = User.objects.create_user(
                email='admin@dbpsports.com',
                username='admin_blog',
                first_name='Admin',
                last_name='DBP Sports',
                password='admin123',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write('Created admin user')

        # Create sample posts
        posts_data = [
            {
                'title': 'DBP Basketball Shoes Pro - Review Chi Tiết',
                'excerpt': 'Đánh giá toàn diện về giày bóng rổ DBP Basketball Shoes Pro với công nghệ tiên tiến và thiết kế hiện đại.',
                'content': '''
                <h2>Giới Thiệu</h2>
                <p>DBP Basketball Shoes Pro là sản phẩm cao cấp nhất trong dòng giày bóng rổ của DBP Sports. Với công nghệ tiên tiến và thiết kế hiện đại, đôi giày này hứa hẹn mang lại trải nghiệm tuyệt vời cho người chơi.</p>
                
                <h2>Thiết Kế</h2>
                <p>Thiết kế của DBP Basketball Shoes Pro được tối ưu hóa cho hiệu suất thi đấu. Đế giày được làm từ cao su cao cấp với độ bám tuyệt vời trên sân cứng.</p>
                
                <h2>Hiệu Suất</h2>
                <p>Trong quá trình test, đôi giày cho thấy khả năng hỗ trợ tuyệt vời cho cổ chân và bàn chân. Độ đàn hồi tốt giúp giảm tác động khi nhảy và chạy.</p>
                
                <h2>Kết Luận</h2>
                <p>DBP Basketball Shoes Pro là lựa chọn tuyệt vời cho những ai đang tìm kiếm một đôi giày bóng rổ chất lượng cao với giá cả hợp lý.</p>
                ''',
                'post_type': 'review',
                'category': categories[1],  # Review Sản Phẩm
                'tags': [tags[2], tags[5]],  # Bóng Rổ, Giày Thể Thao
                'is_featured': True
            },
            {
                'title': 'Giải Đấu Bóng Đá Phong Trào 2025 - Thông Tin Mới Nhất',
                'excerpt': 'Cập nhật thông tin mới nhất về giải đấu bóng đá phong trào 2025 với nhiều đội bóng tham gia.',
                'content': '''
                <h2>Thông Tin Giải Đấu</h2>
                <p>Giải đấu bóng đá phong trào 2025 sẽ được tổ chức từ tháng 3 đến tháng 6 với sự tham gia của hơn 50 đội bóng từ khắp cả nước.</p>
                
                <h2>Thể Thức Thi Đấu</h2>
                <p>Giải đấu sẽ được chia thành 4 bảng đấu, mỗi bảng có 12-13 đội. Các đội sẽ thi đấu vòng tròn một lượt để chọn ra 2 đội đầu bảng vào vòng knock-out.</p>
                
                <h2>Giải Thưởng</h2>
                <p>Tổng giá trị giải thưởng lên đến 500 triệu đồng với giải nhất nhận được 100 triệu đồng và cúp vô địch.</p>
                
                <h2>Đăng Ký Tham Gia</h2>
                <p>Các đội có thể đăng ký tham gia từ ngày 1/1/2025 đến hết ngày 28/2/2025. Phí đăng ký là 2 triệu đồng/đội.</p>
                ''',
                'post_type': 'news',
                'category': categories[0],  # Tin Tức Thể Thao
                'tags': [tags[0]],  # Bóng Đá
                'is_featured': True
            },
            {
                'title': 'Hướng Dẫn Chọn Giày Pickleball Phù Hợp',
                'excerpt': 'Bí quyết chọn giày pickleball phù hợp với phong cách chơi và điều kiện sân đấu.',
                'content': '''
                <h2>Tại Sao Cần Giày Pickleball Chuyên Dụng?</h2>
                <p>Pickleball có những đặc thù riêng về chuyển động và bề mặt sân, do đó cần giày chuyên dụng để đảm bảo an toàn và hiệu suất.</p>
                
                <h2>Các Yếu Tố Cần Xem Xét</h2>
                <h3>1. Độ Bám</h3>
                <p>Giày pickleball cần có độ bám tốt trên sân cứng để tránh trượt ngã khi di chuyển nhanh.</p>
                
                <h3>2. Hỗ Trợ Cổ Chân</h3>
                <p>Cổ chân cần được hỗ trợ tốt để tránh chấn thương khi thực hiện các động tác xoay người.</p>
                
                <h3>3. Độ Thoáng Khí</h3>
                <p>Giày cần có khả năng thoáng khí tốt để giữ chân khô ráo trong suốt trận đấu.</p>
                
                <h2>Khuyến Nghị</h2>
                <p>Nên chọn giày từ các thương hiệu uy tín như DBP Sports với công nghệ tiên tiến và chất lượng đảm bảo.</p>
                ''',
                'post_type': 'guide',
                'category': categories[2],  # Hướng Dẫn
                'tags': [tags[1], tags[5]],  # Pickleball, Giày Thể Thao
                'is_featured': False
            },
            {
                'title': '5 Mẹo Hay Để Tăng Hiệu Suất Chơi Cầu Lông',
                'excerpt': 'Những mẹo hay từ chuyên gia giúp bạn cải thiện kỹ thuật và hiệu suất chơi cầu lông.',
                'content': '''
                <h2>Mẹo 1: Tư Thế Chuẩn Bị</h2>
                <p>Luôn giữ tư thế chuẩn bị với chân rộng bằng vai, đầu gối hơi cong và trọng tâm thấp để sẵn sàng di chuyển.</p>
                
                <h2>Mẹo 2: Cầm Vợt Đúng Cách</h2>
                <p>Cầm vợt bằng ngón cái và ngón trỏ, các ngón còn lại thả lỏng để có thể điều chỉnh góc đánh linh hoạt.</p>
                
                <h2>Mẹo 3: Di Chuyển Hiệu Quả</h2>
                <p>Sử dụng bước chéo để di chuyển nhanh và tiết kiệm sức lực. Luôn quay về vị trí trung tâm sau mỗi cú đánh.</p>
                
                <h2>Mẹo 4: Phát Bóng Chiến Thuật</h2>
                <p>Thay đổi độ cao và hướng phát bóng để đối thủ khó đoán. Phát bóng ngắn để ép đối thủ lên lưới.</p>
                
                <h2>Mẹo 5: Tập Luyện Thường Xuyên</h2>
                <p>Tập luyện ít nhất 3 lần/tuần để duy trì phong độ. Tập trung vào kỹ thuật cơ bản trước khi học các kỹ thuật nâng cao.</p>
                ''',
                'post_type': 'tips',
                'category': categories[3],  # Mẹo Hay
                'tags': [tags[3]],  # Cầu Lông
                'is_featured': False
            },
            {
                'title': 'Xu Hướng Thời Trang Thể Thao 2025',
                'excerpt': 'Khám phá những xu hướng thời trang thể thao mới nhất năm 2025 với thiết kế hiện đại và công nghệ tiên tiến.',
                'content': '''
                <h2>Xu Hướng Màu Sắc</h2>
                <p>Năm 2025, màu sắc neon và pastel sẽ thống trị thời trang thể thao. Các tone màu sáng như xanh neon, hồng pastel sẽ được ưa chuộng.</p>
                
                <h2>Công Nghệ Vải</h2>
                <p>Vải thông minh với khả năng điều chỉnh nhiệt độ và kháng khuẩn sẽ là xu hướng chính. Công nghệ nano được ứng dụng rộng rãi.</p>
                
                <h2>Thiết Kế</h2>
                <p>Thiết kế minimalist với các đường nét đơn giản nhưng tinh tế. Logo và branding được tích hợp một cách tự nhiên.</p>
                
                <h2>Bền Vững</h2>
                <p>Xu hướng sử dụng vật liệu tái chế và thân thiện với môi trường ngày càng được chú trọng.</p>
                ''',
                'post_type': 'news',
                'category': categories[0],  # Tin Tức Thể Thao
                'tags': [tags[6]],  # Quần Áo
                'is_featured': True
            },
            {
                'title': 'Review DBP Running Shoes Marathon - Chạy Bộ Chuyên Nghiệp',
                'excerpt': 'Đánh giá chi tiết giày chạy bộ DBP Running Shoes Marathon với công nghệ đệm khí tiên tiến.',
                'content': '''
                <h2>Tổng Quan</h2>
                <p>DBP Running Shoes Marathon được thiết kế dành riêng cho các runner chuyên nghiệp với công nghệ đệm khí tiên tiến.</p>
                
                <h2>Công Nghệ Đệm</h2>
                <p>Hệ thống đệm khí AirMax được tích hợp trong đế giày giúp giảm tác động lên khớp và tăng hiệu suất chạy.</p>
                
                <h2>Thiết Kế</h2>
                <p>Thiết kế aerodynamic với upper làm từ vải mesh thoáng khí và đế giày bằng cao su cao cấp.</p>
                
                <h2>Hiệu Suất</h2>
                <p>Trong test chạy marathon, giày cho thấy khả năng hỗ trợ tuyệt vời và độ bền cao.</p>
                
                <h2>Kết Luận</h2>
                <p>DBP Running Shoes Marathon là lựa chọn tuyệt vời cho những runner muốn có trải nghiệm chạy bộ tốt nhất.</p>
                ''',
                'post_type': 'review',
                'category': categories[1],  # Review Sản Phẩm
                'tags': [tags[4], tags[5]],  # Chạy Bộ, Giày Thể Thao
                'is_featured': False
            }
        ]

        # Create posts
        for post_data in posts_data:
            post_tags = post_data.pop('tags')
            post, created = BlogPost.objects.get_or_create(
                title=post_data['title'],
                defaults={
                    **post_data,
                    'author': admin_user,
                    'status': 'published',
                    'published_at': timezone.now(),
                    'view_count': 0,
                    'like_count': 0
                }
            )
            
            if created:
                post.tags.set(post_tags)
                self.stdout.write('Created post')
            else:
                self.stdout.write('Post already exists')

        self.stdout.write(
            self.style.SUCCESS('Successfully created sample blog data!')
        )
