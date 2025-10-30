import frappe

def set_location_name(doc, method):
    company_abbr = ""
    
    if doc.custom_company:
        company_abbr = frappe.db.get_value("Company", doc.custom_company, "abbr") or ""
    
    parts = []

    # Custom location number
    if doc.custom_location_number:
        parts.append(doc.custom_location_number)

    # Location Name (don't use doc.name!)
    if doc.location_name:
        parts.append(doc.location_name)

    # Company abbreviation
    if company_abbr:
        parts.append(company_abbr)

    # Final naming format
    new_name = " - ".join(parts)

    doc.name = new_name
