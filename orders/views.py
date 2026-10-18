from datetime import timedelta
from decimal import Decimal
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from inventory.models import Category, Product
from sales.models import Receipt, Sale
from sales.services import create_receipt

from .forms import (
    BusinessPaymentInfoForm,
    CustomerSignUpForm,
    OrderDeliveryForm,
    PaymentProofForm,
)
from .models import (
    BusinessPaymentInfo,
    CustomerProfile,
    Order,
    OrderItem,
    PaymentProof,
)


CART_SESSION_KEY = "cart"


# ============================================================
# PERMISSION HELPERS
# ============================================================

def is_customer(user):
    return user.groups.filter(name="customer").exists()


def can_manage_orders(user):
    return (
        user.groups.filter(name="owner").exists()
        or user.groups.filter(name="employee").exists()
    )


# ============================================================
# PUBLIC PRODUCT CATALOG
# ============================================================

def shop_products(category=None, query=""):
    """Products shown in the shop.

    Ordering: Hot, then Standard, then the rest; inside each group the
    best sellers of the last 30 days come first, then by name.
    Stock is never used to hide or reorder products.
    """

    since = timezone.now() - timedelta(days=30)

    qs = (
        Product.objects.filter(show_in_shop=True)
        .select_related("category")
        .prefetch_related("photos", "colors")
        .annotate(
            sold_30=Coalesce(
                Sum("sales__quantity", filter=Q(sales__date__gte=since)),
                0,
            ),
            tier_rank=Case(
                When(tier="hot", then=Value(0)),
                When(tier="standard", then=Value(1)),
                default=Value(2),
                output_field=IntegerField(),
            ),
        )
        .order_by("tier_rank", "-sold_30", "item_name")
    )

    if category:
        qs = qs.filter(category=category)

    if query:
        qs = qs.filter(
            Q(item_name__icontains=query)
            | Q(brand__icontains=query)
            | Q(specification__icontains=query)
            | Q(category__name__icontains=query)
        )

    return qs


def product_catalog(request):

    categories = Category.objects.annotate(
        n=Count("products", filter=Q(products__show_in_shop=True))
    ).filter(n__gt=0)
    total_products = Product.objects.filter(show_in_shop=True).count()

    selected = None
    c = request.GET.get("c", "")
    if c.isdigit():
        selected = categories.filter(id=int(c)).first()

    query = request.GET.get("q", "").strip()

    page = Paginator(shop_products(selected, query), 12).get_page(
        request.GET.get("page")
    )

    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "orders/catalog.html",
        {
            "page": page,
            "products": page.object_list,
            "categories": categories,
            "total_products": total_products,
            "selected_category": selected,
            "query": query,
            "querystring": params.urlencode(),
            "is_home": not selected and not query and page.number == 1,
        },
    )


def product_detail(request, product_id):

    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related(
            "photos", "specs", "colors"
        ),
        id=product_id,
        show_in_shop=True,
    )

    related = (
        shop_products(product.category).exclude(id=product.id)[:4]
        if product.category_id
        else []
    )

    return render(
        request,
        "orders/product_detail.html",
        {
            "product": product,
            "related": related,
        },
    )


# ============================================================
# CUSTOMER SIGN UP
# ============================================================

def customer_signup(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = CustomerSignUpForm(request.POST)

        if form.is_valid():

            customer_group, _ = Group.objects.get_or_create(
                name="customer"
            )

            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password1"],
            )

            user.groups.add(customer_group)
            user.save()

            CustomerProfile.objects.update_or_create(
                user=user,
                defaults={"phone": form.cleaned_data["phone"]},
            )

            # Keep the validated phone available for the current
            # session until a customer profile system is added.
            request.session["customer_phone"] = (
                form.cleaned_data["phone"]
            )

            request.session.modified = True

            login(request, user)

            messages.success(
                request,
                "Account created. Welcome!",
            )

            return redirect("product_catalog")

    else:

        form = CustomerSignUpForm()

    return render(
        request,
        "orders/signup.html",
        {
            "form": form,
        },
    )


# ============================================================
# CART HELPERS
# ============================================================

def _get_cart(request):

    return request.session.setdefault(
        CART_SESSION_KEY,
        {}
    )


