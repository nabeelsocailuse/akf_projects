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
                    subject = f"Task Completed: {self.name}"
                    message = f"""
                                Dear {donor.get("donor_name")}, <br><br>
                                We are pleased to inform you that the task <b>{self.subject}</b> with 
                                task id <b>{self.name}</b> in the project <b>{self.project}</b> have been 
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
                        subject = f"Task Completed: {self.name}"
                        message = f"""
                                    Dear {donor.get("donor_name")}, <br><br>
                                    We are pleased to inform you that the task <b>{self.subject}</b> with 
                                    task id <b>{self.name}</b> in the project <b>{self.project}</b> have been 
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
