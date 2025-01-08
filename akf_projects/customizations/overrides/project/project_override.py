# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
import json
from email_reply_parser import EmailReplyParser
from frappe import _, qb
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Count, CurDate, Date, Sum, UnixTimestamp
from frappe.utils import add_days, flt, get_datetime, get_time, get_url, nowtime, today
from frappe.utils.user import is_website_user

from erpnext import get_default_company
from erpnext.controllers.queries import get_filters_cond
from erpnext.controllers.website_list_for_contact import get_customers_suppliers
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday

from erpnext.accounts.party import get_dashboard_info

from erpnext.projects.doctype.project.project import Project

class XProject(Project):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from akf_projects.akf_projects.doctype.donor_multiselect.donor_multiselect import DonorMultiselect
		from erpnext.projects.doctype.project_user.project_user import ProjectUser
		from frappe.types import DF

		actual_end_date: DF.Date | None
		actual_start_date: DF.Date | None
		actual_time: DF.Float
		collect_progress: DF.Check
		company: DF.Link
		copied_from: DF.Data | None
		cost_center: DF.Link | None
		customer: DF.Link | None
		daily_time_to_send: DF.Time | None
		day_to_send: DF.Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
		department: DF.Link | None
		donors: DF.TableMultiSelect[DonorMultiselect]
		estimated_costing: DF.Currency
		expected_end_date: DF.Date | None
		expected_start_date: DF.Date | None
		first_email: DF.Time | None
		frequency: DF.Literal["Hourly", "Twice Daily", "Daily", "Weekly"]
		from_time: DF.Time | None
		gross_margin: DF.Currency
		holiday_list: DF.Link | None
		is_active: DF.Literal["Yes", "No"]
		message: DF.Text | None
		naming_series: DF.Literal["PROJ-.####"]
		notes: DF.TextEditor | None
		per_gross_margin: DF.Percent
		percent_complete: DF.Percent
		percent_complete_method: DF.Literal["Manual", "Task Completion", "Task Progress", "Task Weight"]
		priority: DF.Literal["Medium", "Low", "High"]
		project_name: DF.Data
		project_template: DF.Link | None
		project_type: DF.Link | None
		sales_order: DF.Link | None
		second_email: DF.Time | None
		status: DF.Literal["Open", "Completed", "Cancelled"]
		to_time: DF.Time | None
		total_billable_amount: DF.Currency
		total_billed_amount: DF.Currency
		total_consumed_material_cost: DF.Currency
		total_costing_amount: DF.Currency
		total_purchase_cost: DF.Currency
		total_sales_amount: DF.Currency
		users: DF.Table[ProjectUser]
		weekly_time_to_send: DF.Time | None
	# end: auto-generated types

	def onload(self):
		self.set_onload(
			"activity_summary",
			frappe.db.sql(
				"""select activity_type,
			sum(hours) as total_hours
			from `tabTimesheet Detail` where project=%s and docstatus < 2 group by activity_type
			order by total_hours desc""",
				self.name,
				as_dict=True,
			),
		)
		self.update_costing()
		self.load_dashboard_info()
	
	def load_dashboard_info(self):
		# info = get_dashboard_info(self.doctype, self.name, self.loyalty_program)
		self.set_onload("dashboard_info", [ { "billing_this_year": 118036027.77, "company": "Alkhidmat Foundation Pakistan", "currency": "PKR", "total_unpaid": 1064742.57 } ])

	def before_print(self, settings=None):
		self.onload()

	def validate(self):
		super(XProject, self).validate()
		if not self.is_new():
			self.copy_from_template()
		self.send_welcome_email()
		self.update_costing()
		self.update_percent_complete()
		self.validate_from_to_dates("expected_start_date", "expected_end_date")
		self.validate_from_to_dates("actual_start_date", "actual_end_date")
		self.validate_payable() # Mubashir Bashir
		self.update_survey_allocation() # Mubashir Bashir
		self.update_project_allocation_check() # Mubarrim

	def update_project_allocation_check(self): #Mubarrim 07-01-2025
		if(self.custom_total_allocation > self.estimated_costing):
			self.custom_allocation_check = 1			
		else:
			self.custom_allocation_check = 0
						

	def update_survey_allocation(self):  # Mubashir Bashir 3-12-24
		# Fetch the previous value of custom_survey_id
		previous_survey = frappe.db.get_value("Project", {"name": self.name}, "custom_survey_id")
		
		if self.custom_survey_id:
			# If custom_survey_id is set, mark the survey as 'Allocated'
			survey_form = frappe.get_doc("Project Survey Forms", self.custom_survey_id)
			survey_form.allocation_status = "Allocated"
			survey_form.save()
		
			# If there was a previous survey, mark it as 'Unallocated' (only if it's different)
			if previous_survey and previous_survey != self.custom_survey_id:
				previous_survey_form = frappe.get_doc("Project Survey Forms", previous_survey)
				previous_survey_form.allocation_status = "Unallocated"
				previous_survey_form.save()
		else:
			# If custom_survey_id is removed, mark the previous survey as 'Unallocated'
			if previous_survey:
				survey_form = frappe.get_doc("Project Survey Forms", previous_survey)
				survey_form.allocation_status = "Unallocated"
				survey_form.save()



	def copy_from_template(self):  # Mubashir Bashir
		"""
		Copy tasks from template based on custom_task_order.
		"""
		if self.project_template and not frappe.db.get_all("Task", dict(project=self.name), limit=1):

			if not self.expected_start_date:
				self.expected_start_date = today()

			template = frappe.get_doc("Project Template", self.project_template)

			if not self.project_type:
				self.project_type = template.project_type

			# Fetch tasks from the template and sort them by custom_task_order
			template_tasks = sorted(template.tasks, key=lambda x: x.custom_task_order)

			# Create tasks from template
			project_tasks = []
			tmp_task_details = []
			previous_task_end_date = None

			for task in template_tasks:
				template_task_details = frappe.get_doc("Task", task.task)
				tmp_task_details.append(template_task_details)

				task = self.create_task_from_template(template_task_details, previous_task_end_date)
				project_tasks.append(task)

				previous_task_end_date = task.exp_end_date

			self.dependency_mapping(tmp_task_details, project_tasks)

			self.expected_end_date = previous_task_end_date


	# def create_task_from_template(self, task_details, task_order, previous_task_end_date=None):	#Mubashir Bashir
	def create_task_from_template(self, task_details, previous_task_end_date=None):	#Mubashir Bashir

		exp_start_date = self.calculate_start_date(task_details, previous_task_end_date)
		exp_end_date = self.calculate_end_date(task_details, exp_start_date)
		# frappe.msgprint(f'Start Date {exp_start_date} - End Date {exp_end_date}')

		# Initialize the task dictionary
		return frappe.get_doc(
			dict(
				doctype="Task",
				subject=task_details.subject,
				project=self.name,
				status="Open",
				exp_start_date=exp_start_date,
				exp_end_date=exp_end_date,
				description=task_details.description,
				task_weight=task_details.task_weight,
				type=task_details.type,
				issue=task_details.issue,
				is_group=task_details.is_group,
				color=task_details.color,
				template_task=task_details.name,
				priority=task_details.priority,
				# custom_task_order=task_order,
			)
		).insert()

	def calculate_start_date(self, task_details, previous_task_end_date):	#Mubashir Bashir
		"""
		Calculate the start date of the task.
		For the first task, use the project's expected start date.
		For subsequent tasks, use the next working day after the previous task's end date.
		Adjust the start date if it falls on a holiday.
		"""

		if previous_task_end_date:
			start_date = add_days(previous_task_end_date, 1)
		else:
			start_date = self.expected_start_date

		holiday_list = self.holiday_list or get_holiday_list(self.company)
		
		while is_holiday(holiday_list, start_date):
			start_date = add_days(start_date, 1)

		return start_date

	def calculate_end_date(self, task_details, start_date):	#Mubashir Bashir
		"""
		Calculate the end date based on the start date and duration of the task.
		Skips holidays in the calculation.
		"""
		end_date = start_date
		days_to_add = task_details.duration-1

		while days_to_add > 0:			
			end_date = add_days(end_date, 1)

			if not is_holiday(self.holiday_list or get_holiday_list(self.company), end_date):
				days_to_add -= 1

		return end_date




	def dependency_mapping(self, template_tasks, project_tasks):
		for project_task in project_tasks:
			template_task = frappe.get_doc("Task", project_task.template_task)

			self.check_depends_on_value(template_task, project_task, project_tasks)
			self.check_for_parent_tasks(template_task, project_task, project_tasks)

	def check_depends_on_value(self, template_task, project_task, project_tasks):
		if template_task.get("depends_on") and not project_task.get("depends_on"):
			project_template_map = {pt.template_task: pt for pt in project_tasks}

			for child_task in template_task.get("depends_on"):
				if project_template_map and project_template_map.get(child_task.task):
					project_task.reload()  # reload, as it might have been updated in the previous iteration
					project_task.append("depends_on", {"task": project_template_map.get(child_task.task).name})
					project_task.save()

	def check_for_parent_tasks(self, template_task, project_task, project_tasks):
		if template_task.get("parent_task") and not project_task.get("parent_task"):
			for pt in project_tasks:
				if pt.template_task == template_task.parent_task:
					project_task.parent_task = pt.name
					project_task.save()
					break

	def is_row_updated(self, row, existing_task_data, fields):
		if self.get("__islocal") or not existing_task_data:
			return True

		d = existing_task_data.get(row.task_id, {})

		for field in fields:
			if row.get(field) != d.get(field):
				return True

	def update_project(self):
		"""Called externally by Task"""
		self.update_percent_complete()
		self.update_costing()
		self.db_update()

	def after_insert(self):
		self.copy_from_template()
		if self.sales_order:
			frappe.db.set_value("Sales Order", self.sales_order, "project", self.name)

	def on_trash(self):
		frappe.db.set_value("Sales Order", {"project": self.name}, "project", "")

	def update_percent_complete(self):
		if self.percent_complete_method == "Manual":
			if self.status == "Completed":
				self.percent_complete = 100
			return

		total = frappe.db.count("Task", dict(project=self.name))

		if not total:
			self.percent_complete = 0
		else:
			if (self.percent_complete_method == "Task Completion" and total > 0) or (
				not self.percent_complete_method and total > 0
			):
				completed = frappe.db.sql(
					"""select count(name) from tabTask where
					project=%s and status in ('Cancelled', 'Completed')""",
					self.name,
				)[0][0]
				self.percent_complete = flt(flt(completed) / total * 100, 2)

			if self.percent_complete_method == "Task Progress" and total > 0:
				progress = frappe.db.sql(
					"""select sum(progress) from tabTask where
					project=%s""",
					self.name,
				)[0][0]
				self.percent_complete = flt(flt(progress) / total, 2)

			if self.percent_complete_method == "Task Weight" and total > 0:
				weight_sum = frappe.db.sql(
					"""select sum(task_weight) from tabTask where
					project=%s""",
					self.name,
				)[0][0]
				weighted_progress = frappe.db.sql(
					"""select progress, task_weight from tabTask where
					project=%s""",
					self.name,
					as_dict=1,
				)
				pct_complete = 0
				for row in weighted_progress:
					pct_complete += row["progress"] * frappe.utils.safe_div(row["task_weight"], weight_sum)
				self.percent_complete = flt(flt(pct_complete), 2)

		# don't update status if it is cancelled
		if self.status == "Cancelled":
			return

		if self.percent_complete == 100:
			self.status = "Completed"

	def update_costing(self):
		from frappe.query_builder.functions import Max, Min, Sum

		TimesheetDetail = frappe.qb.DocType("Timesheet Detail")
		from_time_sheet = (
			frappe.qb.from_(TimesheetDetail)
			.select(
				Sum(TimesheetDetail.costing_amount).as_("costing_amount"),
				Sum(TimesheetDetail.billing_amount).as_("billing_amount"),
				Min(TimesheetDetail.from_time).as_("start_date"),
				Max(TimesheetDetail.to_time).as_("end_date"),
				Sum(TimesheetDetail.hours).as_("time"),
			)
			.where((TimesheetDetail.project == self.name) & (TimesheetDetail.docstatus == 1))
		).run(as_dict=True)[0]

		self.actual_start_date = from_time_sheet.start_date
		self.actual_end_date = from_time_sheet.end_date

		self.total_costing_amount = from_time_sheet.costing_amount
		self.total_billable_amount = from_time_sheet.billing_amount
		self.actual_time = from_time_sheet.time

		self.update_purchase_costing()
		self.update_sales_amount()
		self.update_billed_amount()
		self.calculate_gross_margin()

	def calculate_gross_margin(self):
		expense_amount = (
			flt(self.total_costing_amount)
			+ flt(self.total_purchase_cost)
			+ flt(self.get("total_consumed_material_cost", 0))
		)

		self.gross_margin = flt(self.total_billed_amount) - expense_amount
		if self.total_billed_amount:
			self.per_gross_margin = (self.gross_margin / flt(self.total_billed_amount)) * 100

	def update_purchase_costing(self):
		total_purchase_cost = calculate_total_purchase_cost(self.name)
		self.total_purchase_cost = total_purchase_cost and total_purchase_cost[0][0] or 0

	def update_sales_amount(self):
		total_sales_amount = frappe.db.sql(
			"""select sum(base_net_total)
			from `tabSales Order` where project = %s and docstatus=1""",
			self.name,
		)

		self.total_sales_amount = total_sales_amount and total_sales_amount[0][0] or 0

	def update_billed_amount(self):
		total_billed_amount = frappe.db.sql(
			"""select sum(base_net_total)
			from `tabSales Invoice` where project = %s and docstatus=1""",
			self.name,
		)

		self.total_billed_amount = total_billed_amount and total_billed_amount[0][0] or 0

	def after_rename(self, old_name, new_name, merge=False):
		if old_name == self.copied_from:
			frappe.db.set_value("Project", new_name, "copied_from", new_name)

	def send_welcome_email(self):
		url = get_url("/project/?name={0}".format(self.name))
		messages = (
			_("You have been invited to collaborate on the project: {0}").format(self.name),
			url,
			_("Join"),
		)

		content = """
		<p>{0}.</p>
		<p><a href="{1}">{2}</a></p>
		"""

		for user in self.users:
			if user.welcome_email_sent == 0:
				frappe.sendmail(
					user.user, subject=_("Project Collaboration Invitation"), content=content.format(*messages)
				)
				user.welcome_email_sent = 1

	# Mubashir Bashir
	def validate_payable(self):
		if(self.custom_financial_close == 'Close'):
			payable_balance = self.get_project_payable_balance()['balance']
			if(payable_balance > 0):
				frappe.throw(_(f'Cannot complete the project because the payable account balance Rs {payable_balance} is pending.'))
		
	def get_project_payable_balance(self):	# Mubashir Bashir 
		payable_balance = 0
		gl_entries = frappe.get_all('GL Entry', 
					filters={'project': self.name, 'docstatus': 1}, 
					fields=['account', 'debit', 'credit'])
		for entry in gl_entries:
			account_type = frappe.db.get_value('Account', entry['account'], 'account_type')

			if(account_type == 'Payable'):
				payable_balance += entry['credit'] - entry['debit']
		return {'balance': payable_balance}
		


