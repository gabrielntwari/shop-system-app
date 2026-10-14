from .models import Order


def active_order_count(request):
    """
    Provides the number of active customer orders
    to owner and employee pages.

    Active orders:
    - Pending Payment
    - Paid

    Inactive orders:
    - Delivered
    - Cancelled
    """

    active_count = 0

    if request.user.is_authenticated:
        is_staff_member = (
            request.user.groups.filter(name="owner").exists()
            or request.user.groups.filter(name="employee").exists()
        )

        if is_staff_member:
            active_count = Order.objects.filter(
                status__in=["pending", "paid"]
            ).count()

    return {
        "active_order_count": active_count,
    }