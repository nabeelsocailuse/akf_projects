import frappe

@frappe.whitelist()
def get_funds_detail(project: str | None = None, total_fund_allocated: float | None = None):
    if (project):
        
        allocated_fund = get_allocated_amount(project)
        consumed_fund = get_consumed_amount(project)
        pledge_fund = get_pledge_amount(project)
        return {
            "allocated_fund": allocated_fund[0][0] if(allocated_fund) else 0.0,
            "consumed_fund": consumed_fund,
            'pledge_fund': pledge_fund[0][0] if(pledge_fund) else 0.0
        }

def get_allocated_amount(project):
    return frappe.db.sql(f""" 
            Select sum(credit) 
            From `tabGL Entry` gl
            Where voucher_type in ("Donation", "Fund Transfer")
                and is_cancelled=0
                and account in (select name from `tabAccount` where disabled=0 and is_group=0 and account_type='Equity' and name=gl.account)
                and project = '{project}'
        """)
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
        Select sum(credit)
        From `tabGL Entry` gl
        Where
            voucher_type in ("Donation", "Fund Transfer")
            and is_cancelled=0
            and account in (select name from `tabAccount` where disabled=0 and is_group=0 and account_type='Equity' and name=gl.account)
            and voucher_no in (select name from `tabDonation` where docstatus=1 and contribution_type='Pledge' and name=gl.voucher_no )
            and project = '{project}'
                  """)