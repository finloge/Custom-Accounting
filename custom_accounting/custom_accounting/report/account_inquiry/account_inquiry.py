# Copyright (c) 2025, example.com and contributors
# For license information, please see license.txt

# import frappe

import frappe
from frappe import _
from frappe.utils import flt, getdate, get_last_day, add_months, get_first_day
from datetime import datetime
from dateutil.relativedelta import relativedelta


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    group_by = filters.get("group_by") or "Month"

    # Build periods based on grouping
    if group_by == "Quarter":
        periods = get_quarters_between(filters.from_date, filters.to_date)
    elif group_by == "Year":
        periods = get_years_between(filters.from_date, filters.to_date)
    else:
        periods = get_months_between(filters.from_date, filters.to_date)

    data, grand_totals = get_data(filters, periods, group_by)

    # Apply scaling
    scale = get_scale_factor(filters.get("factor"))
    for row in data:
        if isinstance(row, dict):
            for field in ["debit", "credit", "balance", "variance"]:
                if field in row and isinstance(row[field], (int, float)):
                    row[field] = flt(row[field]) / scale

    columns = get_columns(filters)

    if filters.get("show_summary"):
        total_row = {
            "name": _("Grand Total"),
            "indent": 0,
            "is_group": 1,
            "debit": flt(grand_totals["debit"]) / scale,
            "credit": flt(grand_totals["credit"]) / scale,
            "balance": (flt(grand_totals["debit"]) - flt(grand_totals["credit"])) / scale,
        }
        if filters.get("show_variance"):
            total_row["variance"] = flt(grand_totals.get("variance", 0)) / scale
        data.append({})
        data.append(total_row)

    return columns, data


# -----------------------------
# Validation
# -----------------------------
def validate_filters(filters):
    if not filters.company:
        frappe.throw(_("Company is required"))
    if not filters.from_date or not filters.to_date:
        frappe.throw(_("From Date and To Date are required"))
    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be greater than To Date"))


# -----------------------------
# Period Generators
# -----------------------------
def get_months_between(from_date, to_date):
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")
    months = []
    current = start.replace(day=1)
    while current <= end:
        months.append(current.strftime("%b %Y"))
        current += relativedelta(months=1)
    return months


def get_quarters_between(from_date, to_date):
    start = datetime.strptime(from_date, "%Y-%m-%d")
    end = datetime.strptime(to_date, "%Y-%m-%d")
    quarters = []
    current = start.replace(day=1)
    while current <= end:
        q = (current.month - 1) // 3 + 1
        label = f"Q{q} {current.year}"
        if label not in quarters:
            quarters.append(label)
        current += relativedelta(months=3)
    return quarters


def get_years_between(from_date, to_date):
    start_year = datetime.strptime(from_date, "%Y-%m-%d").year
    end_year = datetime.strptime(to_date, "%Y-%m-%d").year
    return [str(y) for y in range(start_year, end_year + 1)]


