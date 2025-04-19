# Mubashir Bashir 19-04-2025

import frappe
from frappe.model.document import Document


class ProjectApprovalForm(Document):
	def validate(self):
		if self.is_new():
			self.posting_date = frappe.utils.nowdate()
			self.requester_id = frappe.session.user
			self.requested_by = frappe.utils.get_fullname(frappe.session.user)
		
		if not self.senior_manager_approver_id and 'Senior Manager P&D' in frappe.get_roles():
			self.senior_manager_approving_date = frappe.utils.nowdate()
			self.senior_manager_approver_id = frappe.session.user
			# self.requested_by = frappe.utils.get_fullname(frappe.session.user)
		elif not self.director_approver_id and 'Director P&D' in frappe.get_roles():
			self.director_approving_date = frappe.utils.nowdate()
			self.director_approver_id = frappe.session.user
			# self.requested_by = frappe.utils.get_fullname(frappe.session.user)
		elif not self.chairman_approver_id and 'Chairman P&D' in frappe.get_roles():
			self.chairman_approving_date = frappe.utils.nowdate()
			self.chairman_approver_id = frappe.session.user
			# self.requested_by = frappe.utils.get_fullname(frappe.session.user)



