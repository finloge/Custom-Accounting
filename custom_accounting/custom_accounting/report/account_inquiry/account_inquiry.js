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
                filters: {
                    company: frappe.query_report.get_filter_value("company"),
                    is_group: 0
                }
            })
        },
        {
            fieldname: "cost_center",
            label: __("Cost Center"),
            fieldtype: "Link",
            options: "Cost Center",
            get_query: () => {
                const company = frappe.query_report.get_filter_value("company");
                const location = frappe.query_report.get_filter_value("location");
                
                let filters = {
                    company: company,
                    is_group: 0
                };

                // If user selected a location → limit cost centers
                if (location) {
                    filters.custom_location = location;
                }

                return { filters };
            }
        },
        {
            fieldname: "location",
            label: __("Location"),
            fieldtype: "Link",
            options: "Location",
            get_query: () => {
                const cost_center = frappe.query_report.get_filter_value("cost_center");

                return {
                    query: "custom_accounting.custom_accounting.report.account_inquiry.account_inquiry.location_query",
                    filters: {
                        cost_center: cost_center || ""
                    }
                };
            }
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

    formatter: function(value, row, column, data, default_formatter, indent) {
        if (column && column.fieldname === "balance" && data && !data.is_group && data.account) {
            const currency = frappe.query_report.get_filter_value("currency") || frappe.defaults.get_user_default("Currency") || "AED";
            const formatted_value = default_formatter(value, row, column, data, indent);

            const company = frappe.query_report.get_filter_value("company");
            const account = data.account;
            const from_date = data.report_from;
            const to_date = data.report_to;
            const cost_center = data.cost_center || "";
            const location = data.location || "";

            let filter_params = [
                `company=${encodeURIComponent(company)}`,
                `account=${encodeURIComponent(account)}`,
                `from_date=${encodeURIComponent(from_date)}`,
                `to_date=${encodeURIComponent(to_date)}`
            ];

            if (cost_center) {
                filter_params.push(`cost_center=${encodeURIComponent(cost_center)}`);
            }

            if (location) {
                filter_params.push(`location=${encodeURIComponent(location)}`);
            }

            const report_currency = frappe.query_report.get_filter_value("currency");
            if (report_currency) {
                filter_params.push(`currency=${encodeURIComponent(report_currency)}`);
            }

            const url = `/app/query-report/General Ledger?${filter_params.join("&")}`;
            return `<a href="${url}" target="_blank" class="btn-link">${formatted_value}</a>`;
        }
        return default_formatter(value, row, column, data, indent);
    },

    // onload: function (report) {
    //     // reset location when cost center changes
    //     frappe.query_report.get_filter('cost_center').on_change = () => {
    //         frappe.query_report.set_filter_value('location', '');
    //     };
    // }
};