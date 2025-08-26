# tournaments/admin.py

from django.contrib import admin
from .models import Tournament # Đảm bảo có dòng này

# Đăng ký model Tournament tại đây
admin.site.register(Tournament) # Và dòng này