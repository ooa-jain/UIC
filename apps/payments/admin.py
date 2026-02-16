from django.contrib import admin
from .models import Payment, Escrow, Invoice


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['project', 'company', 'student', 'amount', 'status',
                   'created_at', 'released_at']
    list_filter = ['status', 'created_at', 'released_at']
    search_fields = ['project__title', 'company__name', 'student__user__username',
                    'transaction_id']
    raw_id_fields = ['project', 'company', 'student', 'milestone']
    date_hierarchy = 'created_at'


@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    list_display = ['payment', 'hold_amount', 'platform_fee', 'release_amount',
                   'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    raw_id_fields = ['payment']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'payment', 'total_amount', 'is_paid',
                   'issued_date', 'due_date']
    list_filter = ['is_paid', 'issued_date', 'due_date']
    search_fields = ['invoice_number']
    raw_id_fields = ['payment']
    date_hierarchy = 'issued_date'