"""
Views cho music statistics và tracking
"""
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
import json
from .models import Track, UserTrack, TrackPlayHistory


@login_required
@require_POST
def record_track_play(request):
    """
    API endpoint để ghi nhận lượt nghe
    Quy tắc: Chỉ tính khi nghe ít nhất 30 giây hoặc 50% thời lượng bài (nếu bài ngắn)
    """
    try:
        data = json.loads(request.body)
        track_id = data.get('track_id')
        track_type = data.get('track_type', 'global')  # 'global' hoặc 'user'
        listen_duration = data.get('listen_duration', 0)  # Số giây đã nghe
        
        if not track_id:
            return JsonResponse({
                'success': False,
                'error': 'Missing track_id'
            }, status=400)
        
        # Lấy track object
        if track_type == 'global':
            track = get_object_or_404(Track, id=track_id, is_active=True)
            global_track = track
            user_track_obj = None
        else:
            track = get_object_or_404(UserTrack, id=track_id, user=request.user, is_active=True)
            global_track = None
            user_track_obj = track
        
        # Kiểm tra điều kiện tính lượt nghe
        # ✅ Fix division by zero: nếu duration = 0 hoặc None thì skip calculation
        if not track.duration or track.duration <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Track duration không hợp lệ'
            }, status=400)
        
        min_duration = min(30, track.duration * 0.5)  # 30s hoặc 50% bài (cái nào nhỏ hơn)
        is_completed = listen_duration >= track.duration * 0.9  # Nghe ít nhất 90% = hoàn thành
        
        if listen_duration < min_duration:
            return JsonResponse({
                'success': False,
                'message': 'Chưa đủ thời gian để tính lượt nghe',
                'min_duration': min_duration,
                'listened': listen_duration
            })
        
        # Kiểm tra spam (cùng user + track trong 5 phút gần nhất)
        should_count = TrackPlayHistory.should_count_as_play(
            user=request.user,
            track_id=track_id,
            track_type=track_type
        )
        
        if not should_count:
            return JsonResponse({
                'success': True,
                'message': 'Đã ghi nhận (không tính trùng)',
                'counted': False
            })
        
        # Tạo lịch sử nghe
        play_history = TrackPlayHistory.objects.create(
            user=request.user,
            global_track=global_track,
            user_track=user_track_obj,
            listen_duration=listen_duration,
            is_completed=is_completed,
            track_title=track.title,
            track_artist=track.artist or '',
            track_duration=track.duration
        )
        
        # Tăng play_count của track
        track.play_count += 1
        track.save(update_fields=['play_count'])
        
        return JsonResponse({
            'success': True,
            'message': 'Đã ghi nhận lượt nghe',
            'counted': True,
            'play_count': track.play_count,
            'is_completed': is_completed
        })
        
    except Track.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Track không tồn tại'
        }, status=404)
    except UserTrack.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Track không tồn tại hoặc không thuộc về bạn'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_user_stats(request):
    """API endpoint để lấy thống kê của user"""
    try:
        days = int(request.GET.get('days', 30))
        stats = TrackPlayHistory.get_user_stats(request.user, days=days)
        
        # Format thời gian nghe
        total_minutes = stats['total_listen_time'] // 60
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        return JsonResponse({
            'success': True,
            'stats': {
                'total_plays': stats['total_plays'],
                'total_listen_time': stats['total_listen_time'],
                'total_listen_time_formatted': f"{hours}h {minutes}m",
                'completed_plays': stats['completed_plays'],
                'completion_rate': round(stats['completed_plays'] / stats['total_plays'] * 100, 1) if stats['total_plays'] > 0 else 0
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_popular_tracks(request):
    """API endpoint để lấy top tracks phổ biến"""
    try:
        limit = int(request.GET.get('limit', 10))
        days = int(request.GET.get('days', 7))
        
        popular = TrackPlayHistory.get_popular_tracks(limit=limit, days=days)
        
        return JsonResponse({
            'success': True,
            'popular_tracks': popular
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

