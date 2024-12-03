import frappe

@frappe.whitelist()
def get_funds_detail(project: str | None = None, total_fund_allocated: float | None = None):
    if (project):
        
        allocated_fund = get_allocated_amount(project)
        consumed_fund = get_consumed_amount(project)
        pledge_fund = get_pledge_amount(project)
        
        allocated_amount = allocated_fund[0][0] if(allocated_fund) else 0.0
        
        
        return {
            "allocated_fund": allocated_amount - consumed_fund,
            "consumed_fund": consumed_fund,
            'pledge_fund': pledge_fund[0][0] if(pledge_fund) else 0.0
        }

def get_allocated_amount(project):
    return frappe.db.sql(f""" select sum(credit)
        from `tabGL Entry` gl
        where is_cancelled=0
            and account in (select name from `tabAccount` where disabled=0 and is_group=0 and account_type in ('Equity') and name=gl.account)
            and project = '{project}' """)
    
    # return frappe.db.sql(f""" 
    #         Select sum(case when voucher_type in ("Donation", "Fund Transfer") then credit else 0 end) - sum(case when voucher_type in ("Payment Entry") then debit else 0 end)
    #         From `tabGL Entry` gl
    #         Where voucher_type in ("Donation", "Fund Transfer", "Payment Entry")
    #             and is_cancelled=0
    #             and account in (select name from `tabAccount` where disabled=0 and is_group=0 and account_type in ('Equity', 'Receivable') and name=gl.account)
    #             and project = '{project}'
    #     """)
    """ allocated_fund = frappe.db.get_value(
            "GL Entry",
            {"voucher_type": ["in", ["Donation", "Fund Transfer"]],"is_cancelled": 0, "project": project},
            "sum(credit)",
        ) or 0.0 """

def get_consumed_amount(project):
    return frappe.db.get_value(
            "GL Entry",
            {"voucher_type": "Purchase Invoice","is_cancelled": 0, "project": project},
            "sum(debit)",
        ) or 0.0

def get_pledge_amount(project):
    return frappe.db.sql(f""" 
        Select sum(case when voucher_type in ("Donation", "Fund Transfer") then credit else 0 end) - sum(case when voucher_type in ("Payment Entry") then debit else 0 end)
        From `tabGL Entry` gl
        Where
            voucher_type in ("Donation", "Fund Transfer", "Payment Entry")
            and is_cancelled=0
            and account in (select name from `tabAccount` where disabled=0 and is_group=0 and account_type in ('Equity', 'Receivable') and name=gl.account)
            and against_voucher in (select name from `tabDonation` where docstatus=1 and contribution_type='Pledge' and name=gl.voucher_no)
            and project = '{project}'
                  """)