@frappe.whitelist()
def send_project_completion_report(doc):   #Mubashir Bashir
	doc = json.loads(doc)
	donors = frappe.db.sql("""
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
	""", (doc.get('name'),), as_dict=1)
	if donors:
		for donor in donors:
			if donor.get("email"):
				subject = "Project Completion Report"
				message = f"""
							Dear {donor.get("donor_name")}, <br><br>
							<p>We are delighted to inform you that the {doc.get("project_name")} has been successfully completed, thanks to your invaluable support and generosity.</p>
							
							<p>Please find attached the Project Completion Report, which provides a comprehensive overview of the project's objectives, activities, outcomes, 
							and overall impact. The report highlights key achievements, lessons learned, and how the project has contributed to the intended goals. We have also 
							included financial details to ensure full transparency regarding resource utilization.</p>

							<p>Your contribution has made a significant difference, and the success of this project would not have been possible without your trust and encouragement. 
							If you have any feedback or need further clarification, we would be happy to address it.</p>

							<p>Thank you once again for being an integral part of this journey. We look forward to your continued partnership in future endeavors.</p><br>
							Best Regards,<br>
							{doc.get('company')}
							"""
				# pdf = frappe.get_print(doc.get("doctype"), doc.get("name"), print_format="Project Completion Report")

                # # Prepare the attachment
				# attachments = [
				# 	{
				# 		"fname": f"Project_Completion_Report_{doc.get('name')}.pdf",
				# 		"fcontent": pdf,
				# 		# "is_private": 1 
				# 	}
				# ]
				attachments = [            
					{
						"print_format": "Project Completion Report",
						"html": "",
						"print_format_attachment": 1,
						"doctype": doc.get("doctype"),
						"name": doc.get("name"),
						"lang": "en",
						"print_letterhead": "1"
					}
				]
				
				frappe.sendmail(
					recipients = donor.get('email'),
					subject = subject,
					message = message,
					attachments=attachments
				)

