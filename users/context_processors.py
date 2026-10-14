from .models import EmployeeMessage


def unread_message_count(request):
    """
    Number of unread employee messages, for the owner only.
    Used for the badge on the "Messages" menu link and the alert
    banner on the owner dashboard.
    """

    unread_count = 0

    user = getattr(request, "user", None)

    if (
        user is not None
        and user.is_authenticated
        and user.groups.filter(name="owner").exists()
    ):
        unread_count = EmployeeMessage.objects.filter(
            is_read=False
        ).count()

    return {
        "unread_message_count": unread_count,
    }
