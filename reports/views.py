from collections import defaultdict
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from sales.models import Sale
from purchase.models import Purchase
from inventory.models import Product
from expenses.models import Expense, OwnerWithdrawal


# ==========================================================
# HELPERS
# ==========================================================

ZERO = Decimal("0")


def decimal_value(value):

    if value is None:
        return ZERO

    return Decimal(str(value))


def get_period_dates(period, today):

    if period in ["month", "this_month"]:

        return (
            today.replace(day=1),
            today,
            "This Month"
        )

    if period == "today":

        return (
            today,
            today,
            "Today"
        )

    if period == "yesterday":

        yesterday = today - timezone.timedelta(days=1)

        return (
            yesterday,
            yesterday,
            "Yesterday"
        )

    if period == "last_7_days":

        start = today - timezone.timedelta(days=6)

        return (
            start,
            today,
            "Last 7 Days"
        )

    if period == "last_month":

        first_this_month = today.replace(day=1)

        last_previous = (
            first_this_month
            - timezone.timedelta(days=1)
        )

        return (
            last_previous.replace(day=1),
            last_previous,
            "Last Month"
        )

    if period == "this_year":

        return (
            today.replace(
                month=1,
                day=1
            ),
            today,
            "This Year"
        )

    if period == "last_year":

        return (
            today.replace(
                year=today.year - 1,
                month=1,
                day=1
            ),
            today.replace(
                year=today.year - 1,
                month=12,
                day=31
            ),
            "Last Year"
        )

    return (
        None,
        None,
        "All Time"
    )


# ==========================================================
# COST OF GOODS SOLD
# ==========================================================

def get_sale_cost(sale):

    """
    Cost rule:

    For every sale, find the most recent recorded
    purchase cost for that product at or before
    the sale date.

    No FIFO.
    No LIFO.

    Each sale therefore uses the recorded cost
    applicable at that time.
    """

    purchase = (
        Purchase.objects
        .filter(
            product_id=sale.product_id,
            date__lte=sale.date
        )
        .order_by("-date", "-id")
        .first()
    )

    if not purchase:
        return ZERO

    return (
        Decimal(purchase.unit_cost)
        * Decimal(sale.quantity)
    )


# ==========================================================
# MAIN REPORT
# ==========================================================

