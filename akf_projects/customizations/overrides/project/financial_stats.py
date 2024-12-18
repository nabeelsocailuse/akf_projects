import frappe

@frappe.whitelist()
def get_funds_detail(project: str | None = None, total_fund_allocated: float | None = None):
    if (project):
        
        allocated = get_allocated_amount(project) or 0.0
        consumed = get_consumed_amount(project) or 0.0 #Mubashir
        unpaid = get_unpaid_pledge(project) or 0.0
        paid = get_paid_pledge(project) or 0.0 
        
        allocated_fund = allocated + paid
        allocated_fund = allocated_fund - consumed if(allocated_fund>=consumed) else 0.0
        return {
            "allocated_fund": allocated_fund,
            "consumed_fund": consumed,
            'unpaid_pledge': unpaid,
            'paid_pledge': paid,
            'remaining_pledge': (unpaid - paid),
        }

def get_allocated_amount(project):
    
    result = frappe.db.sql(f""" 
        Select 
            sum(distinct gl.credit) credit,  sum(distinct gl.debit) debit
        From 
            `tabGL Entry` gl, `tabDonation` d, `tabFunds Transfer` ft
        Where 
            (gl.voucher_no = d.name or gl.voucher_no = ft.name)
            and d.contribution_type ='Donation'
            and gl.is_cancelled=0
            and voucher_type  in ('Donation', 'Funds Transfer')
            and gl.account in (select name from `tabAccount` where disabled=0 and account_type='Equity' and name=gl.account)
            and gl.project='{project}'
        Group By
          gl.name
        """, as_dict=1)
    
    return sum((d.credit-d.debit) for d in result)

def get_consumed_amount(project):
    return frappe.db.get_value(
            "GL Entry",
            {"voucher_type": "Purchase Invoice","is_cancelled": 0, "project": project},
            "sum(debit)",
        ) or 0.0

def get_unpaid_pledge(project):
    return frappe.db.sql(f""" 
        Select ifnull(sum(credit),0)
        From `tabGL Entry` gl
        Where
            is_cancelled=0
            and voucher_no in (select name from `tabDonation` where docstatus=1 and contribution_type='Pledge' and name=gl.voucher_no)
            and project = '{project}'
                  """)[0][0] or 0.0

def get_paid_pledge(project):
    return frappe.db.sql(f""" 
        Select ifnull(sum(credit),0)
        From `tabGL Entry` gl
        Where
            is_cancelled=0
            and voucher_type='Payment Entry'
            and against_voucher in (select name from `tabDonation` where docstatus=1 and contribution_type='Pledge' and name=gl.against_voucher)
            and project = '{project}'
                  """)[0][0] or 0.0