def _cart_key(product_id, color=""):
    return f"{product_id}|{color}" if color else str(product_id)


def _split_cart_key(key):
    pid, _, color = str(key).partition("|")
    return pid, color


def _build_cart_items(request):
    """
    Convert the session cart into complete product information
    that can be displayed on cart and checkout pages.
    """

    cart = _get_cart(request)

    items = []
    total = Decimal("0.00")

    for key, quantity in cart.items():

        product_id, color = _split_cart_key(key)

        product = Product.objects.filter(
            id=product_id
        ).first()

        if not product:
            continue

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        price = product.shop_price
        amount = price * quantity

        total += amount

        items.append(
            {
                "product": product,
                "quantity": quantity,
                "price": price,
                "amount": amount,
                "color": color,
                "key": key,
            }
        )

    return items, total


# ============================================================
# CART
# ============================================================

def _safe_next(request, default="product_catalog"):
    target = request.POST.get("next", "")
    if target and url_has_allowed_host_and_scheme(
        target, allowed_hosts={request.get_host()}
    ):
        return redirect(target)
    return redirect(default)


def _staff_blocked(request):
    """Staff (owner/employee) cannot shop; tell them kindly."""
    if request.user.is_authenticated and not is_customer(request.user):
        messages.info(
            request,
            "Staff accounts cannot place orders. "
            "Please use a customer account to shop.",
        )
        return True
    return False


def add_to_cart(request, product_id):

    if _staff_blocked(request):
        return redirect("product_catalog")

    product = get_object_or_404(
        Product,
        id=product_id
    )

    if request.method == "POST":

        try:
            quantity = int(
                request.POST.get(
                    "quantity",
                    1,
                )
            )
        except (TypeError, ValueError):
            quantity = 1

        if quantity <= 0:

            messages.error(
                request,
                "Quantity must be at least 1.",
            )

            return _safe_next(request)

        color = request.POST.get("color", "").strip()
        colors = list(product.colors.values_list("name", flat=True))

        if colors:
            if color not in colors:
                color = colors[0]
        else:
            color = ""

        key = _cart_key(product_id, color)
        cart = _get_cart(request)

        try:
            current = int(cart.get(key, 0))
        except (TypeError, ValueError):
            current = 0

        cart[key] = current + quantity

        request.session.modified = True

        label = f"{product.item_name} ({color})" if color else product.item_name
        messages.success(
            request,
            f"Added {label} to your cart.",
        )

    return _safe_next(request)


def view_cart(request):

    if _staff_blocked(request):
        return redirect("product_catalog")

    items, total = _build_cart_items(request)

    return render(
        request,
        "orders/cart.html",
        {
            "items": items,
            "total": total,
        },
    )


def remove_from_cart(request, product_id):

    if _staff_blocked(request):
        return redirect("product_catalog")

    cart = _get_cart(request)

    color = request.POST.get("color") or request.GET.get("c", "")

    cart.pop(
        _cart_key(product_id, color),
        None,
    )

    request.session.modified = True

    return redirect("view_cart")


# ============================================================
# CHECKOUT -> CREATE ORDER
# ============================================================

