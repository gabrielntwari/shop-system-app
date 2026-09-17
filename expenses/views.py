from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Expense, OwnerWithdrawal
from .forms import ExpenseForm, OwnerWithdrawalForm


# ==========================================================
# HELPERS
# ==========================================================

def is_owner(user):
    return user.groups.filter(name="owner").exists()


def is_employee(user):
    return user.groups.filter(name="employee").exists()


def is_authorized(user):
    return is_owner(user) or is_employee(user)


# ==========================================================
# ADD EXPENSE
# Owner + Employee
# ==========================================================

@login_required
def add_expense(request):

    if not is_authorized(request.user):
        raise PermissionDenied

    if request.method == "POST":

        form = ExpenseForm(request.POST)

        if form.is_valid():

            expense = form.save(commit=False)

            # Automatically record who created the expense
            expense.recorded_by = request.user

            expense.save()

            return redirect("dashboard")

    else:
        form = ExpenseForm()

    return render(
        request,
        "expenses/add_expense.html",
        {
            "form": form,
        }
    )


# ==========================================================
# EMPLOYEE EXPENSES
# Employee sees their own expenses
# ==========================================================

@login_required
def employee_expenses(request):

    if not is_employee(request.user):
        raise PermissionDenied

    expenses = Expense.objects.filter(
        recorded_by=request.user
    ).order_by("-date")

    return render(
        request,
        "expenses/employee_expenses.html",
        {
            "expenses": expenses,
        }
    )


# ==========================================================
# OWNER EXPENSES
# Owner sees ALL expenses + withdrawals
# ==========================================================

@login_required
def owner_expenses(request):

    if not is_owner(request.user):
        raise PermissionDenied

    # ALL business expenses
    expenses = Expense.objects.select_related(
        "recorded_by"
    ).order_by("-date")

    # ALL owner withdrawals
    withdrawals = OwnerWithdrawal.objects.select_related(
        "recorded_by"
    ).order_by("-date")

    # Total business expenses
    total = sum(
        expense.amount
        for expense in expenses
    )

    # Total owner withdrawals
    withdrawal_total = sum(
        withdrawal.amount
        for withdrawal in withdrawals
    )

    # Total money leaving the business
    total_outflows = total + withdrawal_total

    return render(
        request,
        "expenses/owner_expenses.html",
        {
            "expenses": expenses,
            "withdrawals": withdrawals,
            "total": total,
            "withdrawal_total": withdrawal_total,
            "total_outflows": total_outflows,
        }
    )


# ==========================================================
# ADD OWNER WITHDRAWAL
# Owner only
# ==========================================================

@login_required
def add_withdrawal(request):

    if not is_owner(request.user):
        raise PermissionDenied

    if request.method == "POST":

        form = OwnerWithdrawalForm(request.POST)

        if form.is_valid():

            withdrawal = form.save(commit=False)

            # Automatically record the owner
            withdrawal.recorded_by = request.user

            withdrawal.save()

            return redirect("dashboard")

    else:
        form = OwnerWithdrawalForm()

    return render(
        request,
        "expenses/add_withdrawal.html",
        {
            "form": form,
        }
    )