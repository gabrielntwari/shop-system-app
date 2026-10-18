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


def shop_config(request):
    """Shop settings (contacts, socials, slides, video) for templates."""

    import os

    from django.conf import settings

    cfg = settings.SHOP

    def exists(rel):
        for base in [settings.BASE_DIR / "static"] + [
            p for p in getattr(settings, "STATICFILES_DIRS", [])
        ]:
            if os.path.exists(os.path.join(str(base), rel)):
                return True
        return False

    # Pictures and video are found automatically: put ANY image files in
    # static/shop/slides/ (shown in name order) and any .mp4/.webm video
    # (plus an optional picture for phones) in static/shop/.
    img_ext = (".jpg", ".jpeg", ".png", ".webp", ".jfif")
    vid_ext = (".mp4", ".webm", ".m4v")

    def list_files(rel_dir, exts):
        found = []
        for base in [settings.BASE_DIR / "static"] + [
            p for p in getattr(settings, "STATICFILES_DIRS", [])
        ]:
            folder = os.path.join(str(base), rel_dir)
            if os.path.isdir(folder):
                for name in sorted(os.listdir(folder), key=lambda n: n.lower()):
                    if name.lower().endswith(exts):
                        rel = (rel_dir + "/" + name) if rel_dir else name
                        if rel not in found:
                            found.append(rel)
        return found

    texts = cfg["slides"]
    slides = []
    files = list_files("shop/slides", img_ext)
    if files:
        for i, rel in enumerate(files):
            item = dict(texts[i % len(texts)]) if texts else {}
            item["image"] = settings.STATIC_URL + rel
            slides.append(item)
    else:
        for slide in texts:
            item = dict(slide)
            item["image"] = ""
            slides.append(item)

    video = cfg.get("video") or ""
    if not (video and exists(video)):
        vids = list_files("shop", vid_ext)
        video = vids[0] if vids else ""
    poster = cfg.get("video_poster") or ""
    if not (poster and exists(poster)):
        pics = list_files("shop", img_ext)
        poster = pics[0] if pics else ""

    cart_count = 0
    try:
        for qty in request.session.get("cart", {}).values():
            cart_count += int(qty)
    except (TypeError, ValueError, AttributeError):
        pass

    from inventory.models import Category

    return {
        "cart_count": cart_count,
        "footer_categories": list(Category.objects.filter(products__show_in_shop=True).distinct()[:8]),
        "SHOP": cfg,
        "shop_socials": [(k, v) for k, v in cfg["socials"].items() if v],
        "shop_slides": slides,
        "shop_video": settings.STATIC_URL + video if video and exists(video) else "",
        "shop_poster": settings.STATIC_URL + poster if poster and exists(poster) else "",
    }
