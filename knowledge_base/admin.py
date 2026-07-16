from django.contrib import admin
from .models import Article


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'category', 'status', 'is_internal', 'views_count', 'helpful_count', 'updated_at')
    list_filter = ('status', 'department', 'category', 'is_internal')
    search_fields = ('title', 'summary', 'content', 'tags')