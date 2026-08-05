import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from auditlogs.utils import log_activity
from departments.models import Department
from .models import Article
from departments.utils import get_department_category_map

MANAGE_ROLES = ['ADMIN', 'SUPER_ADMIN']


@login_required
def knowledge_base_list(request):

    if request.user.role == 'SUPER_ADMIN':
        return redirect('dashboard')

    status = request.GET.get('status', 'PUBLISHED')
    department_id = request.GET.get('department', '')
    category = request.GET.get('category', '')
    query = request.GET.get('q', '').strip()

    articles = Article.objects.filter(
        tenant=request.user.tenant
    ).select_related('department')

    if request.user.role not in MANAGE_ROLES:
        articles = articles.filter(is_internal=False)
        articles = articles.filter(status='PUBLISHED')
    else:
        if status in ['DRAFT', 'PUBLISHED', 'ARCHIVED']:
            articles = articles.filter(status=status)

    if department_id:
        articles = articles.filter(department_id=department_id)

    if category:
        articles = articles.filter(category=category)

    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__icontains=query)
        )

    departments = Department.objects.filter(
        is_active=True, tenant=request.user.tenant
    ).order_by('name')

    return render(
        request,
        'knowledge_base/knowledge_base_list.html',
        {
            'articles': articles,
            'departments': departments,
            'category_choices': Article.CATEGORY_CHOICES,
            'selected_status': status,
            'selected_department': str(department_id),
            'selected_category': category,
            'query': query,
            'can_manage': request.user.role in MANAGE_ROLES,
        }
    )


@login_required
def article_detail(request, article_id):

    article = get_object_or_404(
        Article, id=article_id, tenant=request.user.tenant
    )

    if article.is_internal and request.user.role not in MANAGE_ROLES:
        return redirect('knowledge_base_list')

    if article.status != 'PUBLISHED' and request.user.role not in MANAGE_ROLES:
        return redirect('knowledge_base_list')

    viewed_articles = request.session.get('kb_viewed_articles', [])

    if article.id not in viewed_articles:
        article.views_count += 1
        article.save(update_fields=['views_count'])
        viewed_articles.append(article.id)
        request.session['kb_viewed_articles'] = viewed_articles

    helpful_articles = request.session.get('kb_helpful_articles', [])
    already_marked_helpful = article.id in helpful_articles

    return render(
        request,
        'knowledge_base/article_detail.html',
        {
            'article': article,
            'already_marked_helpful': already_marked_helpful,
            'can_manage': request.user.role in MANAGE_ROLES,
        }
    )

@login_required
def faq_list(request):

    if request.user.role == 'SUPER_ADMIN':
        return redirect('dashboard')

    query = request.GET.get('q', '').strip()
    topic = request.GET.get('topic', '').strip()

    articles = Article.objects.filter(
        status='PUBLISHED', tenant=request.user.tenant
    )

    if request.user.role not in MANAGE_ROLES:
        articles = articles.filter(is_internal=False)

    if topic:
        articles = articles.filter(tags=topic)

    if query:
        articles = articles.filter(
            Q(title__icontains=query) |
            Q(summary__icontains=query) |
            Q(content__icontains=query) |
            Q(tags__icontains=query)
        )

    topics_qs = Article.objects.filter(
        status='PUBLISHED', tenant=request.user.tenant
    )

    if request.user.role not in MANAGE_ROLES:
        topics_qs = topics_qs.filter(is_internal=False)

    topics = topics_qs.exclude(tags='').values_list('tags', flat=True).distinct().order_by('tags')

    return render(
        request,
        'knowledge_base/faq_list.html',
        {
            'articles': articles.order_by('title'),
            'topics': topics,
            'selected_topic': topic,
            'query': query,
            'can_manage': request.user.role in MANAGE_ROLES,
        }
    )


