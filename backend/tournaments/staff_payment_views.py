# backend/tournaments/staff_payment_views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import StaffPaymentForm, StaffPaymentStatusForm, StaffPaymentQuickForm
from .models import StaffPayment, TournamentBudget, BudgetHistory, Tournament, TournamentStaff


# ===== VIEWS CHO QUẢN LÝ TIỀN CÔNG NHÂN VIÊN =====

@login_required
def staff_payment_list(request, tournament_pk):
    """Danh sách tiền công nhân viên"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and request.user in tournament.organization.members.all()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    # Lấy danh sách staff payments
    staff_payments = StaffPayment.objects.filter(
        tournament=tournament
    ).select_related('staff_member__user', 'staff_member__role', 'role').order_by('-created_at')
    
    # Thống kê
    total_pending = staff_payments.filter(status='PENDING').aggregate(total=Sum('total_amount'))['total'] or 0
    total_paid = staff_payments.filter(status='PAID').aggregate(total=Sum('total_amount'))['total'] or 0
    total_cancelled = staff_payments.filter(status='CANCELLED').aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'tournament': tournament,
        'staff_payments': staff_payments,
        'total_pending': total_pending,
        'total_paid': total_paid,
        'total_cancelled': total_cancelled,
        'is_organizer': is_organizer,
    }
    
    return render(request, 'tournaments/staff_payment_list.html', context)


@login_required
def add_staff_payment(request, tournament_pk):
    """Thêm tiền công cho nhân viên"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and request.user in tournament.organization.members.all()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    if request.method == 'POST':
        form = StaffPaymentForm(request.POST, tournament=tournament)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.tournament = tournament
            payment.role = payment.staff_member.role
            payment.created_by = request.user
            
            # Xử lý payment_date nếu status không phải PAID
            if payment.status != 'PAID':
                payment.payment_date = None
            
            payment.save()
            
            # Ghi lịch sử budget
            budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
            BudgetHistory.objects.create(
                budget=budget,
                action='ADD_STAFF_PAYMENT',
                description=f'Thêm tiền công: {payment.staff_member.user.get_full_name()} - {payment.role.name}',
                amount=payment.total_amount,
                user=request.user
            )
            
            messages.success(request, "Đã thêm tiền công nhân viên thành công!")
            return redirect('staff_payment_list', tournament_pk=tournament.pk)
    else:
        form = StaffPaymentForm(tournament=tournament)
    
    context = {
        'tournament': tournament,
        'form': form,
        'is_organizer': is_organizer,
    }
    
    return render(request, 'tournaments/add_staff_payment.html', context)


@login_required
def add_staff_payment_quick(request, tournament_pk):
    """Thêm nhanh tiền công cho nhiều nhân viên"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and request.user in tournament.organization.members.all()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    if request.method == 'POST':
        form = StaffPaymentQuickForm(request.POST, tournament=tournament)
        if form.is_valid():
            staff_member_ids = form.cleaned_data['staff_members']
            rate_per_unit = form.cleaned_data['rate_per_unit']
            payment_unit = form.cleaned_data['payment_unit']
            number_of_units = form.cleaned_data['number_of_units']
            notes = form.cleaned_data['notes']
            
            created_count = 0
            for staff_member_id in staff_member_ids:
                staff_member = get_object_or_404(TournamentStaff, pk=staff_member_id)
                
                # Kiểm tra xem đã có payment cho staff member này chưa
                existing_payment = StaffPayment.objects.filter(
                    tournament=tournament,
                    staff_member=staff_member,
                    role=staff_member.role
                ).first()
                
                if not existing_payment:
                    payment = StaffPayment.objects.create(
                        tournament=tournament,
                        staff_member=staff_member,
                        role=staff_member.role,
                        rate_per_unit=rate_per_unit,
                        payment_unit=payment_unit,
                        number_of_units=number_of_units,
                        notes=notes,
                        created_by=request.user
                    )
                    created_count += 1
            
            if created_count > 0:
                # Ghi lịch sử budget
                budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
                BudgetHistory.objects.create(
                    budget=budget,
                    action='ADD_STAFF_PAYMENT_BATCH',
                    description=f'Thêm tiền công cho {created_count} nhân viên',
                    amount=rate_per_unit * number_of_units * created_count,
                    user=request.user
                )
                
                messages.success(request, f"Đã thêm tiền công cho {created_count} nhân viên thành công!")
            else:
                messages.warning(request, "Tất cả nhân viên đã được chọn đều đã có tiền công!")
            
            return redirect('staff_payment_list', tournament_pk=tournament.pk)
    else:
        form = StaffPaymentQuickForm(tournament=tournament)
    
    context = {
        'tournament': tournament,
        'form': form,
        'is_organizer': is_organizer,
    }
    
    return render(request, 'tournaments/add_staff_payment_quick.html', context)


@login_required
def update_staff_payment_status(request, tournament_pk, payment_pk):
    """Cập nhật trạng thái thanh toán"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    payment = get_object_or_404(StaffPayment, pk=payment_pk, tournament=tournament)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and request.user in tournament.organization.members.all()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    if request.method == 'POST':
        form = StaffPaymentStatusForm(request.POST, instance=payment)
        if form.is_valid():
            old_status = payment.status
            payment = form.save()
            
            # Ghi lịch sử budget nếu trạng thái thay đổi
            if old_status != payment.status:
                budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
                action = 'UPDATE_STAFF_PAYMENT_STATUS'
                description = f'Cập nhật trạng thái tiền công {payment.staff_member.user.get_full_name()}: {old_status} → {payment.status}'
                
                BudgetHistory.objects.create(
                    budget=budget,
                    action=action,
                    description=description,
                    amount=payment.total_amount if payment.status == 'PAID' else 0,
                    user=request.user
                )
            
            messages.success(request, "Đã cập nhật trạng thái thanh toán thành công!")
            return redirect('staff_payment_list', tournament_pk=tournament.pk)
    else:
        form = StaffPaymentStatusForm(instance=payment)
    
    context = {
        'tournament': tournament,
        'payment': payment,
        'form': form,
        'is_organizer': is_organizer,
    }
    
    return render(request, 'tournaments/update_staff_payment_status.html', context)


