import frappe
import erpnext.accounts.utils
import json

@frappe.whitelist()
def get_children(doctype, parent=None, company=None, is_root=False):
    """
    Company → Location → Cost Center → Accounts
    """
    if not company:
        frappe.throw("Company is required")

    # Helper to build titles
    def format_main_title(acc_no, acc_name):
        if acc_no:
            return f"{acc_no} - {acc_name}"
        return acc_name or ""

    company_abbr = frappe.get_cached_value("Company", company, "abbr") or ""
    company_suffix = f" - {company_abbr}" if company_abbr else ""

    # LEVEL 1: Company root
    if not parent:
        return [{"value": company, "expandable": True, "title": company}]

    # LEVEL 2: Locations under Company
    if parent == company:
        loc_accounts = frappe.get_all(
            "Account",
            filters={"company": company},
            fields=["distinct custom_location as value"],
            order_by="custom_location"
        )
        loc_values = [la.value for la in loc_accounts if la.value]
        if loc_values:
            locs = frappe.get_all(
                "Location",
                filters={"name": ["in", loc_values]},
                fields=["name", "custom_account_number"],
                order_by="name"
            )
            loc_map = {loc.name: loc.custom_account_number for loc in locs}
            return [
                {
                    "value": f"{loc_map.get(loc.name, '')} - {loc.name}" if loc_map.get(loc.name) else loc.name,
                    "title": f"{loc_map.get(loc.name, '')} - {loc.name}" if loc_map.get(loc.name) else loc.name,
                    "expandable": True,
                    "is_ledger": False,
                    "hide_add": True
                }
                for loc in locs
            ]
        return []

    # LEVEL 3: Cost Centers under a Location (⚙ modified part)
    actual_loc = parent
    if " - " in parent:
        parts = parent.split(" - ", 1)
        first_part = parts[0].strip()
        if first_part and first_part.replace("-", "").isdigit():
            actual_loc = parts[1].strip()

    if frappe.db.exists("Location", actual_loc):
        cost_centers = frappe.get_all(
            "Account",
            filters={"company": company, "custom_location": actual_loc},
            fields=["distinct custom_cost_center as value"],
            order_by="custom_cost_center"
        )
        if cost_centers:
            cc_values = [cc.value for cc in cost_centers if cc.value]
            if cc_values:
                # Fetch only name (ignore custom_account_number for Cost Centers)
                ccs = frappe.get_all(
                    "Cost Center",
                    filters={"name": ["in", cc_values]},
                    fields=["name"],
                    order_by="name"
                )
                return [
                    {
                        "value": cc.name,
                        "title": cc.name,
                        "expandable": True,
                        "is_ledger": False
                    }
                    for cc in ccs
                ]

    # CASE A: parent is a synthetic base node (main_title)
    if company_suffix and not parent.endswith(company_suffix):
        if " - " in parent:
            parts = parent.split(" - ", 1)
            acc_no = parts[0]
            acc_name = parts[1]
        else:
            acc_no = None
            acc_name = parent

        filters = {"company": company, "account_name": acc_name}
        if acc_no:
            filters["account_number"] = acc_no

        real_accs = frappe.get_all("Account", filters=filters, fields=["name"], limit=1)
        if not real_accs:
            return []

        real_name = real_accs[0].name
        acc = frappe.get_doc("Account", real_name)
        main_title = format_main_title(acc.account_number, acc.account_name)
        real_title = f"{main_title}{company_suffix}"

        return [{
            "value": acc.name,
            "title": real_title,
            "expandable": 1 if acc.is_group else 0,
            "is_ledger": True,
            "account_currency": acc.account_currency
        }]

    # CASE B: Parent is an actual account → return child accounts
    children = frappe.get_all(
        "Account",
        filters={"company": company, "parent_account": parent},
        fields=["name", "account_name", "account_number", "is_group", "account_currency"],
        order_by="account_number asc"
    )
    if children:
        nodes = []
        for ch in children:
            main_title = format_main_title(ch.get("account_number"), ch.get("account_name"))
            node = {"title": main_title, "is_ledger": True}
            if company_suffix:
                node["value"] = main_title
                node["expandable"] = 1
            else:
                node["value"] = ch['name']
                node["expandable"] = ch.get("is_group", 0)
                node["account_currency"] = ch.get("account_currency")
            nodes.append(node)
        return nodes

    # CASE C: parent is likely a Cost Center → return top-level accounts
    actual_cc = parent
    if " - " in parent:
        parts = parent.split(" - ", 1)
        first_part = parts[0].strip()
        if first_part and first_part.replace("-", "").isdigit():
            actual_cc = parts[1].strip()

    if frappe.db.exists("Cost Center", actual_cc):
        accounts_in_cc = frappe.get_all(
            "Account",
            filters={"company": company, "custom_cost_center": actual_cc},
            fields=["name", "account_name", "account_number", "parent_account", "is_group", "account_currency"],
            order_by="account_number asc"
        )
        if not accounts_in_cc:
            return []

        names_in_cc = {a["name"] for a in accounts_in_cc}
        top_level = [a for a in accounts_in_cc if not a.get("parent_account") or a.get("parent_account") not in names_in_cc]

        result_nodes = []
        for acc in top_level:
            main_title = format_main_title(acc.get("account_number"), acc.get("account_name"))
            node = {"title": main_title, "is_ledger": True}
            if company_suffix:
                node["value"] = main_title
                node["expandable"] = 1
            else:
                full_title = f"{main_title}{company_suffix}"
                node["value"] = acc['name']
                node["title"] = full_title
                node["expandable"] = acc.get("is_group", 0)
                node["account_currency"] = acc.get("account_currency")
            result_nodes.append(node)

        return result_nodes

    return []


