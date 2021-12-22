from typing import overload
from . import __version__ as app_version

app_name = "tyf_app"
app_title = "TYF App"
app_publisher = "Tamdeen Youth Foundation"
app_description = "TYF App"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@tamdeen-ye.org"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tyf_app/css/tyf_app.css"
# app_include_js = "/assets/tyf_app/js/tyf_app.js"
app_include_css = "/assets/tyf_app/css/tyf_app.css"

# include js, css files in header of web template
# web_include_css = "/assets/tyf_app/css/tyf_app.css"
# web_include_js = "/assets/tyf_app/js/tyf_app.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tyf_app/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
	"Project" : "public/js/project.js",
	"Payroll Entry" : "public/js/payroll_entry.js",
	"Journal Entry" : "public/js/journal_entry.js",
	"Material Request" : "public/js/material_request.js",
	"Purchase Order" : "public/js/purchase_order.js",
	"Purchase Invoice": "public/js/purchase_invoice.js"
	}
# doctype_js = {"Payroll Entry" : "public/js/payroll_entry.js"}
# doctype_js = {"Employee" : "public/js/employee.js"}
# doctype_js = {"Employee" : "public/js/employee.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "tyf_app.install.before_install"
# after_install = "tyf_app.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tyf_app.notifications.get_notification_config"

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

override_doctype_class = {
	"Payroll Entry": "tyf_app.overrides.TYFPayrollEntry",
	# "Budget Line": "tyf_app.overrides.TYFDocument",
	# "Journal Entry": "tyf_app.overrides.TYFJournalEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
	"Journal Entry": {
		"before_save": "tyf_app.tyf_app.validations.journal_entry.validate_jv"
		# "on_cancel": "method",
		# "on_trash": "method"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tyf_app.tasks.all"
# 	],
# 	"daily": [
# 		"tyf_app.tasks.daily"
# 	],
# 	"hourly": [
# 		"tyf_app.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tyf_app.tasks.weekly"
# 	]
# 	"monthly": [
# 		"tyf_app.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "tyf_app.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tyf_app.event.get_events"
# }

# Overriding Non-Whitelisted & Non-Class Methods
# ------------------------------
# import erpnext.payroll.doctype.payroll_entry.payroll_entry #Python file pathe that contine the original method
# import tyf_app.overrides #Python file pathe that contine the custom method

# erpnext.payroll.doctype.payroll_entry.payroll_entry.get_filter_condition = tyf_app.overrides.get_filter_condition


# import erpnext.payroll.doctype.payroll_entry.payroll_entry as _erpnext_payroll_entry
# from erpnext.controllers.accounts_controller import AccountsController as _erpnext_controller
# from frappe.model.document import Document as frappe_document
# import tyf_app.overrides as _tyf_app_overrides

# _erpnext_payroll_entry.get_filter_condition = _tyf_app_overrides.get_filter_condition
# _erpnext_controller.get_gl_dict = _tyf_app_overrides.get_gl_dict
# frappe_document.set_new_name = tyf_app_overrides.set_new_name

#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "tyf_app.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"tyf_app.auth.validate"
# ]

