frappe.treeview_settings["Cost Center"] = {
	breadcrumb: "Accounts",
	get_tree_root: false,
	filters: [
		{
			fieldname: "company",
			fieldtype: "Select",
			options: erpnext.utils.get_tree_options("company"),
			label: __("Company"),
			default: erpnext.utils.get_tree_default("company"),
		},
	],
	root_label: "Cost Centers",
	get_tree_nodes: "custom_accounting.custom_accounting.account.cost_center_hierarchy.get_cost_center_hierarchy",
	add_tree_node: "erpnext.accounts.utils.add_cc",
	ignore_fields: ["parent_cost_center"],
	fields: [
		{ fieldtype: "Data", fieldname: "cost_center_name", label: __("New Cost Center Name"), reqd: true },
		{
			fieldtype: "Check",
			fieldname: "is_group",
			label: __("Is Group"),
		},
		{
			fieldtype: "Data",
			fieldname: "cost_center_number",
			label: __("Cost Center Number"),
		},
	],
	onload: function (treeview) {
		function get_company() {
			return treeview.page.fields_dict.company.get_value();
		}

		treeview.page.add_inner_button(__("Chart of Accounts"), function () {
			frappe.set_route("Tree", "Account", { company: get_company() });
		}, __("View"));
	},
};