def checkout(request):

    # The account is only asked for here, at the last step.
    if not request.user.is_authenticated:
        messages.info(
            request,
            "Sign in or create an account to place your order. "
            "Your cart is saved.",
        )
        return redirect(
            f"{reverse('login')}?role=customer"
            f"&next={reverse('checkout')}"
        )

    if _staff_blocked(request):
        return redirect("product_catalog")

    cart = _get_cart(request)

    if not cart:

        messages.error(
            request,
            "Your cart is empty.",
        )

        return redirect("product_catalog")

    cart_items, cart_total = _build_cart_items(request)

    if not cart_items:

        messages.error(
            request,
            "Your cart contains no valid products.",
        )

        request.session[CART_SESSION_KEY] = {}
        request.session.modified = True

        return redirect("product_catalog")

    if request.method == "POST":

        form = OrderDeliveryForm(request.POST)

        if form.is_valid():

            try:

                with transaction.atomic():

                    order = form.save(
                        commit=False
                    )

                    order.customer = request.user

                    # Build the complete delivery address from
                    # the structured checkout fields.
                    order.delivery_address = (
                        f"District: "
                        f"{form.cleaned_data['district']}; "
                        f"Sector: "
                        f"{form.cleaned_data['sector']}; "
                        f"Cell/Village: "
                        f"{form.cleaned_data['cell_village']}; "
                        f"Detailed Address: "
                        f"{form.cleaned_data['detailed_address']}"
                    )

                    order.save()

                    # Keep the phone on the account for next time.
                    profile, _ = CustomerProfile.objects.get_or_create(
                        user=request.user
                    )
                    if not profile.phone:
                        profile.phone = order.delivery_phone
                        profile.save(update_fields=["phone"])

                    # Re-read the cart from the session and validate
                    # every product before creating order items.
                    for cart_key, quantity in cart.items():

                        product_id, color = _split_cart_key(cart_key)

                        product = get_object_or_404(
                            Product,
                            id=product_id,
                        )

                        try:
                            quantity = int(quantity)
                        except (TypeError, ValueError):

                            raise ValidationError(
                                "Invalid quantity in your cart."
                            )

                        if quantity <= 0:

                            raise ValidationError(
                                (
                                    f"Invalid quantity for "
                                    f"{product.item_name}."
                                )
                            )

                        item = OrderItem(
                            order=order,
                            product=product,
                            quantity=quantity,
                            price=product.shop_price,
                            color=color,
                        )

                        item.full_clean()
                        item.save()

                    request.session[CART_SESSION_KEY] = {}
                    request.session.modified = True

                messages.success(
                    request,
                    (
                        f"Order {order.order_number} "
                        "was created successfully."
                    ),
                )

                return redirect(
                    "order_payment",
                    order_id=order.id,
                )

            except ValidationError as error:

                if hasattr(error, "message_dict"):

                    for field, msgs in error.message_dict.items():

                        for msg in msgs:

                            form.add_error(
                                None,
                                msg,
                            )

                elif hasattr(error, "messages"):

                    for msg in error.messages:

                        form.add_error(
                            None,
                            msg,
                        )

                else:

                    form.add_error(
                        None,
                        str(error),
                    )

    else:

        # Pre-fill from the logged-in customer's account.
        profile = getattr(request.user, "customer_profile", None)

        initial_data = {
            "customer_name": request.user.get_full_name(),
            "delivery_email": request.user.email,
            "delivery_phone": (
                profile.phone
                if profile and profile.phone
                else request.session.get("customer_phone", "")
            ),
        }

        form = OrderDeliveryForm(
            initial=initial_data
        )

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "cart_items": cart_items,
            "cart_total": cart_total,
            "items": cart_items,
            "total": cart_total,
        },
    )


# ============================================================
# ORDER PAYMENT PAGE
# ============================================================