@frappe.whitelist()
def send_project_progress_report(doc):   #Mubashir Bashir
	doc = json.loads(doc)
	donors = frappe.db.sql("""
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
	""", (doc.get('name'),), as_dict=1)
	if donors:
		for donor in donors:
			if donor.get("email"):
				subject = "Project Progress Report"
				message = f"""
							Dear {donor.get("donor_name")}, <br><br>
							<p>I hope this email finds you in good health and high spirits.</p>
							
							<p>We are pleased to share the latest progress report for the {doc.get("project_name")}, 
							attached for your review. The report provides detailed insights into the milestones achieved, 
							activities completed, and upcoming plans.</p>

							<p>We remain deeply grateful for your generous support and commitment, which makes this progress possible. 
							Should you have any questions or require additional details, please do not hesitate to reach out.</p>

							<p>Thank you once again for your trust in our work.</p><br>
							Best Regards,<br>
							{doc.get('company')}
							"""
				# pdf = frappe.get_print(doc.get("doctype"), doc.get("name"), print_format="Project Completion Report")

                # # Prepare the attachment
				# attachments = [
				# 	{
				# 		"fname": f"Project_Completion_Report_{doc.get('name')}.pdf",
				# 		"fcontent": pdf,
				# 		# "is_private": 1 
				# 	}
				# ]
				attachments = [            
					{
						"print_format": "Project Progress Report",
						"html": "",
						"print_format_attachment": 1,
						"doctype": doc.get("doctype"),
						"name": doc.get("name"),
						"lang": "en",
						"print_letterhead": "1"
					}
				]
				
				frappe.sendmail(
					recipients = donor.get('email'),
					subject = subject,
					message = message,
					attachments=attachments
				)



