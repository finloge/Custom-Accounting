frappe.query_reports["Account Inquiry"] = {
    filters: [
        {
            fieldname: "company",
            label: __("Company"),
            fieldtype: "Link",
            options: "Company",
            default: frappe.defaults.get_user_default("Company"),
            reqd: 1
        },
        {
            fieldname: "currency",
            label: __("Currency"),
            fieldtype: "Link",
            options: "Currency",
            default: frappe.defaults.get_user_default("Currency") || "AED"
        },
        {
            fieldname: "from_date",
            label: __("From Date"),
            fieldtype: "Date",
            default: frappe.datetime.month_start(),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: __("To Date"),
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        {
            fieldname: "account",
            label: __("Account"),
            fieldtype: "Link",
            options: "Account",
            get_query: () => ({
                filters: { company: frappe.query_report.get_filter_value("company"), is_group: 0 }
            })
        },
        {
            fieldname: "cost_center",
            label: __("Cost Center / Location"),
            fieldtype: "Link",
            options: "Cost Center"
        },
        {
            fieldname: "group_by",
            label: __("Group By"),
            fieldtype: "Select",
            options: ["Month", "Quarter", "Year"],
            default: "Month"
        },
        {
            fieldname: "factor",
            label: __("Factor"),
            fieldtype: "Select",
            options: ["Units", "Thousands", "Millions", "Billions"],
            default: "Units"
        },
        {
            fieldname: "currency_type",
            label: __("Currency Type"),
            fieldtype: "Select",
            options: ["Total Entered", "PTD Converted", "YTD Converted"],
            default: "Total Entered"
        },
        {
            fieldname: "show_summary",
            label: __("Show Summary Totals"),
            fieldtype: "Check",
            default: 1
        },
        {
            fieldname: "show_variance",
            label: __("Show Variance vs Budget"),
            fieldtype: "Check",
            default: 0
        }
    ],

    tree: true,
    name_field: "name",
    parent_field: "parent",
    initial_depth: 1,

    onload: function (report) {
        // report.page.add_inner_button(__("Refresh"), () => report.refresh());
    }
};
