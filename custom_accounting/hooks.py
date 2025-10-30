app_name = "custom_accounting"
app_title = "Custom Accounting"
app_publisher = "example.com"
app_description = "accounting module customization app"
app_email = "example@example.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "custom_accounting",
# 		"logo": "/assets/custom_accounting/logo.png",
# 		"title": "Custom Accounting",
# 		"route": "/custom_accounting",
# 		"has_permission": "custom_accounting.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/custom_accounting/css/custom_accounting.css"
# app_include_js = "/assets/custom_accounting/js/custom_accounting.js"

# include js, css files in header of web template
# web_include_css = "/assets/custom_accounting/css/custom_accounting.css"
# web_include_js = "/assets/custom_accounting/js/custom_accounting.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "custom_accounting/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}


# doctype_tree_js = {"Account" : "public/js/account_tree.js"}

doctype_tree_js = {"Cost Center" : "public/js/cost_center_tree.js"}

fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            ["module", "=", "Custom Accounting"]
        ]
    },
    {
        "dt": "Client Script",
        "filters": [
            ["module", "=", "Custom Accounting"]
        ]
    },
    {
        "doctype": "Report",
        "filters": [
            ["module", "=", "Custom Accounting"]
        ]
    }
]

doc_events = {
    "Location": {
        "autoname": "custom_accounting.custom_accounting.naming.naming_series.set_location_name"
    }
}


# app_include_js = [ "/assets/custom_accounting/js/report/general_ledger.js"]


# override_report_js = {
#     "General Ledger": "/assets/custom_accounting/js/report/general_ledger.js"
# }

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "custom_accounting/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "custom_accounting.utils.jinja_methods",
# 	"filters": "custom_accounting.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "custom_accounting.install.before_install"
# after_install = "custom_accounting.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "custom_accounting.uninstall.before_uninstall"
# after_uninstall = "custom_accounting.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "custom_accounting.utils.before_app_install"
# after_app_install = "custom_accounting.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "custom_accounting.utils.before_app_uninstall"
# after_app_uninstall = "custom_accounting.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "custom_accounting.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"custom_accounting.tasks.all"
# 	],
# 	"daily": [
# 		"custom_accounting.tasks.daily"
# 	],
# 	"hourly": [
# 		"custom_accounting.tasks.hourly"
# 	],
# 	"weekly": [
# 		"custom_accounting.tasks.weekly"
# 	],
# 	"monthly": [
# 		"custom_accounting.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "custom_accounting.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "custom_accounting.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "custom_accounting.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["custom_accounting.utils.before_request"]
# after_request = ["custom_accounting.utils.after_request"]

# Job Events
# ----------
# before_job = ["custom_accounting.utils.before_job"]
# after_job = ["custom_accounting.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"custom_accounting.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

