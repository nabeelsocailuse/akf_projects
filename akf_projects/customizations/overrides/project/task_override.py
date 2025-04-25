# Created by Mubashir on 04-12-2024

import frappe
from erpnext.projects.doctype.task.task import Task

class XTask(Task):
    def validate(self):
        super(XTask, self).validate()
        self.notify_donors_on_task_completion()
    
    # def after_insert(self):
    #     self.notify_donors_on_task_creation()

    def get_donors(self):   #Mubashir Bashir
        return frappe.db.sql("""
            SELECT 
                pd.donor_name, 
                pd.email
            FROM 
                `tabDonation` d 
            INNER JOIN 
                `tabPayment Detail` pd 
            ON 
                d.name = pd.parent
            WHERE 
                d.is_return = 0
                AND d.docstatus = 1
                AND pd.project_id = %s
            GROUP BY 
                pd.donor_name, pd.email
        """, (self.project,), as_dict=1)
    
    def notify_donors_on_task_creation(self):   #Mubashir Bashir
        donors = self.get_donors()
        if donors:
            for donor in donors:
                if donor.get("email"):
                    project_name = frappe.db.get_value("Project", self.project, "project_name")
                    subject = f"Task Completed: {self.name}"
                    message = f"""
                                Dear {donor.get("donor_name")}, <br><br>
                                We are pleased to inform you that the task <b>{self.subject}</b> with 
                                task id <b>{self.name}</b> in the project <b>{project_name}</b> have been 
                                successfully created. <br><br>
                                Thank you for for your continued support! <br><br>
                                Best Regards,<br>
                                {self.company}                                    
                                """
                    
                    frappe.sendmail(
                        recipients = donor.get('email'),
                        subject = subject,
                        message = message
                    )
    
    def notify_donors_on_task_completion(self):     #Mubashir Bashir
        previous_status = frappe.db.get_value('Task', {'name':self.name}, 'status')
        if self.status == 'Completed' and previous_status != 'Completed':
            donors = self.get_donors()
            if donors:
                for donor in donors:
                    if donor.get("email"):
                        project_name = frappe.db.get_value("Project", self.project, "project_name")
                        subject = f"Task Completed: {self.name}"
                        message = f"""
                                    Dear {donor.get("donor_name")}, <br><br>
                                    We are pleased to inform you that the task <b>{self.subject}</b> with 
                                    task id <b>{self.name}</b> in the project <b>{project_name}</b> have been 
                                    successfully completed. <br><br>
                                    Thank you for for your continued support! <br><br>
                                    Best Regards,<br>
                                    {self.company}                                    
                                    """
                        
                        frappe.sendmail(
                            recipients = donor.get('email'),
                            subject = subject,
                            message = message
                        )

    def on_trash(self):      #Mubashir Bashir

        self.remove_from_all_parent_dependencies()

        if self.is_group:
            self.delete_all_child_tasks()

    def remove_from_all_parent_dependencies(self):
        parent_tasks = frappe.get_all("Task Depends On", filters={"task": self.name}, fields=["parent"])
        for record in parent_tasks:
            parent_doc = frappe.get_doc("Task", record.parent)
            parent_doc.depends_on = [d for d in parent_doc.depends_on if d.task != self.name]
            parent_doc.save()

    def delete_all_child_tasks(self):
        child_tasks = frappe.get_all("Task", filters={"parent_task": self.name}, pluck="name")
        for child in child_tasks:
            frappe.delete_doc("Task", child, force=True)                     

@frappe.whitelist()                                  #Mubashir Bashir
def create_duplicate_tasks(prev_doc, subject):
	import json
	prev_doc = json.loads(prev_doc)
	parent_name = prev_doc.get("name")

	# Creating the new parent task
	new_parent = frappe.new_doc("Task")
	new_parent.subject = subject
	new_parent.project = prev_doc.get("project")
	new_parent.is_group = 1
	new_parent.status = "Open"
	new_parent.description = prev_doc.get("description")
	new_parent.exp_start_date = prev_doc.get("exp_start_date")
	new_parent.exp_end_date = prev_doc.get("exp_end_date")
	new_parent.priority = prev_doc.get("priority")
	new_parent.custom_risk_id = prev_doc.get("custom_risk_id")
	new_parent.insert()

	# Recursively copy children
	duplicate_child_tasks(parent_name, new_parent.name)

	frappe.db.commit()
	return new_parent.name


def duplicate_child_tasks(old_parent_name, new_parent_name):
	child_tasks = frappe.get_all("Task", filters={"parent_task": old_parent_name}, fields=["*"])

	for child in child_tasks:
		new_child = frappe.new_doc("Task")
		new_child.subject = child.subject
		new_child.project = child.project
		new_child.status = "Open"
		new_child.description = child.description
		new_child.exp_start_date = child.exp_start_date
		new_child.exp_end_date = child.exp_end_date
		new_child.priority = child.priority
		new_child.parent_task = new_parent_name
		new_child.custom_risk_id = child.custom_risk_id
		new_child.is_group = child.is_group
		new_child.insert()

		# Recursively duplicate this child’s children
		if child.is_group:
			duplicate_child_tasks(child.name, new_child.name)




