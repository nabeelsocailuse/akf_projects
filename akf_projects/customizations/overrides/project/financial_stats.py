import frappe, ast

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
            "total_allocated": allocated + paid,
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
            {"voucher_type": "Purchase Invoice","is_cancelled": 0, "party": ["!=", ""], "debit": [">", 0.0], "project": project},
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

""" 
Transition of Accounts and Stock

1- Donation
2- Funds Transfer
3- Purchase Invoice

"""
@frappe.whitelist()
def get_transactions(filters=None):
    if(type(filters) == str): filters = ast.literal_eval(filters) 
    conditions = get_conditions(filters)
    
    total_allocation = get_total_allocation(filters, conditions)
    transfered_funds = get_transfered_funds(filters, conditions)
    received_funds = get_received_funds(filters, conditions)
    total_purchase = get_total_purchasing(filters, conditions)
    total_pledge = get_total_pledge(filters, conditions)
    
    total_allocation = total_allocation + received_funds
    
    return{
        "total_allocation": total_allocation,
        "total_pledge": total_pledge,
        "transfered_funds": transfered_funds,
        "received_funds": received_funds,
        "total_purchase": total_purchase,
        "remaining_amount": (total_allocation + received_funds -( transfered_funds + total_purchase ))
    }
    
def get_conditions(filters, skip_pledge=False):
    conditions = " and company = %(company)s " if(filters.get('company')) else ""
    conditions += " and cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
    conditions += " and program = %(service_area)s " if(filters.get('service_area')) else ""
    conditions += " and subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
    conditions += " and product = %(product)s " if(filters.get('product')) else ""
    conditions += " and project = %(project)s " if(filters.get('project')) else ""
    conditions += " and donor = %(donor)s " if(filters.get('donor')) else ""
    conditions += " and account = %(account)s " if(filters.get('account') and (not skip_pledge)) else ""
    return conditions
   
def get_total_allocation(filters, conditions):
    conditions = get_conditions(filters, skip_pledge=True)
    return frappe.db.sql(f""" 
    Select 
        sum(credit) as total_allocation
    From 
        `tabGL Entry` gl
    Where 
        is_cancelled=0
        and ifnull(party,'')!=''
        and voucher_type in ('Donation', 'Payment Entry')
        and against_voucher_type in ('Donation')
        -- and account in (select name from `tabAccount` where account_type='Equity' and name = gl.account)
        {conditions}
    """, filters)[0][0] or 0.0

def get_total_pledge(filters, conditions):
    
    def get_actual_pledge():
        return frappe.db.sql(f""" 
            Select ifnull(sum(credit),0), (select sum(credit) from `tabGL Entry` where against_voucher =voucher_no)
            From `tabGL Entry` gl
            Where
                is_cancelled=0
                and voucher_no in (select name from `tabDonation` where docstatus=1 and contribution_type='Pledge' and name=gl.voucher_no)
                {conditions}
                    """, filters)[0][0] or 0.0

    
    def get_receive_pledge():
        return frappe.db.sql(f""" 
            Select ifnull(sum(credit),0)
            From `tabGL Entry` gl
            Where
                is_cancelled=0
                and voucher_type in ('Payment Entry')
                and against_voucher in (select name from `tabDonation` where docstatus=1 and contribution_type='Pledge' and name=gl.against_voucher)
                and account like '%%Debtors%%'
                {conditions}
                """, filters)[0][0] or 0.0

    actual_pledge = get_actual_pledge()
    receive_pledge = get_receive_pledge()
    # frappe.throw(f"{actual_pledge}")
    return (actual_pledge - receive_pledge)

def get_transfered_funds(filters, conditions):
    return frappe.db.sql(f"""
    Select 
        sum(debit) total_balance
    From 
        `tabGL Entry` gl
    Where 
        is_cancelled=0
        and ifnull(party, '')!=''
        and against_voucher_type  in ('Funds Transfer')
        {conditions}
    """, filters)[0][0] or 0.0

def get_received_funds(filters, conditions):
    return frappe.db.sql(f"""
    Select 
        sum(credit) total_balance
    From 
        `tabGL Entry` gl
    Where 
        is_cancelled=0
        and ifnull(party, '')!=''
        and against_voucher_type  in ('Funds Transfer')
        {conditions}
    """, filters)[0][0] or 0.0

def get_total_purchasing(filters, conditions):
    return frappe.db.sql(f"""
    Select 
        sum(debit) total_consumed
    From 
        `tabGL Entry` gl
    Where 
        is_cancelled=0
        and ifnull(party, '')!=''
        and voucher_type  in ('Purchase Invoice')
        and debit>0.0
        {conditions}
    """, filters)[0][0] or 0.0

