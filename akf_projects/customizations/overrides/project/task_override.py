# Created by Mubashir on 04-12-2024

import frappe
from erpnext.projects.doctype.task.task import Task
from frappe.utils import add_days, getdate

class XTask(Task):
    def validate(self):
        self.notify_donors_on_task_completion()
        calculate_dates(self)
        super(XTask, self).validate()

    def on_update(self):
        if self.is_template: return
        update_parent_tasks(self.project)
        # update_project_expected_end_date(self.project)


    def on_trash(self):      #Mubashir Bashir
        self.remove_from_all_parent_dependencies()
        self.remove_custom_predecessor_references()
        if self.is_group:
            self.delete_all_child_tasks()

        super(XTask, self).on_trash()
    
    def after_delete(self):
        # frappe.throw("after deleter")
        if self.is_template: return
        reset_project_schedule(self.project)        
        update_all_project_tasks(self.project, self.name)
        
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
        if self.is_template: return
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
        # frappe.throw("deleting parent dependency")
        parent_tasks = frappe.get_all("Task Depends On", filters={"task": self.name}, fields=["parent"])
        for record in parent_tasks:
            # frappe.throw(frappe.as_json(record.parent))
            parent_doc = frappe.get_doc("Task", record.parent)
            parent_doc.depends_on = [d for d in parent_doc.depends_on if d.task != self.name]
            parent_doc.save()
        self.parent_task = ""
        self.save()

    def remove_custom_predecessor_references(self):
        """Remove this task as a custom_predecessor from other tasks in the same project."""
        if not self.project:
            return

        affected_tasks = frappe.get_all(
            "Task",
            filters={
                "project": self.project,
                "custom_predecessor": self.name
            },
            pluck="name"
        )

        for task_name in affected_tasks:
            frappe.db.set_value("Task", task_name, "custom_predecessor", None)

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

def update_all_project_tasks(project, task_to_skip=None):
    """Reschedules all tasks in a project, skipping the deleted one, and updating parent and project dates."""
    if not project:
        return

    project_doc = frappe.get_doc("Project", project)
    holiday_list = project_doc.custom_task_holidays

    # Fetch all non-group tasks (excluding the deleted one), ordered by exp_start_date
    tasks = frappe.get_all("Task", 
        filters={
            "project": project,
            "is_group": 0,
            "name": ["!=", task_to_skip] if task_to_skip else ["!=", ""]
        },
        fields=["name", "custom_predecessor", "duration", "exp_start_date", "exp_end_date"],
        order_by="exp_start_date asc"
    )

    # Track completed tasks for chaining
    task_end_map = {}

    for task in tasks:
        task_doc = frappe.get_doc("Task", task.name)

        # Resolve start date based on predecessor or last known task
        if task_doc.custom_predecessor:
            predecessor_end = frappe.get_value("Task", task_doc.custom_predecessor, "exp_end_date")
            if predecessor_end:
                task_doc.exp_start_date = calculate_next_working_day(predecessor_end, 1, holiday_list)
            else:
                task_doc.custom_predecessor = None
                task_doc.exp_start_date = calculate_next_working_day(project_doc.expected_start_date, 0, holiday_list)
        else:
            # Chain from last known end date (if any)
            if task_end_map:
                last_end = max(task_end_map.values())
                task_doc.exp_start_date = calculate_next_working_day(last_end, 1, holiday_list)
            else:
                task_doc.exp_start_date = calculate_next_working_day(project_doc.expected_start_date, 0, holiday_list)

        # Calculate end date based on duration
        task_doc.exp_end_date = calculate_next_working_day(task_doc.exp_start_date, task_doc.duration - 1, holiday_list)
        
        # Save and register this task's end date
        task_doc.save(ignore_permissions=True)
        task_end_map[task_doc.name] = task_doc.exp_end_date

    update_parent_tasks(project)
    # update_project_expected_end_date(project)

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
    # frappe.throw(f"Project end date: {last_task[0].exp_end_date}")

def update_parent_tasks(project):
    """Updates parent tasks start and end dates based on their children."""
    # Get all parent (group) task names
    parent_tasks = frappe.db.sql("""
        SELECT name FROM `tabTask`
        WHERE project = %s AND is_group = 1
    """, (project,), as_dict=True)

    project_doc = frappe.get_doc("Project", project)
    holiday_list = project_doc.custom_task_holidays

    for parent in parent_tasks:
        # Fetch all child tasks for this parent
        children = frappe.db.sql("""
            SELECT exp_start_date, exp_end_date
            FROM `tabTask`
            WHERE parent_task = %s
        """, (parent.name,), as_dict=True)

        if children:
            start_dates = [c.exp_start_date for c in children if c.exp_start_date]
            end_dates = [c.exp_end_date for c in children if c.exp_end_date]

            if start_dates and end_dates:
                earliest_start = min(start_dates)
                latest_end = max(end_dates)
                duration = calculate_duration(earliest_start, latest_end, holiday_list)

                # frappe.throw(f"{earliest_start} - {latest_end}")

                frappe.db.set_value("Task", parent.name, {
                    "exp_start_date": earliest_start,
                    "exp_end_date": latest_end,
                    "duration": duration
                })

def calculate_dates(self):
    """Handles date calculation during task creation or update."""
    if self.is_group or self.is_template:
        return
    
    reset_project_schedule(self.project)

    if (self.duration is None or self.duration <= 0) and (not (self.exp_start_date and self.exp_end_date)):
        frappe.throw("Project timeline is required: provide either a duration or both expected start and end dates.")

    
    if not self.project: frappe.throw("Please select Project")
    project_doc = frappe.get_doc("Project", self.project)
    holiday_list = project_doc.custom_task_holidays

    if self.exp_start_date and self.exp_end_date:
        self.duration = calculate_duration(self.exp_start_date, self.exp_end_date, holiday_list)
    else:
        if self.custom_predecessor:
            predecessor_end_date = frappe.get_value("Task", self.custom_predecessor, "exp_end_date")
            if predecessor_end_date:
                self.exp_start_date = calculate_next_working_day(predecessor_end_date, 1, holiday_list)
            else:
                self.custom_predecessor = None
                self.exp_start_date = calculate_next_working_day(project_doc.expected_start_date, 0, holiday_list)
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
                self.exp_start_date = calculate_next_working_day(project_doc.expected_start_date, 0, holiday_list)

        self.exp_end_date = calculate_next_working_day(self.exp_start_date, self.duration - 1, holiday_list)


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

def reset_project_schedule(project):
    """Clears expected_end_date of project and date fields of all parent tasks."""
    if not project:
        return

    # Clear project expected_end_date
    frappe.db.set_value("Project", project, "expected_end_date", None)

    # Get all parent (group) tasks for this project
    parent_tasks = frappe.get_all("Task", filters={
        "project": project,
        "is_group": 1
    }, fields=["name"])

    # Clear date fields in parent tasks
    for task in parent_tasks:
        frappe.db.set_value("Task", task.name, {
            "exp_start_date": None,
            "exp_end_date": None,
            "duration": 0
        })


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
