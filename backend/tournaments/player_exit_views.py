# backend/tournaments/player_exit_views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db import transaction
from django.utils import timezone
from django.urls import reverse

from .models import Player, PlayerTeamExit, Notification
from .utils import send_notification_email


@login_required
def request_team_exit(request, player_pk):
    """
    View để cầu thủ yêu cầu rời đội
    """
    player = get_object_or_404(Player, pk=player_pk)
    
    # Kiểm tra quyền: chỉ cầu thủ đó mới có thể yêu cầu rời đội
    if not player.team:
        messages.error(request, "Bạn không thuộc đội nào.")
        return redirect('player_detail', pk=player.pk)
    
    if player.user != request.user:
        messages.error(request, "Bạn không có quyền thực hiện hành động này.")
        return redirect('player_detail', pk=player.pk)
    
    # Kiểm tra đã có yêu cầu rời đội đang chờ xử lý chưa
    existing_request = PlayerTeamExit.objects.filter(
        player=player,
        status=PlayerTeamExit.Status.PENDING
    ).first()
    
    if existing_request:
        messages.warning(request, "Bạn đã có yêu cầu rời đội đang chờ xử lý.")
        return redirect('player_detail', pk=player.pk)
    
    if request.method == 'POST':
        exit_type = request.POST.get('exit_type', PlayerTeamExit.ExitType.IMMEDIATE)
        reason = request.POST.get('reason', '')
        
        try:
            with transaction.atomic():
                exit_request = PlayerTeamExit.objects.create(
                    player=player,
                    current_team=player.team,
                    exit_type=exit_type,
                    reason=reason
                )
                
                # Tạo thông báo cho đội trưởng
                Notification.objects.create(
                    user=player.team.captain,
                    title=f"Cầu thủ {player.full_name} yêu cầu rời đội",
                    message=f"Cầu thủ {player.full_name} đã gửi yêu cầu rời đội {player.team.name}. Lý do: {reason or 'Không có lý do cụ thể'}",
                    related_url=reverse('team_detail', kwargs={'pk': player.team.pk})
                )
                
                # Gửi email cho đội trưởng
                send_notification_email(
                    subject=f"[DBP Sports] Cầu thủ {player.full_name} yêu cầu rời đội",
                    template_name='tournaments/emails/player_exit_request.html',
                    context={
                        'player': player,
                        'team': player.team,
                        'exit_request': exit_request,
                        'exit_type_display': exit_request.get_exit_type_display(),
                        'team_detail_url': request.build_absolute_uri(reverse('team_detail', kwargs={'pk': player.team.pk}))
                    },
                    recipient_list=[player.team.captain.email],
                    request=request
                )
                
            messages.success(request, "Đã gửi yêu cầu rời đội thành công! Đội trưởng sẽ xem xét và phản hồi.")
            return redirect('player_detail', pk=player.pk)
            
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
    
    context = {
        'player': player,
        'team': player.team,
        'exit_types': PlayerTeamExit.ExitType.choices
    }
    return render(request, 'tournaments/request_team_exit.html', context)


@login_required
@require_POST
def approve_team_exit(request, exit_request_pk):
    """
    View để đội trưởng duyệt yêu cầu rời đội
    """
    exit_request = get_object_or_404(PlayerTeamExit, pk=exit_request_pk)
    
    # Kiểm tra quyền: chỉ đội trưởng mới có thể duyệt
    if request.user != exit_request.current_team.captain:
        messages.error(request, "Bạn không có quyền thực hiện hành động này.")
        return redirect('team_detail', pk=exit_request.current_team.pk)
    
    if exit_request.status != PlayerTeamExit.Status.PENDING:
        messages.error(request, "Yêu cầu này đã được xử lý.")
        return redirect('team_detail', pk=exit_request.current_team.pk)
    
    admin_notes = request.POST.get('admin_notes', '')
    
    try:
        with transaction.atomic():
            # Cập nhật trạng thái yêu cầu
            exit_request.status = PlayerTeamExit.Status.APPROVED
            exit_request.processed_by = request.user
            exit_request.processed_at = timezone.now()
            exit_request.admin_notes = admin_notes
            exit_request.save()
            
            # Xử lý rời đội
            if exit_request.exit_type == PlayerTeamExit.ExitType.IMMEDIATE:
                # Rời ngay lập tức
                player = exit_request.player
                old_team_name = player.team.name
                player.team = None
                player.save()
                
                # Tạo thông báo cho cầu thủ
                Notification.objects.create(
                    user=player.user,
                    title=f"Yêu cầu rời đội đã được duyệt",
                    message=f"Yêu cầu rời đội {old_team_name} của bạn đã được duyệt. Bạn hiện đã trở thành cầu thủ tự do.",
                    related_url=reverse('player_detail', kwargs={'pk': player.pk})
                )
                
                # Gửi email cho cầu thủ
                send_notification_email(
                    subject=f"[DBP Sports] Yêu cầu rời đội đã được duyệt",
                    template_name='tournaments/emails/player_exit_approved.html',
                    context={
                        'player': player,
                        'old_team_name': old_team_name,
                        'admin_notes': admin_notes,
                        'player_detail_url': request.build_absolute_uri(reverse('player_detail', kwargs={'pk': player.pk}))
                    },
                    recipient_list=[player.user.email],
                    request=request
                )
                
            else:
                # Rời cuối mùa giải - chỉ cập nhật trạng thái
                Notification.objects.create(
                    user=exit_request.player.user,
                    title=f"Yêu cầu rời đội đã được duyệt",
                    message=f"Yêu cầu rời đội {exit_request.current_team.name} cuối mùa giải của bạn đã được duyệt.",
                    related_url=reverse('player_detail', kwargs={'pk': exit_request.player.pk})
                )
        
        messages.success(request, f"Đã duyệt yêu cầu rời đội của {exit_request.player.full_name}.")
        
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    return redirect('team_detail', pk=exit_request.current_team.pk)


