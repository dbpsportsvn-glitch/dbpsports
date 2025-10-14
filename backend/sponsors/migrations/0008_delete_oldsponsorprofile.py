from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('sponsors', '0007_oldsponsorprofile_alter_testimonial_sponsor_profile_and_more'),
    ]

    operations = [
        # BƯỚC 1: Thêm thao tác RunSQL để gỡ bỏ Foreign Key Constraint một cách thủ công.
        # Tên của constraint và tên bảng lấy từ thông báo lỗi bạn nhận được.
        migrations.RunSQL(
            sql="ALTER TABLE `sponsors_testimonial` DROP FOREIGN KEY `sponsors_testimonial_sponsor_profile_id_ac11d79a_fk_sponsors_`;",
            reverse_sql=migrations.RunSQL.noop # Không cần làm gì khi rollback
        ),
        
        # BƯỚC 2: Sau khi đã gỡ bỏ ràng buộc, tiến hành xóa model như cũ.
        migrations.DeleteModel(
            name='OldSponsorProfile',
        ),
    ]