@login_required
def edit_staff_payment(request, tournament_pk, payment_pk):
    """Chỉnh sửa tiền công nhân viên"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    payment = get_object_or_404(StaffPayment, pk=payment_pk, tournament=tournament)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and request.user in tournament.organization.members.all()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    if request.method == 'POST':
        form = StaffPaymentForm(request.POST, instance=payment, tournament=tournament)
        if form.is_valid():
            old_amount = payment.total_amount
            old_status = payment.status
            payment = form.save()
            
            # Xử lý payment_date nếu status không phải PAID
            if payment.status != 'PAID':
                payment.payment_date = None
                payment.save()
            
            # Ghi lịch sử budget nếu số tiền hoặc trạng thái thay đổi
            if old_amount != payment.total_amount or old_status != payment.status:
                budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
                BudgetHistory.objects.create(
                    budget=budget,
                    action='UPDATE_STAFF_PAYMENT',
                    description=f'Cập nhật tiền công {payment.staff_member.user.get_full_name()}: {old_amount:,} → {payment.total_amount:,} VNĐ',
                    amount=payment.total_amount - old_amount,
                    user=request.user
                )
            
            messages.success(request, "Đã cập nhật tiền công nhân viên thành công!")
            return redirect('staff_payment_list', tournament_pk=tournament.pk)
    else:
        form = StaffPaymentForm(instance=payment, tournament=tournament)
    
    context = {
        'tournament': tournament,
        'payment': payment,
        'form': form,
        'is_organizer': is_organizer,
    }
    
    return render(request, 'tournaments/edit_staff_payment.html', context)


@login_required
@require_POST
def delete_staff_payment(request, tournament_pk, payment_pk):
    """Xóa tiền công nhân viên"""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)
    payment = get_object_or_404(StaffPayment, pk=payment_pk, tournament=tournament)
    
    # Kiểm tra quyền truy cập
    is_organizer = tournament.organization and request.user in tournament.organization.members.all()
    if not request.user.is_staff and not is_organizer:
        return HttpResponseForbidden("Bạn không có quyền truy cập trang này.")
    
    # Ghi lịch sử budget
    budget, created = TournamentBudget.objects.get_or_create(tournament=tournament)
    BudgetHistory.objects.create(
        budget=budget,
        action='DELETE_STAFF_PAYMENT',
        description=f'Xóa tiền công: {payment.staff_member.user.get_full_name()} - {payment.role.name}',
        amount=-payment.total_amount,
        user=request.user
    )
    
    payment.delete()
    messages.success(request, "Đã xóa tiền công nhân viên thành công!")
    
    return redirect('staff_payment_list', tournament_pk=tournament.pk)