# @frappe.whitelist()
# def send_email_attachments(doc):
#     # Convert string to dictionary
#     doc = json.loads(doc)

#     project_users = frappe.get_all(
#         "Project User",
#         filters={"parent": doc.get("name"), "parenttype": "Project"},
#         fields=["email", "full_name"]
#     )

#     recipients = [{'email': user.email, 'full_name': user.full_name} for user in project_users if frappe.utils.validate_email_address(user.email)]
#     if not recipients:
#         frappe.throw(_("No valid email addresses found in the project's user list."))

#     subject = "Attachments"

#     # Iterate over recipients and send personalized emails
#     for recipient in recipients:
#         full_name = recipient['full_name'] or "Team"
#         message = f""" 
#             <p>Dear {full_name},</p>
#             <p>Please review the attached documents for more details.</p>
#             <p>Best Regards,</p>
#             <p><b>{doc.get('company')}</b></p>.
#         """

#         # Attachments for email
#         attachments = [
#             {
#                 "print_format": "Project Progress Report",
#                 "html": "",
#                 "print_format_attachment": 1,
#                 "doctype": doc.get("doctype"),
#                 "name": doc.get("name"),
#                 "lang": "en",
#                 "print_letterhead": "1"
#             },
#             {
#                 "print_format": "Project Completion Report",
#                 "html": "",
#                 "print_format_attachment": 1,
#                 "doctype": doc.get("doctype"),
#                 "name": doc.get("name"),
#                 "lang": "en",
#                 "print_letterhead": "1"
#             }
#         ]