@login_required
def article_form(request, article_id=None):

    if request.user.role not in MANAGE_ROLES:
        return redirect('knowledge_base_list')

    article = None

    if article_id:
        article = get_object_or_404(
            Article, id=article_id, tenant=request.user.tenant
        )

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()
        summary = request.POST.get('summary', '').strip()
        content = request.POST.get('content', '').strip()
        department_id = request.POST.get('department') or None
        category = request.POST.get('category', '').strip()
        status = request.POST.get('status', 'DRAFT')
        is_internal = request.POST.get('is_internal') == 'on'
        tags = request.POST.get('tags', '').strip()

        if not title:
            messages.error(request, 'Article title is required.')
            return redirect(request.path)

        if not content:
            messages.error(request, 'Article content is required.')
            return redirect(request.path)

        if article:

            article.title = title
            article.summary = summary
            article.content = content
            article.department_id = department_id
            article.category = category
            article.status = status
            article.is_internal = is_internal
            article.tags = tags
            article.save()

            log_activity(
                actor=request.user,
                action='knowledge_base.article_updated',
                action_label='Knowledge base article updated',
                module='KNOWLEDGE_BASE',
                target=article.title,
                severity='INFO',
            )

            messages.success(request, f"Article '{title}' updated.")

        else:

            article = Article.objects.create(
                title=title,
                summary=summary,
                content=content,
                department_id=department_id,
                category=category,
                status=status,
                is_internal=is_internal,
                tags=tags,
                created_by=request.user,
                tenant=request.user.tenant,
            )

            log_activity(
                actor=request.user,
                action='knowledge_base.article_created',
                action_label='Knowledge base article created',
                module='KNOWLEDGE_BASE',
                target=article.title,
                severity='INFO',
            )

            messages.success(request, f"Article '{title}' created.")

        return redirect('knowledge_base_list')

    departments = Department.objects.filter(
        is_active=True, tenant=request.user.tenant
    ).order_by('name')

    department_category_map = get_department_category_map()

    return render(
        request,
        'knowledge_base/article_form.html',
        {
            'article': article,
            'departments': departments,
            'department_category_map': json.dumps(department_category_map),
        }
    )


@login_required
@require_POST
def delete_article(request, article_id):

    if request.user.role not in MANAGE_ROLES:
        return redirect('knowledge_base_list')

    article = get_object_or_404(
        Article, id=article_id, tenant=request.user.tenant
    )
    title = article.title
    article.delete()

    log_activity(
        actor=request.user,
        action='knowledge_base.article_deleted',
        action_label='Knowledge base article deleted',
        module='KNOWLEDGE_BASE',
        target=title,
        severity='CRITICAL',
    )

    messages.success(request, f"Article '{title}' deleted.")

    return redirect('knowledge_base_list')


@login_required
@require_POST
def mark_helpful(request, article_id):

    article = get_object_or_404(
        Article, id=article_id, tenant=request.user.tenant
    )

    helpful_articles = request.session.get('kb_helpful_articles', [])

    if article.id in helpful_articles:
        return JsonResponse({
            'success': False,
            'message': 'You already marked this article as helpful.',
            'helpful_count': article.helpful_count,
        })

    article.helpful_count += 1
    article.save(update_fields=['helpful_count'])

    helpful_articles.append(article.id)
    request.session['kb_helpful_articles'] = helpful_articles

    return JsonResponse({
        'success': True,
        'helpful_count': article.helpful_count,
    })


@login_required
@require_POST
def ai_generate_summary(request):

    if request.user.role not in MANAGE_ROLES:
        return JsonResponse({'success': False, 'error': 'Not allowed.'})

    try:
        data = json.loads(request.body)
        title = data.get('title', '')
        content = data.get('content', '')

        if not content.strip():
            return JsonResponse({
                'success': False,
                'error': 'Write some article content first.'
            })

        from .services.ai_service import generate_summary
        summary = generate_summary(title, content)

        return JsonResponse({
            'success': True,
            'summary': summary,
        })

    except Exception as e:

        return JsonResponse({
            'success': False,
            'error': str(e),
        })