import frappe

# https://erp.alkhidmat.org/api/method/akf_projects.apis.api.get_project_details
@frappe.whitelist(allow_guest=True)
def get_project_details():
    return frappe.db.sql(""" Select p.*, t.*
            From 
                `tabProject` p inner join `tabTask` t on (p.name=t.project)
            Where 
                p.docstatus=0
            group by 
                t.project, t.name 
            """, as_dict=1)