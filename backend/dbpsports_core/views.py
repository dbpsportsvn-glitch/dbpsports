from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
import json
import logging

from .models import NewsletterSubscription

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def subscribe_newsletter(request):
    """API endpoint để đăng ký nhận thông báo newsletter"""
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        
        if not email:
            return JsonResponse({
                'success': False,
                'message': 'Vui lòng nhập địa chỉ email'
            }, status=400)
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({
                'success': False,
                'message': 'Địa chỉ email không hợp lệ'
            }, status=400)
        
        # Check if email already exists
        subscription, created = NewsletterSubscription.objects.get_or_create(
            email=email,
            defaults={
                'is_active': True,
                'subscribed_at': timezone.now()
            }
        )
        
        if not created:
            if subscription.is_active:
                return JsonResponse({
                    'success': False,
                    'message': 'Email này đã được đăng ký nhận thông báo'
                }, status=400)
            else:
                # Reactivate subscription
                subscription.is_active = True
                subscription.subscribed_at = timezone.now()
                subscription.unsubscribed_at = None
                subscription.save()
                
                logger.info(f"Newsletter subscription reactivated: {email}")
                return JsonResponse({
                    'success': True,
                    'message': 'Đăng ký nhận thông báo thành công! Cảm ơn bạn đã quan tâm.'
                })
        else:
            logger.info(f"New newsletter subscription: {email}")
            return JsonResponse({
                'success': True,
                'message': 'Đăng ký nhận thông báo thành công! Cảm ơn bạn đã quan tâm.'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Dữ liệu không hợp lệ'
        }, status=400)
    except Exception as e:
        logger.error(f"Newsletter subscription error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Có lỗi xảy ra, vui lòng thử lại sau'
        }, status=500)


def unsubscribe_newsletter(request, email):
    """Trang hủy đăng ký newsletter"""
    try:
        subscription = NewsletterSubscription.objects.get(email=email)
        subscription.unsubscribe()
        
        messages.success(request, f'Đã hủy đăng ký nhận thông báo cho email {email}')
        
    except NewsletterSubscription.DoesNotExist:
        messages.error(request, 'Email không tồn tại trong hệ thống')
    
    return render(request, 'newsletter_unsubscribed.html')


def send_newsletter_email(subject, content, subscriber_email, tournament_highlight=None):
    """
    Gửi email newsletter cho một subscriber
    """
    try:
        # Render HTML template
        html_content = render_to_string('emails/newsletter.html', {
            'subject': subject,
            'content': content,
            'subscriber_email': subscriber_email,
            'tournament_highlight': tournament_highlight
        })
        
        # Create email
        email = EmailMultiAlternatives(
            subject=subject,
            body=content,  # Plain text fallback
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[subscriber_email]
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Newsletter sent successfully to {subscriber_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send newsletter to {subscriber_email}: {str(e)}")
        return False


def send_newsletter_bulk(subject, content, tournament_highlight=None, test_mode=False):
    """
    Gửi newsletter cho tất cả subscribers hoạt động
    """
    try:
        # Lấy tất cả subscribers hoạt động
        active_subscribers = NewsletterSubscription.objects.filter(is_active=True)
        
        if test_mode:
            # Test mode - chỉ gửi cho 1 email đầu tiên
            active_subscribers = active_subscribers[:1]
            logger.info(f"Test mode: Sending newsletter to first subscriber only")
        
        success_count = 0
        total_count = active_subscribers.count()
        
        for subscriber in active_subscribers:
            if send_newsletter_email(subject, content, subscriber.email, tournament_highlight):
                success_count += 1
        
        logger.info(f"Newsletter bulk send completed: {success_count}/{total_count} successful")
        return {
            'success': True,
            'sent': success_count,
            'total': total_count,
            'failed': total_count - success_count
        }
        
    except Exception as e:
        logger.error(f"Failed to send newsletter bulk: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@login_required
@csrf_protect
def newsletter_form_view(request):
    """View hiển thị form để gửi newsletter"""
    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        content = request.POST.get('content', '').strip()
        test_mode = request.POST.get('test_mode') == 'on'
        
        if not subject or not content:
            messages.error(request, 'Vui lòng nhập đầy đủ tiêu đề và nội dung!')
        else:
            try:
                result = send_newsletter_bulk(subject, content, test_mode=test_mode)
                
                if result['success']:
                    if test_mode:
                        messages.success(request, f'✅ Gửi newsletter test thành công! Đã gửi {result["sent"]} email.')
                    else:
                        messages.success(request, f'✅ Gửi newsletter thành công! Đã gửi {result["sent"]}/{result["total"]} email.')
                else:
                    messages.error(request, f'❌ Lỗi khi gửi newsletter: {result["error"]}')
                    
            except Exception as e:
                messages.error(request, f'❌ Có lỗi xảy ra: {str(e)}')
    
    # Lấy số lượng subscribers
    active_subscribers = NewsletterSubscription.objects.filter(is_active=True).count()
    total_subscribers = NewsletterSubscription.objects.count()
    
    context = {
        'active_subscribers': active_subscribers,
        'total_subscribers': total_subscribers,
    }
    
    return render(request, 'newsletter_form.html', context)


@login_required
def newsletter_dashboard_view(request):
    """Dashboard newsletter"""
    # Lấy số lượng subscribers
    active_subscribers = NewsletterSubscription.objects.filter(is_active=True).count()
    total_subscribers = NewsletterSubscription.objects.count()
    
    context = {
        'active_subscribers': active_subscribers,
        'total_subscribers': total_subscribers,
    }
    
    return render(request, 'newsletter_dashboard.html', context)
