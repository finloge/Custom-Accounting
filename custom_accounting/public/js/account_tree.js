frappe.provide("frappe.treeview_settings");

frappe.treeview_settings["Account"] = {
	breadcrumb: "Accounts",
	title: __("Chart of Accounts"),
	get_tree_root: false,
	filters: [
		{
			fieldname: "company",
			fieldtype: "Select",
			options: erpnext.utils.get_tree_options("company"),
			label: __("Company"),
			default: erpnext.utils.get_tree_default("company"),
			on_change: function () {
				var me = frappe.treeview_settings["Account"].treeview;
				var company = me.page.fields_dict.company.get_value();
				if (!company) {
					frappe.throw(__("Please set a Company"));
				}
				frappe.call({
					method: "erpnext.accounts.doctype.account.account.get_root_company",
					args: {
						company: company,
					},
					callback: function (r) {
						if (r.message) {
							let root_company = r.message.length ? r.message[0] : "";
							me.page.fields_dict.root_company.set_value(root_company);

							frappe.db.get_value(
								"Company",
								{ name: company },
								"allow_account_creation_against_child_company",
								(r) => {
									frappe.flags.ignore_root_company_validation =
										r.allow_account_creation_against_child_company;
								}
							);
						}
					},
				});
			},
		},
		{
			fieldname: "root_company",
			fieldtype: "Data",
			label: __("Root Company"),
			hidden: true,
			disable_onchange: true,
		},
	],
	root_label: "Accounts",
	get_tree_nodes: "custom_accounting.custom_accounting.account.custom_account_hierarchy.get_children",
	on_get_node: function (nodes, deep = false) {
		if (frappe.boot.user.can_read.indexOf("GL Entry") == -1) return;

		const company = cur_tree.args.company;
		if (!company) return;

		frappe.db.get_value("Company", company, "abbr", (r) => {
			const company_abbr = r ? (r.abbr || "") : "";
			const company_suffix = company_abbr ? ` - ${company_abbr}` : "";

			let all_nodes = [];
			if (deep) {
				// Collect all nodes recursively if data is present
				function collect(acc, node_list) {
					for (let node of node_list) {
						acc.push(node);
						if (node.data && node.data.length) {
							collect(acc, node.data);
						}
					}
				}
				collect(all_nodes, nodes);
			} else {
				all_nodes = nodes;
			}

			// FIX: Include both base nodes (parent accounts) and real accounts for balance calculation
			const accounts_for_balance = all_nodes
				.filter((node) => node && node.value && node.is_ledger)
				.map((node) => {
					// For base nodes (without suffix), we need to find the real account name
					if (!node.value.endsWith(company_suffix)) {
						// This is a base node, construct the real account name
						return {
							value: node.value + company_suffix,
							account_currency: node.account_currency || null,
							is_base_node: true,
							original_value: node.value // Keep original for mapping back
						};
					} else {
						// This is a real account
						return {
							value: node.value,
							account_currency: node.account_currency || null,
							is_base_node: false,
							original_value: node.value
						};
					}
				});

			if (accounts_for_balance.length === 0) return;

			frappe.db.get_single_value("Accounts Settings", "show_balance_in_coa").then((value) => {
				if (value) {
					const get_balances = frappe.call({
						method: "erpnext.accounts.utils.get_account_balances",
						args: {
							accounts: accounts_for_balance.map(acc => ({
								value: acc.value,
								account_currency: acc.account_currency
							})),
							company: company,
						},
					});

					get_balances.then((r) => {
						if (!r.message || r.message.length == 0) return;

						// Create a mapping of account value to balance data
						const balance_map = {};
						r.message.forEach(account => {
							balance_map[account.value] = account;
						});

						for (let account_data of accounts_for_balance) {
							const balance_info = balance_map[account_data.value];
							if (!balance_info) continue;

							// Find the corresponding node - for base nodes use original_value, for real accounts use value
							const node_value = account_data.is_base_node ? account_data.original_value : account_data.value;
							const node = cur_tree.nodes && cur_tree.nodes[node_value];
							if (!node || node.is_root) continue;

							const balance = balance_info.balance_in_account_currency || balance_info.balance;
							const dr_or_cr = balance > 0 ? "Dr" : "Cr";
							const format = (value, currency) => format_currency(Math.abs(value), currency);

							if (balance_info.balance !== undefined) {
								node.parent && node.parent.find(".balance-area").remove();
								$(
									'<span class="balance-area pull-right">' +
										(balance_info.balance_in_account_currency
											? format(
													balance_info.balance_in_account_currency,
													balance_info.account_currency
											  ) + " / "
											: "") +
										format(balance_info.balance, balance_info.company_currency) +
										" " +
										dr_or_cr +
										"</span>"
								).insertBefore(node.$ul);
							}
						}
					});
				}
			});
		});
	},
	add_tree_node: "custom_accounting.custom_accounting.account.custom_account_hierarchy.add_custom_ac",
	menu_items: [
		{
			label: __("New Company"),
			action: function () {
				frappe.new_doc("Company", true);
			},
			condition: 'frappe.boot.user.can_create.indexOf("Company") !== -1',
		},
	],
	fields: [
		{
			fieldtype: "Data",
			fieldname: "account_name",
			label: __("New Account Name"),
			reqd: true,
			description: __(
				"Name of new Account. Note: Please don't create accounts for Customers and Suppliers"
			),
		},
		{
			fieldtype: "Data",
			fieldname: "account_number",
			label: __("Account Number"),
			description: __("Number of new Account, it will be included in the account name as a prefix"),
		},
		{
			fieldtype: "Check",
			fieldname: "is_group",
			label: __("Is Group"),
			description: __(
				"Further accounts can be made under Groups, but entries can be made against non-Groups"
			),
			onchange: function () {
				if (!this.value) {
					this.layout.set_value("root_type", "");
				}
			},
		},
		{
			fieldtype: "Select",
			fieldname: "root_type",
			label: __("Root Type"),
			options: ["Asset", "Liability", "Equity", "Income", "Expense"].join("\n"),
			depends_on: "eval:doc.is_group && !doc.parent_account",
		},
		{
			fieldtype: "Select",
			fieldname: "account_type",
			label: __("Account Type"),
			options: frappe.get_meta("Account").fields.filter((d) => d.fieldname == "account_type")[0]
				.options,
			description: __("Optional. This setting will be used to filter in various transactions."),
		},
		{
			fieldtype: "Float",
			fieldname: "tax_rate",
			label: __("Tax Rate"),
			depends_on: 'eval:doc.is_group==0&&doc.account_type=="Tax"',
		},
		{
			fieldtype: "Link",
			fieldname: "account_currency",
			label: __("Currency"),
			options: "Currency",
			description: __("Optional. Sets company's default currency, if not specified."),
		},
	],
	ignore_fields: ["parent_account"],
	onload: function (treeview) {
		frappe.treeview_settings["Account"].treeview = {};
		$.extend(frappe.treeview_settings["Account"].treeview, treeview);
		function get_company() {
			return treeview.page.fields_dict.company.get_value();
		}

		// tools
		treeview.page.add_inner_button(
			__("Chart of Cost Centers"),
			function () {
				frappe.set_route("Tree", "Cost Center", { company: get_company() });
			},
			__("View")
		);

		treeview.page.add_inner_button(
			__("Opening Invoice Creation Tool"),
			function () {
				frappe.set_route("Form", "Opening Invoice Creation Tool", { company: get_company() });
			},
			__("View")
		);

		treeview.page.add_inner_button(
			__("Period Closing Voucher"),
			function () {
				frappe.set_route("List", "Period Closing Voucher", { company: get_company() });
			},
			__("View")
		);

		treeview.page.add_inner_button(
			__("Journal Entry"),
			function () {
				frappe.new_doc("Journal Entry", { company: get_company() });
			},
			__("Create")
		);
		treeview.page.add_inner_button(
			__("Company"),
			function () {
				frappe.new_doc("Company");
			},
			__("Create")
		);

		// financial statements
		for (let report of [
			"Trial Balance",
			"General Ledger",
			"Balance Sheet",
			"Profit and Loss Statement",
			"Cash Flow",
			"Accounts Payable",
			"Accounts Receivable",
		]) {
			treeview.page.add_inner_button(
				__(report),
				function () {
					frappe.set_route("query-report", report, { company: get_company() });
				},
				__("Financial Statements")
			);
		}
	},
	post_render: function (treeview) {
		frappe.treeview_settings["Account"].treeview["tree"] = treeview.tree;
		if (treeview.can_create) {
			treeview.page.set_primary_action(
				__("New"),
				function () {
					let root_company = treeview.page.fields_dict.root_company.get_value();
					if (root_company) {
						frappe.throw(__("Please add the account to root level Company - {0}"), [
							root_company,
						]);
					} else {
						treeview.new_node();
					}
				},
				"add"
			);
		}
	},
	toolbar: [
		{
			label: __("Add Child"),
			condition: function (node) {
				return (
					frappe.boot.user.can_create.indexOf("Account") !== -1 &&
					(!frappe.treeview_settings[
						"Account"
					].treeview.page.fields_dict.root_company.get_value() ||
						frappe.flags.ignore_root_company_validation) &&
					node.expandable &&
					!node.hide_add
				);
			},
			click: function () {
				var me = frappe.views.trees["Account"];
				me.new_node();
			},
			btnClass: "hidden-xs",
		},
		{
			condition: function (node) {
				return !node.root && frappe.boot.user.can_read.indexOf("GL Entry") !== -1 && node.is_ledger;
			},
			label: __("View Ledger"),
			click: function (node, btn) {
				const company = frappe.treeview_settings["Account"].treeview.page.fields_dict.company.get_value();
				frappe.db.get_value("Company", company, "abbr", (r) => {
					const abbr = r ? r.abbr || "" : "";
					const suffix = abbr ? ` - ${abbr}` : "";
					let acc_value = node.value;
					if (!acc_value.endsWith(suffix)) {
						// Parse and get real docname
						let acc_no = null;
						let acc_name;
						if (acc_value.includes(" - ")) {
							const parts = acc_value.split(" - ");
							acc_no = parts[0];
							acc_name = parts.slice(1).join(" - ");
						} else {
							acc_name = acc_value;
						}
						const filters = {
							company: company,
							account_name: acc_name
						};
						if (acc_no) {
							filters.account_number = acc_no;
						}
						frappe.call({
							method: "frappe.client.get_list",
							args: {
								doctype: "Account",
								filters: filters,
								fields: ["name"],
								limit: 1
							},
							callback: (resp) => {
								if (resp.message && resp.message.length > 0) {
									acc_value = resp.message[0].name;
								} else {
									frappe.msgprint(__("Account not found"));
									return;
								}
								frappe.route_options = {
									from_date: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
									to_date: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
									company: company,
									account: acc_value
								};
								frappe.set_route("query-report", "General Ledger");
							}
						});
					} else {
						frappe.route_options = {
							from_date: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
							to_date: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[2],
							company: company,
							account: acc_value
						};
						frappe.set_route("query-report", "General Ledger");
					}
				});
			},
			btnClass: "hidden-xs",
		},
	],
	extend_toolbar: true,
};