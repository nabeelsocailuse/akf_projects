# Created by Mubashir on 04-12-2024

import frappe
from erpnext.projects.doctype.task.task import Task
from frappe.utils import add_days, getdate

class XTask(Task):
    def validate(self):
        if not self.flags.in_delete:
            self.notify_donors_on_task_completion()
            calculate_dates(self)
        super(XTask, self).validate()


    def on_trash(self):      #Mubashir Bashir
        self.remove_from_all_parent_dependencies()
        if self.is_group:
            self.delete_all_child_tasks()        
        update_all_project_tasks(self.project)
        
        super(XTask, self).on_trash()

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

# Mubashir Bashir 28-4-25 Start

def calculate_next_working_day(start_date, days, holiday_list):
    """Add days to start_date skipping holidays."""
    if not start_date:
        return None
    start_date = getdate(start_date)
    added_days = 0
    while added_days < days:
        start_date = add_days(start_date, 1)
        if not is_holiday(start_date, holiday_list):
            added_days += 1
    return start_date

def is_holiday(date, holiday_list):
    if not holiday_list:
        return False
    return frappe.db.exists("Holiday", {"holiday_date": date, "parent": holiday_list})

def update_all_project_tasks(project):
    """Reschedules all tasks after a deletion or major change."""
    project_doc = frappe.get_doc("Project", project)
    holiday_list = project_doc.custom_task_holidays

    # Fetch all non-group (child) tasks ordered properly
    tasks = frappe.get_all("Task", 
        filters={"project": project, "is_group": 0},
        fields=["name", "custom_predecessor", "duration", "exp_start_date", "exp_end_date"],
        order_by="creation asc"
    )

    last_end_date = None
    for task in tasks:
        task_doc = frappe.get_doc("Task", task.name)

        if task_doc.custom_predecessor:
            predecessor = frappe.get_value("Task", task_doc.custom_predecessor, ["exp_end_date"])
            if not predecessor:
                # If predecessor is missing (maybe deleted), clear it
                task_doc.custom_predecessor = None
                last_end_date = None  # Reset flow
            else:
                last_end_date = calculate_next_working_day(predecessor, 1, holiday_list)
        if not task_doc.custom_predecessor:
            # No predecessor, continue from last task end date or project start date
            if last_end_date:
                task_doc.exp_start_date = last_end_date
            else:
                task_doc.exp_start_date = project_doc.expected_start_date

        # Calculate exp_end_date
        task_doc.exp_end_date = calculate_next_working_day(task_doc.exp_start_date, task_doc.duration - 1, holiday_list)
        last_end_date = calculate_next_working_day(task_doc.exp_start_date, task_doc.duration, holiday_list)

        task_doc.save(ignore_permissions=True)

    update_parent_tasks(project)
    update_project_expected_end_date(project)

def update_project_expected_end_date(project):
    """Updates project's expected_end_date from the latest task."""
    last_task = frappe.db.sql("""
        SELECT exp_end_date 
        FROM `tabTask` 
        WHERE project = %s 
        ORDER BY exp_end_date DESC 
        LIMIT 1
    """, (project,), as_dict=True)

    if last_task and last_task[0].exp_end_date:
        frappe.db.set_value("Project", project, "expected_end_date", last_task[0].exp_end_date)

def update_parent_tasks(project):
    """Updates parent tasks start and end dates based on their children."""
    parent_tasks = frappe.get_all("Task", 
        filters={"project": project, "is_group": 1},
        fields=["name"]
    )

    for parent in parent_tasks:
        children = frappe.get_all("Task",
            filters={"parent_task": parent.name},
            fields=["exp_start_date", "exp_end_date", "duration"]
        )
        if children:
            start_dates = [c.exp_start_date for c in children if c.exp_start_date]
            end_dates = [c.exp_end_date for c in children if c.exp_end_date]

            project_doc = frappe.get_doc("Project", project)
            holiday_list = project_doc.custom_task_holidays

            if start_dates and end_dates:
                earliest_start = min(start_dates)
                latest_end = max(end_dates)
                frappe.db.set_value("Task", parent.name, {
                    "exp_start_date": earliest_start,
                    "exp_end_date": latest_end,
                    "duration": calculate_duration(earliest_start, latest_end, holiday_list)
                })

def calculate_dates(self):
    """Handles date calculation during task creation or update."""
    if self.is_group:
        return

    if not self.duration or self.duration <= 0:
        frappe.throw("Duration must be greater than 0 for child tasks.")

    project_doc = frappe.get_doc("Project", self.project)
    holiday_list = project_doc.custom_task_holidays

    # if self.exp_start_date and self.exp_end_date:
    #     self.duration = calculate_duration(self.exp_start_date, self.exp_end_date, holiday_list)
    # else:
    if self.custom_predecessor:
        predecessor_end_date = frappe.get_value("Task", self.custom_predecessor, "exp_end_date")
        if predecessor_end_date:
            self.exp_start_date = calculate_next_working_day(predecessor_end_date, 1, holiday_list)
        else:
            self.custom_predecessor = None
            self.exp_start_date = project_doc.expected_start_date
    else:
        last_task = frappe.db.sql("""
            SELECT exp_end_date 
            FROM `tabTask`
            WHERE project = %s AND name != %s AND is_group = 0
            ORDER BY exp_end_date DESC
            LIMIT 1
        """, (self.project, self.name), as_dict=True)

        if last_task and last_task[0].exp_end_date:
            self.exp_start_date = calculate_next_working_day(last_task[0].exp_end_date, 1, holiday_list)
        else:
            self.exp_start_date = project_doc.expected_start_date

    self.exp_end_date = calculate_next_working_day(self.exp_start_date, self.duration - 1, holiday_list)
        
    update_parent_tasks(self.project)
    update_project_expected_end_date(self.project)

def calculate_duration(start_date, end_date, holiday_list):
    """Calculate number of working days between start and end dates inclusive."""
    if not start_date or not end_date:
        return 0
    start_date = getdate(start_date)
    end_date = getdate(end_date)
    days = 0
    current = start_date
    while current <= end_date:
        if not is_holiday(current, holiday_list):
            days += 1
        current = add_days(current, 1)
    return days

# Mubashir Bashir 28-4-25 End

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




# @frappe.whitelist()
# def del_tasks():
#     frappe.db.sql("""
#         DELETE FROM `tabProject` WHERE name IN (%s, %s, %s, %s)
#     """, ('P&D-2025-000084', 'P&D-2025-000080', 'P&D-2025-000079', 'Orphan-2025-000078'))


