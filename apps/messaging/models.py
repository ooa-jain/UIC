from django.db import models
from apps.accounts.models import User
from apps.projects.models import Project


class Conversation(models.Model):
    """Conversation between users"""
    participants = models.ManyToManyField(User, related_name='conversations')
    project = models.ForeignKey(Project, on_delete=models.CASCADE,
                                related_name='conversations', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']

    def __str__(self):
        participants = ', '.join([p.username for p in self.participants.all()])
        return f"Conversation: {participants}"

    def get_last_message(self):
        """Get the most recent message"""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """Individual message in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE,
                                     related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')

    content = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', blank=True, null=True)

    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.created_at}"