@login_required
@require_POST
def reject_team_exit(request, exit_request_pk):
    """
    View để đội trưởng từ chối yêu cầu rời đội
    """
    exit_request = get_object_or_404(PlayerTeamExit, pk=exit_request_pk)
    
    # Kiểm tra quyền: chỉ đội trưởng mới có thể từ chối
    if request.user != exit_request.current_team.captain:
        messages.error(request, "Bạn không có quyền thực hiện hành động này.")
        return redirect('team_detail', pk=exit_request.current_team.pk)
    
    if exit_request.status != PlayerTeamExit.Status.PENDING:
        messages.error(request, "Yêu cầu này đã được xử lý.")
        return redirect('team_detail', pk=exit_request.current_team.pk)
    
    admin_notes = request.POST.get('admin_notes', '')
    
    try:
        with transaction.atomic():
            # Cập nhật trạng thái yêu cầu
            exit_request.status = PlayerTeamExit.Status.REJECTED
            exit_request.processed_by = request.user
            exit_request.processed_at = timezone.now()
            exit_request.admin_notes = admin_notes
            exit_request.save()
            
            # Tạo thông báo cho cầu thủ
            Notification.objects.create(
                user=exit_request.player.user,
                title=f"Yêu cầu rời đội bị từ chối",
                message=f"Yêu cầu rời đội {exit_request.current_team.name} của bạn đã bị từ chối. Ghi chú: {admin_notes or 'Không có ghi chú'}",
                related_url=reverse('player_detail', kwargs={'pk': exit_request.player.pk})
            )
            
            # Gửi email cho cầu thủ
            send_notification_email(
                subject=f"[DBP Sports] Yêu cầu rời đội bị từ chối",
                template_name='tournaments/emails/player_exit_rejected.html',
                context={
                    'player': exit_request.player,
                    'team': exit_request.current_team,
                    'admin_notes': admin_notes,
                    'player_detail_url': request.build_absolute_uri(reverse('player_detail', kwargs={'pk': exit_request.player.pk}))
                },
                recipient_list=[exit_request.player.user.email],
                request=request
            )
        
        messages.success(request, f"Đã từ chối yêu cầu rời đội của {exit_request.player.full_name}.")
        
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    return redirect('team_detail', pk=exit_request.current_team.pk)


@login_required
@require_POST
def cancel_team_exit(request, exit_request_pk):
    """
    View để cầu thủ hủy yêu cầu rời đội
    """
    exit_request = get_object_or_404(PlayerTeamExit, pk=exit_request_pk)
    
    # Kiểm tra quyền: chỉ cầu thủ đó mới có thể hủy
    if exit_request.player.user != request.user:
        messages.error(request, "Bạn không có quyền thực hiện hành động này.")
        return redirect('player_detail', pk=exit_request.player.pk)
    
    if exit_request.status != PlayerTeamExit.Status.PENDING:
        messages.error(request, "Yêu cầu này đã được xử lý, không thể hủy.")
        return redirect('player_detail', pk=exit_request.player.pk)
    
    try:
        exit_request.status = PlayerTeamExit.Status.CANCELLED
        exit_request.save()
        
        # Tạo thông báo cho đội trưởng
        Notification.objects.create(
            user=exit_request.current_team.captain,
            title=f"Cầu thủ {exit_request.player.full_name} đã hủy yêu cầu rời đội",
            message=f"Cầu thủ {exit_request.player.full_name} đã hủy yêu cầu rời đội {exit_request.current_team.name}.",
            related_url=reverse('team_detail', kwargs={'pk': exit_request.current_team.pk})
        )
        
        messages.success(request, "Đã hủy yêu cầu rời đội thành công.")
        
    except Exception as e:
        messages.error(request, f"Có lỗi xảy ra: {str(e)}")
    
    return redirect('player_detail', pk=exit_request.player.pk)
