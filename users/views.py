from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.exceptions import PermissionDenied
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone

from .forms import EmployeeCreationForm, EmployeeMessageForm
from .models import EmployeeMessage

from inventory.models import Product
from purchase.models import Purchase
from sales.models import Sale
from expenses.models import Expense, OwnerWithdrawal


# =========================================================
# LOGIN
# =========================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("dashboard")

        return render(
            request,
            "users/login.html",
            {
                "error": "Invalid username or password."
            }
        )

    return render(
        request,
        "users/login.html"
    )


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    logout(request)

    return redirect("login")


# =========================================================
# DASHBOARD ROUTER
# =========================================================

@login_required
def dashboard(request):

    if request.user.groups.filter(
        name="owner"
    ).exists():

        return redirect("owner_dashboard")

    if request.user.groups.filter(
        name="employee"
    ).exists():

        return redirect("employee_dashboard")

    raise PermissionDenied


# =========================================================
# CREATE EMPLOYEE
# =========================================================

@login_required
def create_employee(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    if request.method == "POST":

        form = EmployeeCreationForm(
            request.POST
        )

        if form.is_valid():

            employee = form.save()

            employee_group = Group.objects.get(
                name="employee"
            )

            employee.groups.add(
                employee_group
            )

            return redirect(
                "employee_success"
            )

    else:

        form = EmployeeCreationForm()

    return render(
        request,
        "users/create_employee.html",
        {
            "form": form
        }
    )


# =========================================================
# EMPLOYEE SUCCESS
# =========================================================

@login_required
def employee_success(request):

    return render(
        request,
        "users/employee_success.html"
    )


# =========================================================
# OWNER DASHBOARD
# =========================================================

@login_required
def owner_dashboard(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    today = timezone.localdate()

    # =====================================================
    # TODAY'S EXPENSES
    # =====================================================

    today_expenses_queryset = Expense.objects.filter(
        date__date=today
    )

    today_withdrawals_queryset = OwnerWithdrawal.objects.filter(
        date__date=today
    )

    today_business_expenses = sum(
        expense.amount
        for expense in today_expenses_queryset
    )

    today_owner_withdrawals = sum(
        withdrawal.amount
        for withdrawal in today_withdrawals_queryset
    )

    today_expenses = (
        today_business_expenses
        + today_owner_withdrawals
    )

    # =====================================================
    # TODAY'S SALES
    # =====================================================

    today_sales = Sale.objects.filter(
        date__date=today
    )

    today_paid_sales = today_sales.filter(
        payment_status="paid"
    )

    today_credit_sales = today_sales.filter(
        payment_status="credit"
    )

    # =====================================================
    # TODAY'S PURCHASES
    # =====================================================

    today_purchases = Purchase.objects.filter(
        date__date=today
    )

    today_paid_purchases = today_purchases.filter(
        payment_status="paid"
    )

    today_credit_purchases = today_purchases.filter(
        payment_status="credit"
    )

    # =====================================================
    # BASIC SUMMARY
    # =====================================================

    total_products = Product.objects.count()

    products = Product.objects.all()

    total_stock = sum(
        product.current_stock
        for product in products
    )

    # =====================================================
    # AVAILABLE INVENTORY
    # =====================================================

    available_products = [
        product
        for product in products
        if product.current_stock > 0
    ]

    stock_selling_value = sum(
        product.current_stock
        * product.minimum_selling_price
        for product in available_products
    )

    # =====================================================
    # EMPLOYEES
    # =====================================================

    employee_count = Group.objects.get(
        name="employee"
    ).user_set.count()

    # =====================================================
    # SALES SUMMARY
    # =====================================================

    sales_count = today_sales.count()

    sales_revenue = sum(
        sale.total_sales()
        for sale in today_sales
    )

    sales_quantity = sum(
        sale.quantity
        for sale in today_sales
    )

    # =====================================================
    # PAID SALES
    # =====================================================

    paid_sales_count = today_paid_sales.count()

    paid_sales_revenue = sum(
        sale.total_sales()
        for sale in today_paid_sales
    )

    # =====================================================
    # CREDIT SALES
    # =====================================================

    credit_sales_count = today_credit_sales.count()

    credit_sales_amount = sum(
        sale.total_sales()
        for sale in today_credit_sales
    )

    credit_sales_paid = sum(
        sale.total_credit_paid
        for sale in today_credit_sales
    )

    credit_sales_outstanding = sum(
        sale.outstanding_credit
        for sale in today_credit_sales
    )

    # =====================================================
    # PURCHASE SUMMARY
    # =====================================================

    purchases_count = today_purchases.count()

    purchases_value = sum(
        purchase.total_cost
        for purchase in today_purchases
    )

    purchases_quantity = sum(
        purchase.quantity
        for purchase in today_purchases
    )

    # =====================================================
    # PAID PURCHASES
    # =====================================================

    paid_purchases_count = (
        today_paid_purchases.count()
    )

    paid_purchases_value = sum(
        purchase.total_cost
        for purchase in today_paid_purchases
    )

    # =====================================================
    # CREDIT PURCHASES
    # =====================================================

    credit_purchases_count = (
        today_credit_purchases.count()
    )

    credit_purchases_amount = sum(
        purchase.total_cost
        for purchase in today_credit_purchases
    )

    credit_purchases_paid = sum(
        purchase.total_credit_paid
        for purchase in today_credit_purchases
    )

    credit_purchases_outstanding = sum(
        purchase.outstanding_credit
        for purchase in today_credit_purchases
    )

    # =====================================================
    # ALL CUSTOMER CREDITS
    # =====================================================

    all_credit_sales = Sale.objects.filter(
        payment_status="credit"
    )

    total_sales_credit_original = sum(
        sale.total_sales()
        for sale in all_credit_sales
    )

    total_sales_credit_paid = sum(
        sale.total_credit_paid
        for sale in all_credit_sales
    )

    total_sales_credit_outstanding = sum(
        sale.outstanding_credit
        for sale in all_credit_sales
    )

    # =====================================================
    # ALL SUPPLIER CREDITS
    # =====================================================

    all_credit_purchases = Purchase.objects.filter(
        payment_status="credit"
    )

    total_purchase_credit_original = sum(
        purchase.total_cost
        for purchase in all_credit_purchases
    )

    total_purchase_credit_paid = sum(
        purchase.total_credit_paid
        for purchase in all_credit_purchases
    )

    total_purchase_credit_outstanding = sum(
        purchase.outstanding_credit
        for purchase in all_credit_purchases
    )

    # =====================================================
    # RECENT TRANSACTIONS
    # =====================================================

    recent_sales = Sale.objects.select_related(
        "product",
        "employee"
    ).all().order_by(
        "-date"
    )[:10]

    recent_purchases = Purchase.objects.select_related(
        "product",
        "employee"
    ).all().order_by(
        "-date"
    )[:10]

    recent_transactions = []

    # -----------------------------------------------------
    # SALES
    # -----------------------------------------------------

    for sale in recent_sales:

        recent_transactions.append({

            "date": sale.date,

            "type": "Sale",

            "product": sale.product.item_name,

            "employee": (
                sale.employee.username
                if sale.employee
                else "Unknown"
            ),

            "quantity": sale.quantity,

            "amount": sale.total_sales(),

            "payment_status": (
                sale.get_payment_status_display()
            ),

        })

    # -----------------------------------------------------
    # PURCHASES
    # -----------------------------------------------------

    for purchase in recent_purchases:

        recent_transactions.append({

            "date": purchase.date,

            "type": "Purchase",

            "product": purchase.product.item_name,

            "employee": (
                purchase.employee.username
                if purchase.employee
                else "Unknown"
            ),

            "quantity": purchase.quantity,

            "amount": purchase.total_cost,

            "payment_status": (
                purchase.get_payment_status_display()
            ),

        })

    recent_transactions.sort(
        key=lambda transaction: transaction["date"],
        reverse=True
    )

    recent_transactions = recent_transactions[:10]

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        # -------------------------------------------------
        # BASIC DASHBOARD
        # -------------------------------------------------

        "total_products": total_products,

        "total_stock": total_stock,

        "employee_count": employee_count,

        "stock_selling_value": stock_selling_value,

        # -------------------------------------------------
        # TODAY'S EXPENSES
        # -------------------------------------------------

        "today_expenses": today_expenses,

        "today_business_expenses": (
            today_business_expenses
        ),

        "today_owner_withdrawals": (
            today_owner_withdrawals
        ),

        # -------------------------------------------------
        # TOTAL SALES
        # -------------------------------------------------

        "today_sales": sales_count,

        "sales_count": sales_count,

        "sales_revenue": sales_revenue,

        "sales_quantity": sales_quantity,

        # -------------------------------------------------
        # PAID SALES
        # -------------------------------------------------

        "paid_sales_count": paid_sales_count,

        "paid_sales_revenue": paid_sales_revenue,

        # -------------------------------------------------
        # CREDIT SALES
        # -------------------------------------------------

        "credit_sales_count": credit_sales_count,

        "credit_sales_amount": credit_sales_amount,

        "credit_sales_paid": credit_sales_paid,

        "credit_sales_outstanding": (
            credit_sales_outstanding
        ),

        # -------------------------------------------------
        # TOTAL PURCHASES
        # -------------------------------------------------

        "today_purchases": purchases_count,

        "purchases_count": purchases_count,

        "purchases_value": purchases_value,

        "purchases_quantity": purchases_quantity,

        # -------------------------------------------------
        # PAID PURCHASES
        # -------------------------------------------------

        "paid_purchases_count": (
            paid_purchases_count
        ),

        "paid_purchases_value": (
            paid_purchases_value
        ),

        # -------------------------------------------------
        # CREDIT PURCHASES
        # -------------------------------------------------

        "credit_purchases_count": (
            credit_purchases_count
        ),

        "credit_purchases_amount": (
            credit_purchases_amount
        ),

        "credit_purchases_paid": (
            credit_purchases_paid
        ),

        "credit_purchases_outstanding": (
            credit_purchases_outstanding
        ),

        # -------------------------------------------------
        # ALL CUSTOMER CREDIT
        # -------------------------------------------------

        "total_sales_credit_original": (
            total_sales_credit_original
        ),

        "total_sales_credit_paid": (
            total_sales_credit_paid
        ),

        "total_sales_credit_outstanding": (
            total_sales_credit_outstanding
        ),

        # -------------------------------------------------
        # ALL SUPPLIER CREDIT
        # -------------------------------------------------

        "total_purchase_credit_original": (
            total_purchase_credit_original
        ),

        "total_purchase_credit_paid": (
            total_purchase_credit_paid
        ),

        "total_purchase_credit_outstanding": (
            total_purchase_credit_outstanding
        ),

        # -------------------------------------------------
        # RECENT TRANSACTIONS
        # -------------------------------------------------

        "recent_transactions": recent_transactions,
    }

    return render(
        request,
        "users/owner_dashboard.html",
        context
    )


# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

@login_required
def employee_dashboard(request):

    if not request.user.groups.filter(
        name="employee"
    ).exists():

        raise PermissionDenied

    today = timezone.localdate()

    # =====================================================
    # TODAY'S SALES
    # =====================================================

    today_sales = Sale.objects.filter(
        employee=request.user,
        date__date=today
    )

    today_paid_sales = today_sales.filter(
        payment_status="paid"
    )

    today_credit_sales = today_sales.filter(
        payment_status="credit"
    )

    # =====================================================
    # TODAY'S PURCHASES
    # =====================================================

    today_purchases = Purchase.objects.filter(
        employee=request.user,
        date__date=today
    )

    today_paid_purchases = today_purchases.filter(
        payment_status="paid"
    )

    today_credit_purchases = today_purchases.filter(
        payment_status="credit"
    )

    # =====================================================
    # SALES
    # =====================================================

    sales_count = today_sales.count()

    sales_revenue = sum(
        sale.total_sales()
        for sale in today_sales
    )

    sales_quantity = sum(
        sale.quantity
        for sale in today_sales
    )

    # =====================================================
    # PAID SALES
    # =====================================================

    paid_sales_count = today_paid_sales.count()

    paid_sales_revenue = sum(
        sale.total_sales()
        for sale in today_paid_sales
    )

    # =====================================================
    # CREDIT SALES
    # =====================================================

    credit_sales_count = today_credit_sales.count()

    credit_sales_amount = sum(
        sale.total_sales()
        for sale in today_credit_sales
    )

    credit_sales_paid = sum(
        sale.total_credit_paid
        for sale in today_credit_sales
    )

    credit_sales_outstanding = sum(
        sale.outstanding_credit
        for sale in today_credit_sales
    )

    # =====================================================
    # PURCHASES
    # =====================================================

    purchases_count = today_purchases.count()

    purchases_value = sum(
        purchase.total_cost
        for purchase in today_purchases
    )

    purchases_quantity = sum(
        purchase.quantity
        for purchase in today_purchases
    )

    # =====================================================
    # PAID PURCHASES
    # =====================================================

    paid_purchases_count = (
        today_paid_purchases.count()
    )

    paid_purchases_value = sum(
        purchase.total_cost
        for purchase in today_paid_purchases
    )

    # =====================================================
    # CREDIT PURCHASES
    # =====================================================

    credit_purchases_count = (
        today_credit_purchases.count()
    )

    credit_purchases_amount = sum(
        purchase.total_cost
        for purchase in today_credit_purchases
    )

    credit_purchases_paid = sum(
        purchase.total_credit_paid
        for purchase in today_credit_purchases
    )

    credit_purchases_outstanding = sum(
        purchase.outstanding_credit
        for purchase in today_credit_purchases
    )

    # =====================================================
    # MY CUSTOMER CREDIT
    # =====================================================

    my_credit_sales = Sale.objects.filter(
        employee=request.user,
        payment_status="credit"
    )

    my_sales_credit_original = sum(
        sale.total_sales()
        for sale in my_credit_sales
    )

    my_sales_credit_paid = sum(
        sale.total_credit_paid
        for sale in my_credit_sales
    )

    my_sales_credit_outstanding = sum(
        sale.outstanding_credit
        for sale in my_credit_sales
    )

    # =====================================================
    # MY SUPPLIER CREDIT
    # =====================================================

    my_credit_purchases = Purchase.objects.filter(
        employee=request.user,
        payment_status="credit"
    )

    my_purchase_credit_original = sum(
        purchase.total_cost
        for purchase in my_credit_purchases
    )

    my_purchase_credit_paid = sum(
        purchase.total_credit_paid
        for purchase in my_credit_purchases
    )

    my_purchase_credit_outstanding = sum(
        purchase.outstanding_credit
        for purchase in my_credit_purchases
    )

    # =====================================================
    # LAST 7 DAYS SALES
    # =====================================================

    start_date = (
        today - timezone.timedelta(days=6)
    )

    last_week_sales = Sale.objects.filter(
        employee=request.user,
        date__date__gte=start_date,
        date__date__lte=today
    )

    last_week_sales_count = (
        last_week_sales.count()
    )

    # =====================================================
    # MY TRANSACTIONS
    # =====================================================

    sales = Sale.objects.filter(
        employee=request.user
    ).select_related(
        "product"
    )

    purchases = Purchase.objects.filter(
        employee=request.user
    ).select_related(
        "product"
    )

    transactions = []

    for sale in sales:

        transactions.append({

            "date": sale.date,

            "type": "Sale",

            "product": sale.product.item_name,

            "quantity": sale.quantity,

            "amount": sale.total_sales(),

            "payment_status": (
                sale.get_payment_status_display()
            ),

        })

    for purchase in purchases:

        transactions.append({

            "date": purchase.date,

            "type": "Purchase",

            "product": purchase.product.item_name,

            "quantity": purchase.quantity,

            "amount": purchase.total_cost,

            "payment_status": (
                purchase.get_payment_status_display()
            ),

        })

    transactions.sort(
        key=lambda transaction: transaction["date"],
        reverse=True
    )

    recent_transactions = transactions[:10]

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "today_sales": sales_count,

        "today_purchases": purchases_count,

        "weekly_sales": last_week_sales_count,

        "transaction_count": len(
            transactions
        ),

        "sales_revenue": sales_revenue,

        "sales_count": sales_count,

        "sales_quantity": sales_quantity,

        "paid_sales_count": paid_sales_count,

        "paid_sales_revenue": paid_sales_revenue,

        "credit_sales_count": credit_sales_count,

        "credit_sales_amount": credit_sales_amount,

        "credit_sales_paid": credit_sales_paid,

        "credit_sales_outstanding": (
            credit_sales_outstanding
        ),

        "purchases_value": purchases_value,

        "purchases_count": purchases_count,

        "purchases_quantity": purchases_quantity,

        "paid_purchases_count": (
            paid_purchases_count
        ),

        "paid_purchases_value": (
            paid_purchases_value
        ),

        "credit_purchases_count": (
            credit_purchases_count
        ),

        "credit_purchases_amount": (
            credit_purchases_amount
        ),

        "credit_purchases_paid": (
            credit_purchases_paid
        ),

        "credit_purchases_outstanding": (
            credit_purchases_outstanding
        ),

        "my_sales_credit_original": (
            my_sales_credit_original
        ),

        "my_sales_credit_paid": (
            my_sales_credit_paid
        ),

        "my_sales_credit_outstanding": (
            my_sales_credit_outstanding
        ),

        "my_purchase_credit_original": (
            my_purchase_credit_original
        ),

        "my_purchase_credit_paid": (
            my_purchase_credit_paid
        ),

        "my_purchase_credit_outstanding": (
            my_purchase_credit_outstanding
        ),

        "transactions": transactions,

        "recent_transactions": recent_transactions,
    }

    return render(
        request,
        "users/employee_dashboard.html",
        context
    )