# -----------------------------
# Data Builder
# -----------------------------
def get_data(filters, periods, group_by):
    data = []
    grand_totals = {"debit": 0, "credit": 0, "variance": 0}
    ytd_cache = {"debit": 0, "credit": 0}

    for period in periods:
        if group_by == "Month":
            from_date = datetime.strptime(period, "%b %Y")
            to_date = get_last_day(from_date)
        elif group_by == "Quarter":
            q, year = period.split()
            q_num = int(q[1])
            from_date = datetime(int(year), (q_num - 1) * 3 + 1, 1)
            to_date = add_months(from_date, 3) - relativedelta(days=1)
        else:
            year = int(period)
            from_date = datetime(year, 1, 1)
            to_date = datetime(year, 12, 31)

        if filters.currency_type == "YTD Converted":
            ytd_from = get_first_day(datetime(from_date.year, 1, 1))
        else:
            ytd_from = from_date

        gl_entries = frappe.db.sql(
            """
            SELECT account, cost_center, account_currency, SUM(debit) AS debit, SUM(credit) AS credit
            FROM `tabGL Entry`
            WHERE company = %(company)s
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                {account_cond}
                {cost_center_cond}
                {currency_cond}
            GROUP BY account, cost_center, account_currency
            """.format(
                account_cond="AND account = %(account)s" if filters.get("account") else "",
                cost_center_cond="AND cost_center = %(cost_center)s" if filters.get("cost_center") else "",
                currency_cond="AND account_currency = %(currency)s" if filters.get("currency") else "",
            ),
            {
                "company": filters.company,
                "from_date": ytd_from if filters.currency_type == "YTD Converted" else from_date,
                "to_date": to_date,
                "account": filters.get("account"),
                "cost_center": filters.get("cost_center"),
                "currency": filters.get("currency"),
            },
            as_dict=True,
        )

        period_debit = sum(flt(e.debit) for e in gl_entries)
        period_credit = sum(flt(e.credit) for e in gl_entries)

        if filters.currency_type == "YTD Converted":
            ytd_cache["debit"] += period_debit
            ytd_cache["credit"] += period_credit
            period_debit = ytd_cache["debit"]
            period_credit = ytd_cache["credit"]

        period_balance = period_debit - period_credit

        header = {
            "name": period,
            "indent": 0,
            "is_group": 1,
            "debit": flt(period_debit),
            "credit": flt(period_credit),
            "balance": flt(period_balance),
        }

        if filters.show_variance:
            header["variance"] = 0

        data.append(header)

        for e in gl_entries:
            balance = flt(e.debit) - flt(e.credit)
            row = {
                "name": e.account,
                "parent": period,
                "indent": 1,
                "is_group": 0,
                "account": e.account,
                "cost_center": e.cost_center,
                "debit": flt(e.debit),
                "credit": flt(e.credit),
                "balance": flt(balance),
            }
            if filters.show_variance:
                variance = compute_variance(e.account, e.cost_center, filters, balance)
                row["variance"] = variance
                header["variance"] += variance
            data.append(row)

        grand_totals["debit"] += period_debit
        grand_totals["credit"] += period_credit
        if filters.show_variance:
            grand_totals["variance"] += header["variance"]

    return data, grand_totals


# -----------------------------
# Variance Logic
# -----------------------------
def compute_variance(account, cost_center, filters, actual_balance):
    fiscal_year = get_fiscal_year(filters.from_date)
    budget = frappe.db.sql(
        """
        SELECT COALESCE(SUM(budget_amount), 0) AS total
        FROM `tabBudget Account`
        WHERE account = %s
          AND parent IN (
              SELECT name FROM `tabBudget`
              WHERE cost_center = %s AND fiscal_year = %s
          )
        """,
        (account, cost_center or None, fiscal_year),
        as_dict=True,
    )
    budget_val = budget[0].total if budget else 0.0
    return actual_balance - budget_val


def get_fiscal_year(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").year
    except Exception:
        return None


# -----------------------------
# Scaling Factor
# -----------------------------
def get_scale_factor(factor):
    mapping = {
        "Units": 1,
        "Thousands": 1000,
        "Millions": 1000000,
        "Billions": 1000000000,
    }
    return mapping.get(factor, 1)


# -----------------------------
# Columns
# -----------------------------
def get_columns(filters):
    columns = [
        {"label": _("Period / Account"), "fieldname": "name", "fieldtype": "Data", "width": 300},
        {"label": _("Cost Center"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 160},
        {"label": _("Debit"), "fieldname": "debit", "fieldtype": "Currency", "options": filters.get("currency"), "width": 130},
        {"label": _("Credit"), "fieldname": "credit", "fieldtype": "Currency", "options": filters.get("currency"), "width": 130},
        {"label": _("Balance"), "fieldname": "balance", "fieldtype": "Currency", "options": filters.get("currency"), "width": 130},
    ]
    if filters.get("show_variance"):
        columns.append({
            "label": _("Variance vs Budget"),
            "fieldname": "variance",
            "fieldtype": "Currency",
            "options": filters.get("currency"),
            "width": 150,
        })
    return columns
