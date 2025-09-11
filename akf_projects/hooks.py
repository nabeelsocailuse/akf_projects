app_name = "akf_projects"
app_title = "AKF Projects"
app_publisher = "Nabeel Saleem"
app_description = "Project related customizations"
app_email = "nabeel.saleem333@gmail.com"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/akf_projects/css/akf_projects.css"
# app_include_js = "/assets/akf_projects/js/akf_projects.js"

# include js, css files in header of web template
# web_include_css = "/assets/akf_projects/css/akf_projects.css"
# web_include_js = "/assets/akf_projects/js/akf_projects.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "akf_projects/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_js = {
    "Project" : "public/js/project_override.js",
    "Task" : "public/js/task_override.js",
    }


# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "akf_projects/public/icons.svg"

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
# 	"methods": "akf_projects.utils.jinja_methods",
# 	"filters": "akf_projects.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "akf_projects.install.before_install"
# after_install = "akf_projects.install.after_install"

# Uninstallation
# ------------
before_uninstall = "akf_projects.uninstall.before_uninstall"
# before_uninstall = "akf_projects.uninstall.before_uninstall"
# after_uninstall = "akf_projects.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "akf_projects.utils.before_app_install"
# after_app_install = "akf_projects.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "akf_projects.utils.before_app_uninstall"
# after_app_uninstall = "akf_projects.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "akf_projects.notifications.get_notification_config"

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

override_doctype_class = {
	# "Project": "akf_projects.customizations.extends.project.XProject"
	"Project": "akf_projects.customizations.overrides.project.project_override.XProject",
	"Task": "akf_projects.customizations.overrides.project.task_override.XTask"
}


# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	# "*": {
# 	# 	"on_update": "method",
# 	# 	"on_cancel": "method",
# 	# 	"on_trash": "method"
# 	# }
    
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"cron" :{
		"0 0 * * *": [
            "akf_projects.akf_projects.doctype.project_survey_forms.project_survey_forms.fetch_api_data",
        ],
	}
# 	"all": [
# 		"akf_projects.tasks.all"
# 	],
# 	"daily": [
# 		"akf_projects.tasks.daily"
# 	],
# 	"hourly": [
# 		"akf_projects.tasks.hourly"
# 	],
# 	"weekly": [
# 		"akf_projects.tasks.weekly"
# 	],
# 	"monthly": [
# 		"akf_projects.tasks.monthly"
# 	],
}

# Testing
# -------

# before_tests = "akf_projects.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "akf_projects.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
override_doctype_dashboards = {
	"Project": "akf_projects.customizations.overrides.project.project_dashboard.get_dashboard_data"
}

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["akf_projects.utils.before_request"]
# after_request = ["akf_projects.utils.after_request"]

# Job Events
# ----------
# before_job = ["akf_projects.utils.before_job"]
# after_job = ["akf_projects.utils.after_job"]

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
# 	"akf_projects.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