#         # Sending email
#         try:
#             frappe.sendmail(
#                 recipients=[recipient['email']],
#                 subject=subject,
#                 message=message,
#                 attachments=attachments
#             )
#         except Exception as e:
#             frappe.log_error(message=str(e), title="Send Email to Project User Failed")
#             frappe.throw(_("An error occurred while sending the email to {0}. Please check the error log for details.").format(full_name))
    
#     frappe.msgprint(_("Emails sent successfully to project users."))

		

def get_timeline_data(doctype: str, name: str) -> dict[int, int]:
	"""Return timeline for attendance"""

	timesheet_detail = frappe.qb.DocType("Timesheet Detail")

	return dict(
		frappe.qb.from_(timesheet_detail)
		.select(UnixTimestamp(timesheet_detail.from_time), Count("*"))
		.where(timesheet_detail.project == name)
		.where(timesheet_detail.from_time > CurDate() - Interval(years=1))
		.where(timesheet_detail.docstatus < 2)
		.groupby(Date(timesheet_detail.from_time))
		.run()
	)


def get_project_list(
	doctype, txt, filters, limit_start, limit_page_length=20, order_by="modified"
):
	customers, suppliers = get_customers_suppliers("Project", frappe.session.user)

	ignore_permissions = False
	if is_website_user() and frappe.session.user != "Guest":
		if not filters:
			filters = []

		if customers:
			filters.append([doctype, "customer", "in", customers])
			ignore_permissions = True

	meta = frappe.get_meta(doctype)

	fields = "distinct *"

	or_filters = []

	if txt:
		if meta.search_fields:
			for f in meta.get_search_fields():
				if f == "name" or meta.get_field(f).fieldtype in (
					"Data",
					"Text",
					"Small Text",
					"Text Editor",
					"select",
				):
					or_filters.append([doctype, f, "like", "%" + txt + "%"])
		else:
			if isinstance(filters, dict):
				filters["name"] = ("like", "%" + txt + "%")
			else:
				filters.append([doctype, "name", "like", "%" + txt + "%"])

	return frappe.get_list(
		doctype,
		fields=fields,
		filters=filters,
		or_filters=or_filters,
		limit_start=limit_start,
		limit_page_length=limit_page_length,
		order_by=order_by,
		ignore_permissions=ignore_permissions,
	)