@login_required
def order_payment(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    if (
        order.customer != request.user
        and not can_manage_orders(request.user)
    ):
        raise PermissionDenied

    payment_info = BusinessPaymentInfo.get_solo()

    if (
        request.method == "POST"
        and order.status == "pending"
    ):

        form = PaymentProofForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():

            proof = form.save(
                commit=False
            )

            proof.order = order

            proof.save()

            messages.success(
                request,
                (
                    "Proof of payment submitted. "
                    "We'll confirm it shortly."
                ),
            )

            return redirect("my_orders")

    else:

        form = PaymentProofForm()

    return render(
        request,
        "orders/order_payment.html",
        {
            "order": order,
            "payment_info": payment_info,
            "form": form,
        },
    )


# ============================================================
# PRIVATE DOWNLOAD OF A PAYMENT PROOF
# Only the customer who owns the order, the owner and employees.
# ============================================================

@login_required
def payment_proof_file(request, proof_id):

    proof = get_object_or_404(
        PaymentProof.objects.select_related("order"),
        id=proof_id,
    )

    if (
        proof.order.customer != request.user
        and not can_manage_orders(request.user)
    ):
        raise PermissionDenied

    try:
        return FileResponse(
            proof.proof_file.open("rb"),
        )
    except (FileNotFoundError, ValueError):
        raise Http404("The uploaded file is no longer available.")


# ============================================================
# CUSTOMER ORDER LIST
# ============================================================

@login_required
def my_orders(request):

    if not is_customer(request.user):
        raise PermissionDenied

    orders = (
        Order.objects
        .filter(customer=request.user)
        .prefetch_related(
            "items",
            "payment_proofs",
        )
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/my_orders.html",
        {
            "orders": orders,
        },
    )


# ============================================================
# STAFF ORDER DETAIL (everything an employee/owner needs)
# ============================================================

def _staff_order_context(order):
    """Customer, items (with stock check) and history for one order."""

    customer = order.customer
    profile = getattr(customer, "customer_profile", None)

    rows = []
    can_mark_paid = True

    for item in order.items.select_related("product"):

        stock = item.product.current_stock
        short = stock < item.quantity

        if short:
            can_mark_paid = False

        rows.append(
            {
                "item": item,
                "stock": stock,
                "short": short,
                "missing": max(0, item.quantity - stock),
            }
        )

    other_orders = Order.objects.filter(customer=customer)

    spent = sum(
        (
            o.total
            for o in other_orders.filter(
                status__in=["paid", "delivered"]
            ).prefetch_related("items")
        ),
        0,
    )

    return {
        "order": order,
        "customer": customer,
        "profile": profile,
        "rows": rows,
        "can_mark_paid": can_mark_paid,
        "receipt": Receipt.objects.filter(
            order_number=order.order_number
        ).first(),
        "orders_count": other_orders.count(),
        "spent": spent,
        "previous_orders": (
            other_orders.exclude(id=order.id)
            .order_by("-created_at")[:5]
        ),
    }


# ============================================================
# ORDER DETAIL
# ============================================================

@login_required
def order_detail(request, order_id):

    order = get_object_or_404(
        Order.objects.prefetch_related(
            "items",
            "payment_proofs",
        ),
        id=order_id,
    )

    if (
        order.customer != request.user
        and not can_manage_orders(request.user)
    ):
        raise PermissionDenied

    if can_manage_orders(request.user):
        return render(
            request,
            "orders/staff_order_detail.html",
            _staff_order_context(order),
        )

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
            "receipt": Receipt.objects.filter(
                order_number=order.order_number
            ).first(),
        },
    )


# ============================================================
# ORDER RECEIPT (customer who ordered, or staff)
# ============================================================

