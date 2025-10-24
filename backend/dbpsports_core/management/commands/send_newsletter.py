from django.core.management.base import BaseCommand
from django.conf import settings
from dbpsports_core.views import send_newsletter_bulk


class Command(BaseCommand):
    help = 'Gửi newsletter cho tất cả subscribers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Chế độ test - chỉ gửi cho 1 email đầu tiên',
        )
        parser.add_argument(
            '--subject',
            type=str,
            default='🏆 DBP Sports - Newsletter',
            help='Tiêu đề email',
        )
        parser.add_argument(
            '--content',
            type=str,
            help='Nội dung email (HTML)',
        )

    def handle(self, *args, **options):
        test_mode = options['test']
        subject = options['subject']
        content = options['content']
        
        # Nội dung mặc định nếu không được cung cấp
        if not content:
            content = """
            <h2>🎉 Newsletter từ DBP Sports!</h2>
            <p>Chào mừng bạn đến với newsletter của DBP Sports!</p>
            <p>Dưới đây là những thông tin mới nhất:</p>
            
            <h3>🏆 Giải đấu sắp diễn ra</h3>
            <p>Có nhiều giải đấu thú vị đang chờ bạn tham gia. Hãy truy cập website để xem chi tiết!</p>
            
            <h3>⚽ Tin tức nổi bật</h3>
            <p>Cập nhật những tin tức mới nhất về thể thao phong trào tại Điện Biên.</p>
            
            <h3>🎁 Ưu đãi đặc biệt</h3>
            <p>Shop DBP Sports có nhiều ưu đãi hấp dẫn cho các sản phẩm thể thao.</p>
            
            <p>Cảm ơn bạn đã đồng hành cùng DBP Sports!</p>
            """
        
        # Gửi newsletter
        result = send_newsletter_bulk(
            subject=subject,
            content=content,
            test_mode=test_mode
        )
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(
                    f"[SUCCESS] Newsletter sent successfully! "
                    f"Sent: {result['sent']}/{result['total']} emails"
                )
            )
            if result['failed'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARNING] Failed to send {result['failed']} emails"
                    )
                )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"[ERROR] Failed to send newsletter: {result['error']}"
                )
            )
