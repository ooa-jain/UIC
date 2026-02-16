from django.contrib import admin
from .models import Conversation, Message


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    raw_id_fields = ['participants', 'project']
    date_hierarchy = 'created_at'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'conversation', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username']
    raw_id_fields = ['conversation', 'sender']
    date_hierarchy = 'created_at'