@frappe.whitelist()
def add_custom_ac(**args):
    parent_account = args.get('parent_account')
    company = args.get('company')

    if not company:
        frappe.throw("Company is required")

    is_cost_center_parent = False
    is_location_parent = False

    if parent_account:
        if frappe.db.exists("Account", parent_account):
            pass
        else:
            actual_parent = parent_account
            if " - " in parent_account:
                parts = parent_account.split(" - ", 1)
                first_part = parts[0].strip()
                if first_part and first_part.replace("-", "").isdigit():
                    actual_parent = parts[1].strip()

            if frappe.get_all("Account", filters={"company": company, "custom_cost_center": actual_parent}, limit=1):
                args['parent_account'] = None
                is_cost_center_parent = True
            elif frappe.get_all("Account", filters={"company": company, "custom_location": actual_parent}, limit=1):
                args['parent_account'] = None
                is_location_parent = True

            if not is_cost_center_parent and not is_location_parent:
                if frappe.get_all("Account", filters={"company": company, "custom_cost_center": parent_account}, limit=1):
                    args['parent_account'] = None
                    is_cost_center_parent = True
                elif frappe.get_all("Account", filters={"company": company, "custom_location": parent_account}, limit=1):
                    args['parent_account'] = None
                    is_location_parent = True
                else:
                    company_abbr = frappe.get_cached_value("Company", company, "abbr") or ""
                    company_suffix = f" - {company_abbr}" if company_abbr else ""

                    if " - " in parent_account:
                        parts = parent_account.split(" - ", 1)
                        acc_no = parts[0]
                        acc_name = parts[1]
                    else:
                        acc_no = None
                        acc_name = parent_account

                    filters = {"company": company, "account_name": acc_name}
                    if acc_no:
                        filters["account_number"] = acc_no

                    real_accs = frappe.get_all("Account", filters=filters, fields=["name"], limit=1)
                    if real_accs:
                        args['parent_account'] = real_accs[0].name
                    else:
                        frappe.throw(f"No account found for '{parent_account}' in company '{company}'")

    new_account = erpnext.accounts.utils.add_ac(**args)

    if is_cost_center_parent:
        frappe.db.set_value("Account", new_account, "custom_cost_center", actual_parent if 'actual_parent' in locals() else parent_account)
    if is_location_parent:
        frappe.db.set_value("Account", new_account, "custom_location", actual_parent if 'actual_parent' in locals() else parent_account)

    return new_account
