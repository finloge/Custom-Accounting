import frappe

@frappe.whitelist()
def get_cost_center_hierarchy(doctype, parent=None, company=None, is_root=False):
    """
    Custom cost center hierarchy:
    Company
      └── Location (custom_location)
           └── Parent → Child cost centers
    """

    # Root Level — list all unique locations
    if is_root:
        locations = frappe.db.get_all(
            "Cost Center",
            filters={"company": company},
            pluck="custom_location",
            distinct=True
        )
        locations = [loc for loc in locations if loc]
        return [{"value": loc, "expandable": 1} for loc in sorted(locations)]

    # Step 2: If parent is a location → show top-level cost centers of that location
    # Identify cost centers with that location and no parent inside that same location group
    cost_centers = frappe.get_all(
        "Cost Center",
        fields=["name", "is_group", "parent_cost_center", "custom_location"],
        filters={"company": company}
    )

    # Map each cost center by name for reference
    cc_by_name = {c.name: c for c in cost_centers}

    # Create child mapping
    child_map = {}
    for cc in cost_centers:
        parent_cc = cc.parent_cost_center
        if parent_cc:
            child_map.setdefault(parent_cc, []).append(cc)

    # If parent is a location
    locations = set(c.custom_location for c in cost_centers if c.custom_location)
    if parent in locations:
        # top-level CCs for that location = those that belong to this location but have
        # either no parent or parent with different location (so we start fresh tree)
        top_level = [
            cc for cc in cost_centers
            if cc.custom_location == parent and (
                not cc.parent_cost_center or
                cc_by_name.get(cc.parent_cost_center, {}).get("custom_location") != parent
            )
        ]
        return [{"value": cc.name, "expandable": 1 if cc.is_group else 0} for cc in top_level]

    # Step 3: If parent is a cost center → show its children
    if parent in cc_by_name:
        children = child_map.get(parent, [])
        return [{"value": c.name, "expandable": 1 if c.is_group else 0} for c in children]

    # Fallback — no children
    return []
