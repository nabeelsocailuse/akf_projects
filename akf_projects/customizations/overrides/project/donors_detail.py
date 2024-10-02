import frappe, ast

@frappe.whitelist()
def get_donors(filters):
    filters = ast.literal_eval(filters)

    return frappe.db.sql(""" 
        select 
            pd.donor_id, pd.donor_name, (d.name) as donation, d.status
        from 
            `tabDonation` d inner join `tabPayment Detail` pd on (d.name=pd.parent)
        where 
            d.is_return = 0
            and d.docstatus = %(docstatus)s
            and pd.project_id = %(project_id)s
        group by 
            d.name
        order by 
            d.name asc
     """, filters, as_dict=1)