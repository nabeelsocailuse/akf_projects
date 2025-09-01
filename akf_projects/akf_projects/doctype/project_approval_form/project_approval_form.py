# Mubashir Bashir 19-04-2025

import frappe
import json
from frappe.utils import now, get_fullname
from frappe.model.document import Document

class ProjectApprovalForm(Document):
    def validate(self):
        pass

    def before_save(self):
        # Enforce Fund Class Officer must enter fund_class before proceeding
        if self.workflow_state == "Fund Class Assigned by Finance" and not self.fund_class:
            frappe.throw("Fund Class must be filled before assigning fund class.")

        # 1. Detect workflow state change
        old_state = None
        if self.name:  # existing doc
            old_state = frappe.db.get_value(self.doctype, self.name, "workflow_state")
        new_state = self.workflow_state

        if old_state != new_state:
            # ---- custom workflow tracking logic ----

            # find the active workflow for this doctype
            wf = frappe.get_doc("Workflow", {"document_type": self.doctype, "is_active": 1})
            # find matching transition (from current state + next_state)
            transition = next(
                (t for t in wf.transitions if t.state == old_state and t.next_state == new_state),
                None
            )
            if not transition:
                return

            next_state = transition.next_state

            # find allowed role for next state
            next_state_doc = next((s for s in wf.states if s.state == next_state), None)
            allowed_role = next_state_doc.allow_edit if next_state_doc else None

            next_user = None
            if allowed_role:
                # all users with this role
                users = frappe.get_all("Has Role", filters={"role": allowed_role}, fields=["parent"])
                user_ids = [u.parent for u in users]

                if user_ids:
                    # check if any of these users have a User Permission for this service_area
                    matching_users = frappe.get_all(
                        "User Permission",
                        filters={
                            "allow": "Service Area",
                            "for_value": self.service_area,
                            "user": ["in", user_ids]
                        },
                        fields=["user"]
                    )

                    if matching_users:
                        # pick first matching user
                        next_user = matching_users[0].user
                    else:
                        # fallback to first role-holder
                        next_user = user_ids[0]

            # update next_approver fields
            if next_user:
                self.next_approver_id = next_user
                self.next_approver_name = get_fullname(next_user)


            # update next_approver_id
            if next_user:
                self.next_approver_id = next_user
                self.next_approver_name = get_fullname(next_user)

            # append transition details to custom_state_data
            history = []
            if self.custom_state_data:
                try:
                    history = json.loads(self.custom_state_data)
                except Exception:
                    history = []

            history.append({
                "employee_name": get_fullname(frappe.session.user),
                "previous_state": old_state,
                "current_state": new_state,
                "datetime": now(),
                "next_user": get_fullname(next_user) if next_user else None,
                "next_role": allowed_role
            })

            self.custom_state_data = json.dumps(history, indent=2)


	# def notify_program_managers_pd(self):
	# 	users = frappe.get_all("Has Role", 
	# 		filters={"role": "Program Manager P&D"},
	# 		fields=["parent"]
	# 	)

	# 	for user in users:
	# 		user_id = user.parent

	# 		notification = frappe.new_doc("Notification Log")
	# 		notification.update({
	# 			"subject": "New Project Approval Submitted",
	# 			"email_content": f"A Project Approval Form has been submitted: {self.name}",
	# 			"for_user": user_id,
	# 			"document_type": self.doctype,
	# 			"document_name": self.name,
	# 			"type": "Alert"
	# 		})
	# 		notification.insert(ignore_permissions=True)
	# 		frappe.msgprint(f'Notification sent to {user.parent}')



