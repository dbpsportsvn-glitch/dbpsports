# backend/users/management/commands/create_missing_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import Profile

User = get_user_model()

class Command(BaseCommand):
    help = 'Tạo profile cho tất cả users chưa có profile'

    def handle(self, *args, **options):
        users_without_profile = []
        
        for user in User.objects.all():
            try:
                # Thử truy cập profile
                _ = user.profile
            except Profile.DoesNotExist:
                # Nếu không có profile, tạo mới
                Profile.objects.create(user=user)
                users_without_profile.append(user.username)
                self.stdout.write(
                    self.style.SUCCESS(f'[OK] Da tao profile cho user: {user.username}')
                )
        
        if not users_without_profile:
            self.stdout.write(
                self.style.SUCCESS('[OK] Tat ca users da co profile!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n[OK] Hoan thanh! Da tao profile cho {len(users_without_profile)} users.'
                )
            )