# =========================================================
# OWNER TRANSACTIONS
# =========================================================

@login_required
def owner_transactions(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    employee_id = request.GET.get("employee")

    transaction_type = request.GET.get(
        "type",
        "all"
    )

    period = request.GET.get(
        "period",
        "all"
    )

    payment_status = request.GET.get(
        "payment_status",
        "all"
    )

    payment_method = request.GET.get(
        "payment_method",
        "all"
    )

    today = timezone.localdate()

    sales = Sale.objects.all()

    purchases = Purchase.objects.all()

    # =====================================================
    # DATE FILTER
    # =====================================================

    if period == "today":

        sales = sales.filter(
            date__date=today
        )

        purchases = purchases.filter(
            date__date=today
        )

    elif period == "yesterday":

        yesterday = (
            today - timezone.timedelta(days=1)
        )

        sales = sales.filter(
            date__date=yesterday
        )

        purchases = purchases.filter(
            date__date=yesterday
        )

    elif period == "last_7_days":

        start_date = (
            today - timezone.timedelta(days=6)
        )

        sales = sales.filter(
            date__date__gte=start_date,
            date__date__lte=today
        )

        purchases = purchases.filter(
            date__date__gte=start_date,
            date__date__lte=today
        )

    elif period == "this_month":

        sales = sales.filter(
            date__year=today.year,
            date__month=today.month
        )

        purchases = purchases.filter(
            date__year=today.year,
            date__month=today.month
        )

    elif period == "last_month":

        first_day = today.replace(day=1)

        last_day = (
            first_day - timezone.timedelta(days=1)
        )

        sales = sales.filter(
            date__year=last_day.year,
            date__month=last_day.month
        )

        purchases = purchases.filter(
            date__year=last_day.year,
            date__month=last_day.month
        )

    elif period == "this_year":

        sales = sales.filter(
            date__year=today.year
        )

        purchases = purchases.filter(
            date__year=today.year
        )

    elif period == "last_year":

        sales = sales.filter(
            date__year=today.year - 1
        )

        purchases = purchases.filter(
            date__year=today.year - 1
        )

    # =====================================================
    # EMPLOYEE FILTER
    # =====================================================

    if employee_id:

        sales = sales.filter(
            employee_id=employee_id
        )

        purchases = purchases.filter(
            employee_id=employee_id
        )

    # =====================================================
    # PAYMENT STATUS
    # =====================================================

    if payment_status != "all":

        sales = sales.filter(
            payment_status=payment_status
        )

        purchases = purchases.filter(
            payment_status=payment_status
        )

    # =====================================================
    # PAYMENT METHOD
    # =====================================================

    if payment_method != "all":

        sales = sales.filter(
            payment_method=payment_method
        )

        purchases = purchases.filter(
            payment_method=payment_method
        )

    # =====================================================
    # TRANSACTION TYPE
    # =====================================================

    if transaction_type == "sale":

        purchases = Purchase.objects.none()

    elif transaction_type == "purchase":

        sales = Sale.objects.none()

    # =====================================================
    # COMBINE TRANSACTIONS
    # =====================================================

    transactions = []

    for sale in sales:

        transactions.append({

            "date": sale.date,

            "type": "Sale",

            "product": sale.product.item_name,

            "employee": (
                sale.employee.username
                if sale.employee
                else "Unknown"
            ),

            "quantity": sale.quantity,

            "amount": sale.total_sales(),

            "payment_status": (
                sale.get_payment_status_display()
            ),

            "payment_method": (
                sale.get_payment_method_display()
                if sale.payment_method
                else "-"
            ),

            "customer": (
                sale.customer_name
                or "-"
            ),
        })

    for purchase in purchases:

        transactions.append({

            "date": purchase.date,

            "type": "Purchase",

            "product": purchase.product.item_name,

            "employee": (
                purchase.employee.username
                if purchase.employee
                else "Unknown"
            ),

            "quantity": purchase.quantity,

            "amount": purchase.total_cost,

            "payment_status": (
                purchase.get_payment_status_display()
            ),

            "payment_method": (
                purchase.get_payment_method_display()
                if purchase.payment_method
                else "-"
            ),

            "supplier": purchase.supplier,

        })

    transactions.sort(
        key=lambda transaction: transaction["date"],
        reverse=True
    )

    # =====================================================
    # EMPLOYEES
    # =====================================================

    employees = Group.objects.get(
        name="employee"
    ).user_set.all()

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "transactions": transactions,

        "employees": employees,

        "selected_employee": employee_id,

        "selected_type": transaction_type,

        "selected_period": period,

        "selected_payment_status": (
            payment_status
        ),

        "selected_payment_method": (
            payment_method
        ),

    }

    return render(
        request,
        "owner/transaction.html",
        context
    )