def get_list_context(context=None):
	from erpnext.controllers.website_list_for_contact import get_list_context

	list_context = get_list_context(context)
	list_context.update(
		{
			"show_sidebar": True,
			"show_search": True,
			"no_breadcrumbs": True,
			"title": _("Projects"),
			"get_list": get_project_list,
			"row_template": "templates/includes/projects/project_row.html",
		}
	)

	return list_context


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_users_for_project(doctype, txt, searchfield, start, page_len, filters):
	conditions = []
	return frappe.db.sql(
		"""select name, concat_ws(' ', first_name, middle_name, last_name)
		from `tabUser`
		where enabled=1
			and name not in ("Guest", "Administrator")
			and ({key} like %(txt)s
				or full_name like %(txt)s)
			{fcond} {mcond}
		order by
			(case when locate(%(_txt)s, name) > 0 then locate(%(_txt)s, name) else 99999 end),
			(case when locate(%(_txt)s, full_name) > 0 then locate(%(_txt)s, full_name) else 99999 end),
			idx desc,
			name, full_name
		limit %(page_len)s offset %(start)s""".format(
			**{
				"key": searchfield,
				"fcond": get_filters_cond(doctype, filters, conditions),
				"mcond": get_match_cond(doctype),
			}
		),
		{"txt": "%%%s%%" % txt, "_txt": txt.replace("%", ""), "start": start, "page_len": page_len},
	)


@frappe.whitelist()
def get_cost_center_name(project):
	return frappe.db.get_value("Project", project, "cost_center")


def hourly_reminder():
	fields = ["from_time", "to_time"]
	projects = get_projects_for_collect_progress("Hourly", fields)

	for project in projects:
		if get_time(nowtime()) >= get_time(project.from_time) or get_time(nowtime()) <= get_time(
			project.to_time
		):
			send_project_update_email_to_users(project.name)


def project_status_update_reminder():
	daily_reminder()
	twice_daily_reminder()
	weekly_reminder()


