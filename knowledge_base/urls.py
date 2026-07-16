from django.urls import path
from .views import (
    knowledge_base_list,
    article_form,
    article_detail,
    delete_article,
    mark_helpful,
    ai_generate_summary,
)

urlpatterns = [
    path('', knowledge_base_list, name='knowledge_base_list'),
    path('new/', article_form, name='kb_article_new'),
    path('<int:article_id>/', article_detail, name='kb_article_detail'),
    path('<int:article_id>/edit/', article_form, name='kb_article_edit'),
    path('<int:article_id>/delete/', delete_article, name='kb_article_delete'),
    path('<int:article_id>/helpful/', mark_helpful, name='kb_article_helpful'),
    path('ai/generate-summary/', ai_generate_summary, name='kb_ai_generate_summary'),
]