@login_required
def order_receipt(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    if (
        order.customer != request.user
        and not can_manage_orders(request.user)
    ):
        raise PermissionDenied

    receipt = Receipt.objects.filter(
        order_number=order.order_number
    ).first()

    if receipt is None:
        messages.info(
            request,
            "Your receipt will be ready once your payment is confirmed.",
        )
        return redirect("order_detail", order_id=order.id)

    return render(
        request,
        "sales/receipt_print.html",
        {
            "receipt": receipt,
            "lines": receipt.lines,
            "payments": receipt.payments.all(),
            "size": "80" if request.GET.get("size") == "80" else "a4",
            "back_url": reverse("order_detail", args=[order.id]),
            "back_label": "Back to order",
        },
    )


# ============================================================
# CANCEL ORDER
# ============================================================

@login_required
def cancel_order(request, order_id):

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    if (
        order.customer != request.user
        and not can_manage_orders(request.user)
    ):
        raise PermissionDenied

    if order.status != "pending":

        messages.error(
            request,
            "Only pending orders can be cancelled.",
        )

        return redirect(
            "order_detail",
            order_id=order.id,
        )

    if request.method == "POST":

        order.status = "cancelled"

        order.save(
            update_fields=["status"]
        )

        messages.success(
            request,
            f"Order {order.order_number} cancelled.",
        )

    if is_customer(request.user):
        return redirect("my_orders")

    return redirect("manage_orders")


# ============================================================
# STAFF: MANAGE ORDERS
# ============================================================

@login_required
def manage_orders(request):

    if not can_manage_orders(request.user):
        raise PermissionDenied

    orders = (
        Order.objects
        .select_related(
            "customer",
            "customer__customer_profile",
            "processed_by",
        )
        .prefetch_related(
            "items__product",
            "payment_proofs",
        )
        .order_by("-created_at")
    )

    query = request.GET.get("q", "").strip()

    if query:
        orders = orders.filter(
            Q(order_number__icontains=query)
            | Q(customer_name__icontains=query)
            | Q(customer__username__icontains=query)
            | Q(customer__first_name__icontains=query)
            | Q(customer__last_name__icontains=query)
            | Q(delivery_phone__icontains=query)
            | Q(delivery_email__icontains=query)
        )

    status = request.GET.get(
        "status",
        "pending",
    )

    valid_statuses = {
        "pending",
        "paid",
        "delivered",
        "cancelled",
        "all",
    }

    if status not in valid_statuses:
        status = "pending"

    if status != "all":
        orders = orders.filter(
            status=status
        )

    return render(
        request,
        "orders/manage_orders.html",
        {
            "orders": orders,
            "selected_status": status,
            "query": query,
        },
    )

# ============================================================
# STAFF: MARK ORDER PAID
# ============================================================

@login_required
def mark_order_paid(request, order_id):

    if not can_manage_orders(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect("manage_orders")

    try:

        with transaction.atomic():

            order = get_object_or_404(
                Order.objects
                .select_for_update()
                .prefetch_related("items"),
                id=order_id,
            )

            if order.status != "pending":

                messages.error(
                    request,
                    (
                        f"Order {order.order_number} "
                        "has already been processed."
                    ),
                )

                return redirect("manage_orders")

            # ------------------------------------------------
            # Find the latest payment proof
            # ------------------------------------------------

            latest_proof = (
                order.payment_proofs
                .order_by("-uploaded_at")
                .first()
            )

            payment_method = "other"

            if latest_proof and latest_proof.payment_method:
                payment_method = latest_proof.payment_method

            # ------------------------------------------------
            # Create sales records for the paid order
            # ------------------------------------------------

            lines = [
                (item.product, item.quantity, item.price)
                for item in order.items.all()
            ]

            # One receipt for the whole order, paid in full.
            # This also reduces the stock of every product.
            create_receipt(
                user=request.user,
                lines=lines,
                paid=sum(
                    (q * pr for _, q, pr in lines), Decimal(0)
                ),
                method=payment_method,
                customer_name=(
                    order.contact_name
                    or order.customer.get_full_name()
                    or order.customer.username
                ),
                customer_email=order.contact_email,
                customer_phone=order.delivery_phone,
                order_number=order.order_number,
            )

            # ------------------------------------------------
            # Update order
            # ------------------------------------------------

            order.status = "paid"
            order.processed_by = request.user
            order.paid_at = timezone.now()

            order.save(
                update_fields=[
                    "status",
                    "processed_by",
                    "paid_at",
                ]
            )

        messages.success(
            request,
            (
                f"Order {order.order_number} "
                "has been marked as paid."
            ),
        )

    except ValidationError as error:

        if hasattr(error, "message_dict"):

            for field, msgs in error.message_dict.items():

                for msg in msgs:

                    messages.error(
                        request,
                        msg,
                    )

        elif hasattr(error, "messages"):

            for msg in error.messages:

                messages.error(
                    request,
                    msg,
                )

        else:

            messages.error(
                request,
                str(error),
            )

    return redirect("manage_orders")


# ============================================================
# STAFF: MARK ORDER DELIVERED
# ============================================================

@login_required
def mark_order_delivered(request, order_id):

    if not can_manage_orders(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect("manage_orders")

    order = get_object_or_404(
        Order,
        id=order_id,
    )

    if order.status != "paid":

        messages.error(
            request,
            (
                f"Order {order.order_number} must be paid "
                "before it can be marked as delivered."
            ),
        )

        return redirect("manage_orders")

    order.status = "delivered"
    order.processed_by = request.user
    order.delivered_at = timezone.now()

    order.save(
        update_fields=[
            "status",
            "processed_by",
            "delivered_at",
        ]
    )

    messages.success(
        request,
        (
            f"Order {order.order_number} "
            "has been marked as delivered."
        ),
    )

    return redirect("manage_orders")


# ============================================================
# OWNER: PAYMENT SETTINGS
# ============================================================

@login_required
def payment_settings(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    payment_info = BusinessPaymentInfo.get_solo()

    if request.method == "POST":

        form = BusinessPaymentInfoForm(
            request.POST,
            instance=payment_info,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Payment settings updated successfully.",
            )

            return redirect("payment_settings")

    else:

        form = BusinessPaymentInfoForm(
            instance=payment_info
        )

    return render(
        request,
        "orders/payment_settings.html",
        {
            "form": form,
            "payment_info": payment_info,
        },
    )