def daily_reminder():
	fields = ["daily_time_to_send"]
	projects = get_projects_for_collect_progress("Daily", fields)

	for project in projects:
		if allow_to_make_project_update(project.name, project.get("daily_time_to_send"), "Daily"):
			send_project_update_email_to_users(project.name)


def twice_daily_reminder():
	fields = ["first_email", "second_email"]
	projects = get_projects_for_collect_progress("Twice Daily", fields)
	fields.remove("name")

	for project in projects:
		for d in fields:
			if allow_to_make_project_update(project.name, project.get(d), "Twicely"):
				send_project_update_email_to_users(project.name)


def weekly_reminder():
	fields = ["day_to_send", "weekly_time_to_send"]
	projects = get_projects_for_collect_progress("Weekly", fields)

	current_day = get_datetime().strftime("%A")
	for project in projects:
		if current_day != project.day_to_send:
			continue

		if allow_to_make_project_update(project.name, project.get("weekly_time_to_send"), "Weekly"):
			send_project_update_email_to_users(project.name)


def allow_to_make_project_update(project, time, frequency):
	data = frappe.db.sql(
		""" SELECT name from `tabProject Update`
		WHERE project = %s and date = %s """,
		(project, today()),
	)

	# len(data) > 1 condition is checked for twicely frequency
	if data and (frequency in ["Daily", "Weekly"] or len(data) > 1):
		return False

	if get_time(nowtime()) >= get_time(time):
		return True


@frappe.whitelist()
def create_duplicate_project(prev_doc, project_name):
	"""Create duplicate project based on the old project"""
	import json

	prev_doc = json.loads(prev_doc)

	if project_name == prev_doc.get("name"):
		frappe.throw(_("Use a name that is different from previous project name"))

	# change the copied doc name to new project name
	project = frappe.copy_doc(prev_doc)
	project.name = project_name
	project.project_template = ""
	project.project_name = project_name
	project.insert()

	# fetch all the task linked with the old project
	task_list = frappe.get_all("Task", filters={"project": prev_doc.get("name")}, fields=["name"])

	# Create duplicate task for all the task
	for task in task_list:
		task = frappe.get_doc("Task", task)
		new_task = frappe.copy_doc(task)
		new_task.project = project.name
		new_task.insert()

	project.db_set("project_template", prev_doc.get("project_template"))


def get_projects_for_collect_progress(frequency, fields):
	fields.extend(["name"])

	return frappe.get_all(
		"Project",
		fields=fields,
		filters={"collect_progress": 1, "frequency": frequency, "status": "Open"},
	)


def send_project_update_email_to_users(project):
	doc = frappe.get_doc("Project", project)

	if is_holiday(doc.holiday_list) or not doc.users:
		return

	project_update = frappe.get_doc(
		{
			"doctype": "Project Update",
			"project": project,
			"sent": 0,
			"date": today(),
			"time": nowtime(),
			"naming_series": "UPDATE-.project.-.YY.MM.DD.-",
		}
	).insert()

	subject = "For project %s, update your status" % (project)

	incoming_email_account = frappe.db.get_value(
		"Email Account", dict(enable_incoming=1, default_incoming=1), "email_id"
	)

	frappe.sendmail(
		recipients=get_users_email(doc),
		message=doc.message,
		subject=_(subject),
		reference_doctype=project_update.doctype,
		reference_name=project_update.name,
		reply_to=incoming_email_account,
	)


def collect_project_status():
	for data in frappe.get_all("Project Update", {"date": today(), "sent": 0}):
		replies = frappe.get_all(
			"Communication",
			fields=["content", "text_content", "sender"],
			filters=dict(
				reference_doctype="Project Update",
				reference_name=data.name,
				communication_type="Communication",
				sent_or_received="Received",
			),
			order_by="creation asc",
		)

		for d in replies:
			doc = frappe.get_doc("Project Update", data.name)
			user_data = frappe.db.get_values(
				"User", {"email": d.sender}, ["full_name", "user_image", "name"], as_dict=True
			)[0]

			doc.append(
				"users",
				{
					"user": user_data.name,
					"full_name": user_data.full_name,
					"image": user_data.user_image,
					"project_status": frappe.utils.md_to_html(
						EmailReplyParser.parse_reply(d.text_content) or d.content
					),
				},
			)

			doc.save(ignore_permissions=True)


