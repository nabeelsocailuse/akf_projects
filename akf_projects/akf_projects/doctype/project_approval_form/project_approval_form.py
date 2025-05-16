# Mubashir Bashir 19-04-2025

import frappe
from frappe.utils import get_datetime, get_fullname
from frappe.model.document import Document

class ProjectApprovalForm(Document):
	def validate(self):
		# if self.is_new():
		# 	self.posting_date = frappe.utils.nowdate()		
		self.record_application_state()

	def on_submit(self):
		self.notify_program_managers_pd()
	
	def record_application_state(self):
		if(hasattr(self, 'workflow_state')):
			state_dict = eval(self.custom_state_data) if(self.custom_state_data) else {}
			# if(self.workflow_state not in state_dict):
			state_dict.update({f"{self.workflow_state}": {
				"current_state": f"<b>{self.workflow_state}</b>",
				"current_user": f"<b>{get_fullname(frappe.session.user)}</b>",
				"department": f"<b>{self.get_department() or '-'}</b>",
				"modified_on": get_datetime(),
			}})
			self.custom_state_data =  frappe.as_json(state_dict)
	
	def get_department(self):
		return frappe.get_value("Employee", {'user_id': frappe.session.user}, ['department'])

	def notify_program_managers_pd(self):
		users = frappe.get_all("Has Role", 
			filters={"role": "Program Manager P&D"},
			fields=["parent"]
		)

		for user in users:
			user_id = user.parent

			notification = frappe.new_doc("Notification Log")
			notification.update({
				"subject": "New Project Approval Submitted",
				"email_content": f"A Project Approval Form has been submitted: {self.name}",
				"for_user": user_id,
				"document_type": self.doctype,
				"document_name": self.name,
				"type": "Alert"
			})
			notification.insert(ignore_permissions=True)
			frappe.msgprint(f'Notification sent to {user.parent}')





