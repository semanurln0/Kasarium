from .models import ContactMessage, Order


def cart_count(request):
    """Expose cart + admin notification counts to templates."""
    cart = request.session.get('shop_cart', {})
    try:
        total = sum(int(v.get('qty', 0)) for v in cart.values())
    except Exception:
        total = 0

    pending_orders_count = 0
    unread_messages_count = 0
    customer_unread_messages_count = 0
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        is_staff_side = user.is_superuser or user.groups.filter(name__in=['Admin', 'Staff']).exists()
        if is_staff_side:
            pending_orders_count = Order.objects.filter(status=Order.STATUS_PENDING).count()
            unread_messages_count = ContactMessage.objects.filter(
                is_read=False,
                deleted_for_staff=False,
            ).count()
        else:
            customer_unread_messages_count = ContactMessage.objects.filter(
                user=user,
                sent_by__isnull=False,
                read_by_customer=False,
                deleted_for_customer=False,
            ).count()

    return {
        'cart_count': total,
        'pending_orders_count': pending_orders_count,
        'unread_messages_count': unread_messages_count,
        'customer_unread_messages_count': customer_unread_messages_count,
    }