# =========================================================
# EMPLOYEE TRANSACTIONS
# =========================================================

@login_required
def employee_transactions(request):

    if not request.user.groups.filter(
        name="employee"
    ).exists():

        raise PermissionDenied

    today = timezone.localdate()

    period = request.GET.get(
        "period",
        "all"
    )

    transaction_type = request.GET.get(
        "type",
        "all"
    )

    sales = Sale.objects.filter(
        employee=request.user
    )

    purchases = Purchase.objects.filter(
        employee=request.user
    )

    # =====================================================
    # DATE FILTER
    # =====================================================

    if period == "today":

        sales = sales.filter(
            date__date=today
        )

        purchases = purchases.filter(
            date__date=today
        )

    elif period == "yesterday":

        yesterday = (
            today - timezone.timedelta(days=1)
        )

        sales = sales.filter(
            date__date=yesterday
        )

        purchases = purchases.filter(
            date__date=yesterday
        )

    elif period == "last_7_days":

        start_date = (
            today - timezone.timedelta(days=6)
        )

        sales = sales.filter(
            date__date__gte=start_date,
            date__date__lte=today
        )

        purchases = purchases.filter(
            date__date__gte=start_date,
            date__date__lte=today
        )

    elif period == "this_month":

        sales = sales.filter(
            date__year=today.year,
            date__month=today.month
        )

        purchases = purchases.filter(
            date__year=today.year,
            date__month=today.month
        )

    elif period == "last_month":

        first_day = today.replace(day=1)

        last_day = (
            first_day - timezone.timedelta(days=1)
        )

        sales = sales.filter(
            date__year=last_day.year,
            date__month=last_day.month
        )

        purchases = purchases.filter(
            date__year=last_day.year,
            date__month=last_day.month
        )

    elif period == "this_year":

        sales = sales.filter(
            date__year=today.year
        )

        purchases = purchases.filter(
            date__year=today.year
        )

    elif period == "last_year":

        sales = sales.filter(
            date__year=today.year - 1
        )

        purchases = purchases.filter(
            date__year=today.year - 1
        )

    # =====================================================
    # TYPE FILTER
    # =====================================================

    if transaction_type == "sale":

        purchases = Purchase.objects.none()

    elif transaction_type == "purchase":

        sales = Sale.objects.none()

    # =====================================================
    # TRANSACTIONS
    # =====================================================

    transactions = []

    for sale in sales:

        transactions.append({

            "date": sale.date,

            "type": "Sale",

            "product": sale.product.item_name,

            "brand": sale.product.brand,

            "specification": sale.product.specification,

            "quantity": sale.quantity,

            "amount": sale.total_sales(),

            "payment_status": (
                sale.get_payment_status_display()
            ),

            "payment_method": (
                sale.get_payment_method_display()
                if sale.payment_method
                else "-"
            ),

        })

    for purchase in purchases:

        transactions.append({

            "date": purchase.date,

            "type": "Purchase",

            "product": purchase.product.item_name,

            "brand": purchase.product.brand,

            "specification": purchase.product.specification,

            "quantity": purchase.quantity,

            "amount": purchase.total_cost,

            "payment_status": (
                purchase.get_payment_status_display()
            ),

            "payment_method": (
                purchase.get_payment_method_display()
                if purchase.payment_method
                else "-"
            ),

        })

    transactions.sort(
        key=lambda transaction: transaction["date"],
        reverse=True
    )

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "transactions": transactions,

        "selected_period": period,

        "selected_type": transaction_type,

    }

    return render(
        request,
        "employee/transaction.html",
        context
    )