def send_project_status_email_to_users():
	yesterday = add_days(today(), -1)

	for d in frappe.get_all("Project Update", {"date": yesterday, "sent": 0}):
		doc = frappe.get_doc("Project Update", d.name)

		project_doc = frappe.get_doc("Project", doc.project)

		args = {"users": doc.users, "title": _("Project Summary for {0}").format(yesterday)}

		frappe.sendmail(
			recipients=get_users_email(project_doc),
			template="daily_project_summary",
			args=args,
			subject=_("Daily Project Summary for {0}").format(d.name),
			reference_doctype="Project Update",
			reference_name=d.name,
		)

		doc.db_set("sent", 1)


def update_project_sales_billing():
	sales_update_frequency = frappe.db.get_single_value("Selling Settings", "sales_update_frequency")
	if sales_update_frequency == "Each Transaction":
		return
	elif sales_update_frequency == "Monthly" and frappe.utils.now_datetime().day != 1:
		return

	# Else simply fallback to Daily
	exists_query = (
		"(SELECT 1 from `tab{doctype}` where docstatus = 1 and project = `tabProject`.name)"
	)
	project_map = {}
	for project_details in frappe.db.sql(
		"""
			SELECT name, 1 as order_exists, null as invoice_exists from `tabProject` where
			exists {order_exists}
			union
			SELECT name, null as order_exists, 1 as invoice_exists from `tabProject` where
			exists {invoice_exists}
		""".format(
			order_exists=exists_query.format(doctype="Sales Order"),
			invoice_exists=exists_query.format(doctype="Sales Invoice"),
		),
		as_dict=True,
	):
		project = project_map.setdefault(
			project_details.name, frappe.get_doc("Project", project_details.name)
		)
		if project_details.order_exists:
			project.update_sales_amount()
		if project_details.invoice_exists:
			project.update_billed_amount()

	for project in project_map.values():
		project.save()


@frappe.whitelist()
def create_kanban_board_if_not_exists(project):
	from frappe.desk.doctype.kanban_board.kanban_board import quick_kanban_board

	project = frappe.get_doc("Project", project)
	if not frappe.db.exists("Kanban Board", project.project_name):
		quick_kanban_board("Task", project.project_name, "status", project.name)

	return True


@frappe.whitelist()
def set_project_status(project, status):
	"""
	set status for project and all related tasks
	"""
	if not status in ("Completed", "Cancelled"):
		frappe.throw(_("Status must be Cancelled or Completed"))

	project = frappe.get_doc("Project", project)
	frappe.has_permission(doc=project, throw=True)

	for task in frappe.get_all("Task", dict(project=project.name)):
		frappe.db.set_value("Task", task.name, "status", status)

	project.status = status
	project.save()


def get_holiday_list(company=None):
	if not company:
		company = get_default_company() or frappe.get_all("Company")[0].name

	holiday_list = frappe.get_cached_value("Company", company, "default_holiday_list")
	if not holiday_list:
		frappe.throw(
			_("Please set a default Holiday List for Company {0}").format(
				frappe.bold(get_default_company())
			)
		)
	return holiday_list


def get_users_email(doc):
	return [d.email for d in doc.users if frappe.db.get_value("User", d.user, "enabled")]


def calculate_total_purchase_cost(project: str | None = None):
	if project:
		pitem = qb.DocType("Purchase Invoice Item")
		frappe.qb.DocType("Purchase Invoice Item")
		total_purchase_cost = (
			qb.from_(pitem)
			.select(Sum(pitem.base_net_amount))
			.where((pitem.project == project) & (pitem.docstatus == 1))
			.run(as_list=True)
		)
		return total_purchase_cost
	return None


@frappe.whitelist()
def recalculate_project_total_purchase_cost(project: str | None = None):
	if project:
		total_purchase_cost = calculate_total_purchase_cost(project)
		frappe.db.set_value(
			"Project",
			project,
			"total_purchase_cost",
			(total_purchase_cost and total_purchase_cost[0][0] or 0),
		)