@login_required
def owner_reports(request):

    # ------------------------------------------------------
    # OWNER ONLY
    # ------------------------------------------------------

    if not request.user.groups.filter(
        name="owner"
    ).exists():

        raise PermissionDenied


    today = timezone.localdate()


    # ------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------

    period = request.GET.get(
        "period",
        "this_month"
    )

    employee_id = request.GET.get(
        "employee",
        ""
    )

    product_id = request.GET.get(
        "product",
        ""
    )

    transaction_type = request.GET.get(
        "type",
        "all"
    )


    # ------------------------------------------------------
    # DATE RANGE
    # ------------------------------------------------------

    start_date, end_date, period_name = (
        get_period_dates(
            period,
            today
        )
    )


    # ------------------------------------------------------
    # BASE QUERYSETS
    # ------------------------------------------------------

    sales = Sale.objects.select_related(
        "product",
        "employee"
    )

    purchases = Purchase.objects.select_related(
        "product",
        "employee"
    )

    expenses = Expense.objects.select_related(
        "recorded_by"
    )

    withdrawals = OwnerWithdrawal.objects.select_related(
        "recorded_by"
    )


    # ------------------------------------------------------
    # DATE FILTER
    # ------------------------------------------------------

    if start_date and end_date:

        sales = sales.filter(
            date__date__gte=start_date,
            date__date__lte=end_date
        )

        purchases = purchases.filter(
            date__date__gte=start_date,
            date__date__lte=end_date
        )

        expenses = expenses.filter(
            date__date__gte=start_date,
            date__date__lte=end_date
        )

        withdrawals = withdrawals.filter(
            date__date__gte=start_date,
            date__date__lte=end_date
        )


    # ------------------------------------------------------
    # EMPLOYEE FILTER
    # ------------------------------------------------------

    if employee_id:

        sales = sales.filter(
            employee_id=employee_id
        )

        purchases = purchases.filter(
            employee_id=employee_id
        )

        expenses = expenses.filter(
            recorded_by_id=employee_id
        )

        withdrawals = withdrawals.filter(
            recorded_by_id=employee_id
        )


    # ------------------------------------------------------
    # PRODUCT FILTER
    # ------------------------------------------------------

    if product_id:

        sales = sales.filter(
            product_id=product_id
        )

        purchases = purchases.filter(
            product_id=product_id
        )


    # ------------------------------------------------------
    # TRANSACTION TYPE
    # ------------------------------------------------------

    if transaction_type == "sale":

        purchases = Purchase.objects.none()
        expenses = Expense.objects.none()
        withdrawals = OwnerWithdrawal.objects.none()

    elif transaction_type == "purchase":

        sales = Sale.objects.none()
        expenses = Expense.objects.none()
        withdrawals = OwnerWithdrawal.objects.none()

    elif transaction_type == "expense":

        sales = Sale.objects.none()
        purchases = Purchase.objects.none()
        withdrawals = OwnerWithdrawal.objects.none()

    elif transaction_type == "withdrawal":

        sales = Sale.objects.none()
        purchases = Purchase.objects.none()
        expenses = Expense.objects.none()


    # ------------------------------------------------------
    # LISTS
    # ------------------------------------------------------

    sales_list = list(sales)

    purchases_list = list(purchases)

    expenses_list = list(expenses)

    withdrawals_list = list(withdrawals)


    # ======================================================
    # FINANCIAL SUMMARY
    # ======================================================

    sales_count = len(sales_list)

    purchases_count = len(
        purchases_list
    )

    expense_count = len(
        expenses_list
    )

    withdrawal_count = len(
        withdrawals_list
    )


    sales_revenue = sum(
        (
            Decimal(sale.total_sales())
            for sale in sales_list
        ),
        ZERO
    )


    purchase_value = sum(
        (
            Decimal(purchase.total_cost)
            for purchase in purchases_list
        ),
        ZERO
    )


    total_expenses = sum(
        (
            Decimal(expense.amount)
            for expense in expenses_list
        ),
        ZERO
    )


    owner_withdrawals = sum(
        (
            Decimal(withdrawal.amount)
            for withdrawal in withdrawals_list
        ),
        ZERO
    )


    # ======================================================
    # COST OF GOODS SOLD
    # ======================================================

    cogs = ZERO

    for sale in sales_list:

        cogs += get_sale_cost(
            sale
        )


    # ======================================================
    # PROFITS
    # ======================================================

    gross_profit = (
        sales_revenue
        - cogs
    )


    operating_profit = (
        gross_profit
        - total_expenses
    )


    net_profit = (
        operating_profit
        - owner_withdrawals
    )


    if sales_revenue > ZERO:

        gross_margin = (
            gross_profit
            / sales_revenue
        ) * Decimal("100")

        net_margin = (
            net_profit
            / sales_revenue
        ) * Decimal("100")

    else:

        gross_margin = ZERO
        net_margin = ZERO


    # ======================================================
    # UNITS
    # ======================================================

    total_sales_units = sum(
        sale.quantity
        for sale in sales_list
    )


    total_purchase_units = sum(
        purchase.quantity
        for purchase in purchases_list
    )


    # ======================================================
    # PRODUCTS
    # ======================================================

    products = Product.objects.all().order_by(
        "item_name"
    )


    # ======================================================
    # CURRENT STOCK
    #
    # IMPORTANT:
    # Stock is calculated from ALL HISTORY,
    # NOT the selected report period.
    # ======================================================

    stock_data = []

    for product in products:

        purchased_quantity = sum(
            purchase.quantity
            for purchase in Purchase.objects.filter(
                product=product
            )
        )

        sold_quantity = sum(
            sale.quantity
            for sale in Sale.objects.filter(
                product=product
            )
        )

        current_stock = (
            purchased_quantity
            - sold_quantity
        )


        if current_stock <= 0:

            status = "Out of Stock"

        elif current_stock <= 10:

            status = "Low"

        else:

            status = "Good"


        # Most recent recorded cost

        latest_purchase = (
            Purchase.objects
            .filter(
                product=product
            )
            .order_by(
                "-date",
                "-id"
            )
            .first()
        )


        if latest_purchase:

            stock_value = (
                Decimal(current_stock)
                * Decimal(
                    latest_purchase.unit_cost
                )
            )

        else:

            stock_value = ZERO


        stock_data.append({

            "product": product,

            "purchased": purchased_quantity,

            "sold": sold_quantity,

            "stock": current_stock,

            "status": status,

            "stock_value": stock_value,

        })


    total_stock = sum(
        item["stock"]
        for item in stock_data
    )


    total_stock_value = sum(
        (
            item["stock_value"]
            for item in stock_data
        ),
        ZERO
    )


    low_stock_products = [

        item

        for item in stock_data

        if 0 < item["stock"] <= 10

    ]


    out_of_stock_products = [

        item

        for item in stock_data

        if item["stock"] <= 0

    ]


    # ======================================================
    # TOP SELLING PRODUCTS
    # ======================================================

    product_sales = defaultdict(int)

    product_revenue = defaultdict(
        lambda: ZERO
    )

    product_cogs = defaultdict(
        lambda: ZERO
    )


    for sale in sales_list:

        name = sale.product.item_name

        product_sales[name] += (
            sale.quantity
        )

        product_revenue[name] += (
            Decimal(
                sale.total_sales()
            )
        )

        product_cogs[name] += (
            get_sale_cost(sale)
        )


    top_products = []


    for name, quantity in product_sales.items():

        revenue = product_revenue[name]

        cost = product_cogs[name]

        profit = revenue - cost


        top_products.append({

            "name": name,

            "quantity": quantity,

            "revenue": revenue,

            "cogs": cost,

            "profit": profit,

        })


    top_products.sort(
        key=lambda item: item["quantity"],
        reverse=True
    )


    top_products = top_products[:10]


    max_quantity = (

        max(
            (
                item["quantity"]
                for item in top_products
            ),
            default=1
        )

    )


    for item in top_products:

        item["percentage"] = (

            item["quantity"]
            / max_quantity

        ) * 100


    # ======================================================
    # SLOW MOVING PRODUCTS
    # ======================================================

    sold_product_ids = set(
        sale.product_id
        for sale in sales_list
    )


    slow_products = [

        item

        for item in stock_data

        if (
            item["stock"] > 0
            and item["product"].id
            not in sold_product_ids
        )

    ][:10]


    # ======================================================
    # EMPLOYEES
    # ======================================================

    try:

        employee_group = Group.objects.get(
            name="employee"
        )

        employees = (
            employee_group.user_set
            .all()
            .order_by("username")
        )

    except Group.DoesNotExist:

        employees = []


    # ======================================================
    # EMPLOYEE PERFORMANCE
    # ======================================================

    employee_data = {}


    for sale in sales_list:

        if not sale.employee:
            continue


        employee = sale.employee


        if employee.id not in employee_data:

            employee_data[
                employee.id
            ] = {

                "employee": employee,

                "sales_count": 0,

                "units": 0,

                "revenue": ZERO,

                "cogs": ZERO,

                "profit": ZERO,

            }


        data = employee_data[
            employee.id
        ]


        data["sales_count"] += 1

        data["units"] += (
            sale.quantity
        )

        data["revenue"] += (
            Decimal(
                sale.total_sales()
            )
        )

        sale_cost = get_sale_cost(
            sale
        )

        data["cogs"] += sale_cost

        data["profit"] += (
            Decimal(
                sale.total_sales()
            )
            - sale_cost
        )


    employee_performance = list(
        employee_data.values()
    )


    employee_performance.sort(
        key=lambda item: item["revenue"],
        reverse=True
    )


    # ======================================================
    # DAILY PERFORMANCE CHART
    # ======================================================

    daily_data = defaultdict(
        lambda: {

            "sales": ZERO,

            "purchases": ZERO,

            "expenses": ZERO,

            "withdrawals": ZERO,

            "cogs": ZERO,

        }
    )


    for sale in sales_list:

        key = timezone.localtime(
            sale.date
        ).strftime("%d %b")

        daily_data[key]["sales"] += (
            Decimal(
                sale.total_sales()
            )
        )

        daily_data[key]["cogs"] += (
            get_sale_cost(sale)
        )


    for purchase in purchases_list:

        key = timezone.localtime(
            purchase.date
        ).strftime("%d %b")

        daily_data[key]["purchases"] += (
            Decimal(
                purchase.total_cost
            )
        )


    for expense in expenses_list:

        key = timezone.localtime(
            expense.date
        ).strftime("%d %b")

        daily_data[key]["expenses"] += (
            Decimal(
                expense.amount
            )
        )


    for withdrawal in withdrawals_list:

        key = timezone.localtime(
            withdrawal.date
        ).strftime("%d %b")

        daily_data[key]["withdrawals"] += (
            Decimal(
                withdrawal.amount
            )
        )


    daily_sales_chart = []


    for date_name, data in daily_data.items():

        daily_gross = (
            data["sales"]
            - data["cogs"]
        )

        daily_net = (
            daily_gross
            - data["expenses"]
            - data["withdrawals"]
        )


        daily_sales_chart.append({

            "date": date_name,

            "sales": float(
                data["sales"]
            ),

            "purchases": float(
                data["purchases"]
            ),

            "expenses": float(
                data["expenses"]
            ),

            "withdrawals": float(
                data["withdrawals"]
            ),

            "gross_profit": float(
                daily_gross
            ),

            "net_profit": float(
                daily_net
            ),

        })


    # Latest 30 points

    daily_sales_chart = (
        daily_sales_chart[-30:]
    )


    # ======================================================
    # CHART VALUES
    # ======================================================

    stock_chart = {

        "good": len([
            x for x in stock_data
            if x["status"] == "Good"
        ]),

        "low": len(
            low_stock_products
        ),

        "out": len(
            out_of_stock_products
        ),

    }


    # ======================================================
    # TRANSACTIONS
    # ======================================================

    transactions = []


    for sale in sales_list:

        transactions.append({

            "date": sale.date,

            "type": "Sale",

            "product":
                sale.product.item_name,

            "employee": (

                sale.employee.username

                if sale.employee

                else "Unknown"

            ),

            "quantity": sale.quantity,

            "amount":
                Decimal(
                    sale.total_sales()
                ),

        })


    for purchase in purchases_list:

        transactions.append({

            "date": purchase.date,

            "type": "Purchase",

            "product":
                purchase.product.item_name,

            "employee": (

                purchase.employee.username

                if purchase.employee

                else "Unknown"

            ),

            "quantity": purchase.quantity,

            "amount":
                Decimal(
                    purchase.total_cost
                ),

        })


    for expense in expenses_list:

        transactions.append({

            "date": expense.date,

            "type": "Expense",

            "product": "-",

            "employee": (

                expense.recorded_by.username

                if expense.recorded_by

                else "Unknown"

            ),

            "quantity": "-",

            "amount":
                Decimal(
                    expense.amount
                ),

        })


    for withdrawal in withdrawals_list:

        transactions.append({

            "date": withdrawal.date,

            "type": "Withdrawal",

            "product": "-",

            "employee": (

                withdrawal.recorded_by.username

                if withdrawal.recorded_by

                else "Owner"

            ),

            "quantity": "-",

            "amount":
                Decimal(
                    withdrawal.amount
                ),

        })


    transactions.sort(
        key=lambda item: item["date"],
        reverse=True
    )


    transactions = transactions[:50]


    # ======================================================
    # PRODUCT PERFORMANCE
    # ======================================================

    product_performance = sorted(
        top_products,
        key=lambda item: item["revenue"],
        reverse=True
    )


    # ======================================================
    # CONTEXT
    # ======================================================

    context = {

        # Filters

        "period":
            period,

        "selected_period":
            period,

        "selected_period_name":
            period_name,

        "selected_employee":
            employee_id,

        "selected_product":
            product_id,

        "selected_type":
            transaction_type,

        "employees":
            employees,

        "products":
            products,


        # Financial

        "sales_count":
            sales_count,

        "sales_revenue":
            sales_revenue,

        "purchases_count":
            purchases_count,

        "purchases_value":
            purchase_value,

        "total_expenses":
            total_expenses,

        "expense_count":
            expense_count,

        "owner_withdrawals":
            owner_withdrawals,

        "withdrawal_count":
            withdrawal_count,

        "cogs":
            cogs,

        "gross_profit":
            gross_profit,

        "gross_margin":
            gross_margin,

        "operating_profit":
            operating_profit,

        "net_profit":
            net_profit,

        "net_margin":
            net_margin,


        # Units

        "total_sales_units":
            total_sales_units,

        "total_purchase_units":
            total_purchase_units,


        # Stock

        "total_products":
            products.count(),

        "total_stock":
            total_stock,

        "total_stock_value":
            total_stock_value,

        "stock_data":
            stock_data,

        "low_stock_products":
            low_stock_products,

        "out_of_stock_products":
            out_of_stock_products,

        "low_stock_count":
            len(low_stock_products),

        "out_of_stock_count":
            len(out_of_stock_products),

        "stock_chart":
            stock_chart,


        # Products

        "top_products":
            top_products,

        "product_performance":
            product_performance,

        "slow_products":
            slow_products,


        # Employees

        "employee_performance":
            employee_performance,


        # Graphs

        "daily_sales_chart":
            daily_sales_chart,


        # Transactions

        "transactions":
            transactions,

    }


    return render(
        request,
        "reports/reports.html",
        context
    )