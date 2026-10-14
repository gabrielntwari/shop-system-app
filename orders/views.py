
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from inventory.models import Product
from sales.models import Sale

from .forms import (
    BusinessPaymentInfoForm,
    CustomerSignUpForm,
    OrderDeliveryForm,
    PaymentProofForm,
)
from .models import (
    BusinessPaymentInfo,
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

def product_catalog(request):

    products = Product.objects.all().order_by("item_name")

    return render(
        request,
        "orders/catalog.html",
        {
            "products": products,
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


def _build_cart_items(request):
    """
    Convert the session cart into complete product information
    that can be displayed on cart and checkout pages.
    """

    cart = _get_cart(request)

    items = []
    total = Decimal("0.00")

    for product_id, quantity in cart.items():

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

        price = product.minimum_selling_price
        amount = price * quantity

        total += amount

        items.append(
            {
                "product": product,
                "quantity": quantity,
                "price": price,
                "amount": amount,
            }
        )

    return items, total


# ============================================================
# CART
# ============================================================

@login_required
def add_to_cart(request, product_id):

    if not is_customer(request.user):
        raise PermissionDenied

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

            return redirect("product_catalog")

        current_cart_quantity = _get_cart(request).get(
            str(product_id),
            0,
        )

        try:
            current_cart_quantity = int(
                current_cart_quantity
            )
        except (TypeError, ValueError):
            current_cart_quantity = 0

        requested_total_quantity = (
            current_cart_quantity + quantity
        )

        if requested_total_quantity > product.current_stock:

            messages.error(
                request,
                (
                    f"Only {product.current_stock} units "
                    f"of {product.item_name} are available."
                ),
            )

            return redirect("product_catalog")

        cart = _get_cart(request)

        cart[str(product_id)] = requested_total_quantity

        request.session.modified = True

        messages.success(
            request,
            f"Added {product.item_name} to your cart.",
        )

    return redirect("product_catalog")


@login_required
def view_cart(request):

    if not is_customer(request.user):
        raise PermissionDenied

    items, total = _build_cart_items(request)

    return render(
        request,
        "orders/cart.html",
        {
            "items": items,
            "total": total,
        },
    )


@login_required
def remove_from_cart(request, product_id):

    if not is_customer(request.user):
        raise PermissionDenied

    cart = _get_cart(request)

    cart.pop(
        str(product_id),
        None,
    )

    request.session.modified = True

    return redirect("view_cart")


# ============================================================
# CHECKOUT -> CREATE ORDER
# ============================================================

@login_required
def checkout(request):

    if not is_customer(request.user):
        raise PermissionDenied

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

                    # Re-read the cart from the session and validate
                    # every product before creating order items.
                    for product_id, quantity in cart.items():

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
                            price=product.minimum_selling_price,
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

        # Pre-fill email from the logged-in customer's account.
        initial_data = {
            "delivery_email": request.user.email,
        }

        # If the phone was supplied during signup, use it here.
        signup_phone = request.session.get(
            "customer_phone",
            "",
        )

        if signup_phone:
            initial_data["delivery_phone"] = signup_phone

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

    return render(
        request,
        "orders/order_detail.html",
        {
            "order": order,
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
            "processed_by",
        )
        .prefetch_related(
            "items",
            "payment_proofs",
        )
        .order_by("-created_at")
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

            for item in order.items.all():

                sale = Sale(
                    product=item.product,
                    employee=request.user,
                    quantity=item.quantity,
                    selling_price=item.price,
                    customer_name=(
                        order.customer.get_full_name()
                        or order.customer.username
                    ),
                    customer_phone=order.delivery_phone,
                    payment_status="paid",
                    payment_method=payment_method,
                )

                sale.full_clean()
                sale.save()

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