# =========================================================
# OWNER INVENTORY
# =========================================================

@login_required
def owner_inventory(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    products = Product.objects.all()

    return render(
        request,
        "owner/inventory.html",
        {
            "products": products
        }
    )


# =========================================================
# EMPLOYEE PROFILE
# =========================================================

@login_required
def employee_profile(request):

    if not request.user.groups.filter(
        name="employee"
    ).exists():

        raise PermissionDenied

    return render(
        request,
        "employee/profile.html"
    )


# =========================================================
# OWNER EMPLOYEES
# =========================================================

@login_required
def owner_employees(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    employees = Group.objects.get(
        name="employee"
    ).user_set.all()

    return render(
        request,
        "owner/employees.html",
        {
            "employees": employees
        }
    )


# =========================================================
# OWNER EMPLOYEE DETAIL
# =========================================================

@login_required
def owner_employee_detail(
    request,
    employee_id
):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    employee = User.objects.filter(
        id=employee_id,
        groups__name="employee"
    ).first()

    if employee is None:
        raise PermissionDenied

    today = timezone.localdate()

    # =====================================================
    # TODAY
    # =====================================================

    today_sales = Sale.objects.filter(
        employee=employee,
        date__date=today
    )

    today_purchases = Purchase.objects.filter(
        employee=employee,
        date__date=today
    )

    today_sales_count = (
        today_sales.count()
    )

    today_purchases_count = (
        today_purchases.count()
    )

    today_sales_value = sum(
        sale.total_sales()
        for sale in today_sales
    )

    today_purchases_value = sum(
        purchase.total_cost
        for purchase in today_purchases
    )

    # =====================================================
    # CREDIT SUMMARY
    # =====================================================

    employee_credit_sales = Sale.objects.filter(
        employee=employee,
        payment_status="credit"
    )

    employee_credit_purchases = Purchase.objects.filter(
        employee=employee,
        payment_status="credit"
    )

    credit_sales_outstanding = sum(
        sale.outstanding_credit
        for sale in employee_credit_sales
    )

    credit_purchases_outstanding = sum(
        purchase.outstanding_credit
        for purchase in employee_credit_purchases
    )

    # =====================================================
    # ALL TRANSACTIONS
    # =====================================================

    sales = Sale.objects.filter(
        employee=employee
    )

    purchases = Purchase.objects.filter(
        employee=employee
    )

    transactions = []

    for sale in sales:

        transactions.append({

            "date": sale.date,

            "type": "Sale",

            "product": sale.product.item_name,

            "quantity": sale.quantity,

            "amount": sale.total_sales(),

            "payment_status": (
                sale.get_payment_status_display()
            ),

        })

    for purchase in purchases:

        transactions.append({

            "date": purchase.date,

            "type": "Purchase",

            "product": purchase.product.item_name,

            "quantity": purchase.quantity,

            "amount": purchase.total_cost,

            "payment_status": (
                purchase.get_payment_status_display()
            ),

        })

    transactions.sort(
        key=lambda transaction: transaction["date"],
        reverse=True
    )

    recent_transactions = transactions[:10]

    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "employee": employee,

        "today_sales_count": (
            today_sales_count
        ),

        "today_purchases_count": (
            today_purchases_count
        ),

        "today_sales_value": (
            today_sales_value
        ),

        "today_purchases_value": (
            today_purchases_value
        ),

        "transaction_count": len(
            transactions
        ),

        "recent_transactions": (
            recent_transactions
        ),

        "credit_sales_outstanding": (
            credit_sales_outstanding
        ),

        "credit_purchases_outstanding": (
            credit_purchases_outstanding
        ),

    }

    return render(
        request,
        "owner/employee_detail.html",
        context
    )


# =========================================================
# EMPLOYEE MESSAGE TO OWNER
# =========================================================

@login_required
def message_owner(request):

    if not request.user.groups.filter(
        name="employee"
    ).exists():

        raise PermissionDenied

    if request.method == "POST":

        form = EmployeeMessageForm(
            request.POST
        )

        if form.is_valid():

            employee_message = form.save(
                commit=False
            )

            employee_message.employee = (
                request.user
            )

            employee_message.save()

            return redirect(
                "employee_dashboard"
            )

    else:

        form = EmployeeMessageForm()

    return render(
        request,
        "employee/message_owner.html",
        {
            "form": form
        }
    )


# =========================================================
# OWNER MESSAGES
# =========================================================

@login_required
def owner_messages(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    messages = EmployeeMessage.objects.select_related(
        "employee"
    ).all()

    return render(
        request,
        "owner/messages.html",
        {
            "messages": messages
        }
    )


# =========================================================
# MARK MESSAGE AS READ
# =========================================================

@login_required
def mark_message_read(
    request,
    message_id
):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    message = EmployeeMessage.objects.get(
        id=message_id
    )

    message.is_read = True

    message.save(
        update_fields=["is_read"]
    )

    return redirect(
        "owner_messages"
    )


# =========================================================
# OWNER MESSAGE COUNT
# =========================================================

@login_required
def owner_message_count(request):

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied

    unread_count = EmployeeMessage.objects.filter(
        is_read=False
    ).count()

    return render(
        request,
        "users/message_count.html",
        {
            "unread_count": unread_count
        }
    )