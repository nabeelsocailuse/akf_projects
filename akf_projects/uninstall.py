import frappe

def before_uninstall():
	# delete all custom fields created by this app
	fields = frappe.get_all("Custom Field", filters={"module": "AKF Projects"})
	for f in fields:
		frappe.delete_doc("Custom Field", f.name, force=True)
