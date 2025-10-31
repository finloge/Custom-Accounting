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

    # Validate cost_center and location consistency
    if filters.get("cost_center") and filters.get("location"):
        loc = frappe.db.get_value("Cost Center", filters.cost_center, "custom_location")
        if loc and loc != filters.location:
            frappe.throw(_("Selected Cost Center's location does not match the selected Location"))


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
    grand_totals = {"debit": 0, "credit": 0, "variance": 0, "balance": 0}

    last_header = None
    is_ytd = filters.get("currency_type") == "YTD Converted"

    for period in periods:
        if group_by == "Month":
            period_start = datetime.strptime(period, "%b %Y")
            period_end = get_last_day(period_start)
        elif group_by == "Quarter":
            q, year = period.split()
            q_num = int(q[1])
            period_start = datetime(int(year), (q_num - 1) * 3 + 1, 1)
            period_end = add_months(period_start, 3) - relativedelta(days=1)
        else:
            year = int(period)
            period_start = datetime(year, 1, 1)
            period_end = datetime(year, 12, 31)

        # Dynamic filters
        cost_center_filter = ""
        location_filter = ""
        params_base = {
            "company": filters.company,
            "account": filters.get("account"),
            "currency": filters.get("currency"),
        }
        if filters.get("cost_center"):
            cost_center_filter = "AND cost_center = %(cost_center)s"
            params_base["cost_center"] = filters.cost_center
        elif filters.get("location"):
            cost_center_filter = """
            AND cost_center IN (
                SELECT name FROM `tabCost Center`
                WHERE company = %(company)s AND custom_location = %(location)s AND is_group = 0
            )
            """
            params_base["location"] = filters.location

        if filters.get("location"):
            location_filter = "AND location = %(location)s"
            if "location" not in params_base:
                params_base["location"] = filters.location

        account_cond = "AND account = %(account)s" if filters.get("account") else ""
        currency_cond = "AND account_currency = %(currency)s" if filters.get("currency") else ""
        
        # Optional voucher_type filter (e.g., to show only 'Sales Invoice', exclude 'Payment Entry')
        voucher_cond = ""
        if filters.get("voucher_type"):
            voucher_cond = "AND voucher_type = %(voucher_type)s"
            params_base["voucher_type"] = filters.voucher_type

        # Compute period activity for accumulation (always period-specific)
        activity_params = params_base.copy()
        activity_params["from_date"] = period_start
        activity_params["to_date"] = period_end
        activity_query = f"""
            SELECT SUM(debit) AS debit_total, SUM(credit) AS credit_total
            FROM `tabGL Entry`
            WHERE company = %(company)s
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                {account_cond}
                {cost_center_filter}
                {location_filter}
                {currency_cond}
                {voucher_cond}
        """
        activity_data = frappe.db.sql(activity_query, activity_params)
        period_activity_debit = flt(activity_data[0][0]) if activity_data else 0
        period_activity_credit = flt(activity_data[0][1]) if activity_data else 0
        grand_totals["debit"] += period_activity_debit
        grand_totals["credit"] += period_activity_credit

        # Compute display values (YTD or period)
        if is_ytd:
            report_from = get_first_day(datetime(period_start.year, 1, 1))
        else:
            report_from = period_start

        display_params = params_base.copy()
        display_params["from_date"] = report_from
        display_params["to_date"] = period_end
        gl_entries_query = f"""
            SELECT account, cost_center, location, account_currency, SUM(debit) AS debit, SUM(credit) AS credit
            FROM `tabGL Entry`
            WHERE company = %(company)s
                AND posting_date BETWEEN %(from_date)s AND %(to_date)s
                {account_cond}
                {cost_center_filter}
                {location_filter}
                {currency_cond}
                {voucher_cond}
            GROUP BY account, cost_center, location, account_currency
            """
        gl_entries = frappe.db.sql(gl_entries_query, display_params, as_dict=True)

        period_debit = sum(flt(e.debit) for e in gl_entries)
        period_credit = sum(flt(e.credit) for e in gl_entries)
        period_balance = period_debit - period_credit

        header = {
            "name": period,
            "indent": 0,
            "is_group": 1,
            "debit": flt(period_debit),
            "credit": flt(period_credit),
            "balance": flt(period_balance),
            "report_from": report_from.strftime("%Y-%m-%d"),
            "report_to": period_end.strftime("%Y-%m-%d"),
        }
        last_header = header  # Track for YTD grand fix

        if filters.get("show_variance"):
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
                "location": e.location,
                "debit": flt(e.debit),
                "credit": flt(e.credit),
                "balance": flt(balance),
                "report_from": report_from.strftime("%Y-%m-%d"),
                "report_to": period_end.strftime("%Y-%m-%d"),
            }
            if filters.get("show_variance"):
                variance = compute_variance(e.account, e.cost_center, filters, balance, report_from, period_end)
                row["variance"] = variance
                header["variance"] += variance
            data.append(row)

        if filters.get("show_variance"):
            grand_totals["variance"] += header["variance"]

    # Fix for YTD: Grand totals should match last period's YTD (not sum of periods, to avoid undercounting prior months)
    if is_ytd and last_header:
        grand_totals["debit"] = last_header["debit"]
        grand_totals["credit"] = last_header["credit"]
        grand_totals["balance"] = last_header["balance"]
        if filters.get("show_variance"):
            grand_totals["variance"] = last_header["variance"]

    return data, grand_totals


# -----------------------------
# Variance Logic
# -----------------------------
def compute_variance(account, cost_center, filters, actual_balance, period_start, period_end):
    fiscal_year = get_fiscal_year(filters.from_date)
    budget_data = frappe.db.sql(
        """
        SELECT COALESCE(SUM(budget_amount), 0) AS total_budget
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
    if not budget_data:
        return actual_balance  # No budget, variance = actual

    total_budget = flt(budget_data[0].total_budget)
    if total_budget == 0:
        return actual_balance

    # Prorate budget to period/YTD (assume even annual distribution over 12 months)
    dist = 12
    period_months = (period_end.year - period_start.year) * 12 + (period_end.month - period_start.month) + 1
    prorated_budget = total_budget * (period_months / dist)
    return actual_balance - prorated_budget


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
        {"label": _("Location"), "fieldname": "location", "fieldtype": "Link", "options": "Location", "width": 160},
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

#For Location filter
@frappe.whitelist()
def location_query(doctype, txt, searchfield, start, page_len, filters):
    cost_center = filters.get("cost_center")

    # ✅ If cost center not selected → return all locations
    if not cost_center:
        return frappe.db.sql("""
            SELECT name, location_name
            FROM `tabLocation`
            WHERE location_name LIKE %(txt)s
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        })

    # ✅ Fetch mapped location
    custom_location = frappe.db.get_value("Cost Center", cost_center, "custom_location")

    # If no mapping found → show none
    if not custom_location:
        return []

    return frappe.db.sql("""
        SELECT name, location_name
        FROM `tabLocation`
        WHERE location_name LIKE %(loc)s
        LIMIT %(start)s, %(page_len)s
    """, {
        "loc": f"%{custom_location}%",
        "start": start,
        "page_len": page_len
    })