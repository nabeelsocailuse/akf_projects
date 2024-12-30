import frappe, ast

""" 
Nabeel Saleem
Date: 23-12-2024
"""
@frappe.whitelist()
def get_transactions(filters=None):
    if(type(filters) == str): filters = ast.literal_eval(filters) 
    
    args = {}
    args.update(get_donation(filters))
    args.update(get_funds_transfer(filters))
    args.update(get_purchasing(filters))
    
    # total_allocation = (donation + received_pledge + received_funds)
    total_allocation = args['donation'] + args['received_pledge'] +  args['received_funds']
    total_pledge = args['pending_pledge']
    transfered_funds = args['transfered_funds']
    received_funds = args['received_funds']
    total_purchase = args['purchased_amount']
    # balance_amount = (total_allocation + received_funds -( transfered_funds + total_purchase ))
    balance_amount = (total_allocation -( transfered_funds + total_purchase ))
    return{
        "total_allocation": total_allocation,
        "total_pledge": total_pledge,
        "transfered_funds": transfered_funds,
        "received_funds": received_funds,
        "total_purchase": total_purchase,
        "remaining_amount": balance_amount
    }

def get_donation(filters):
    def get_conditions():
        conditions = " and d.company = %(company)s " if(filters.get('company')) else ""
        conditions += " and p.cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
        conditions += " and p.pay_service_area = %(service_area)s " if(filters.get('service_area')) else ""
        conditions += " and p.pay_subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
        conditions += " and p.pay_product = %(product)s " if(filters.get('product')) else ""
        conditions += " and p.project = %(project)s " if(filters.get('project')) else ""
        conditions += " and p.donor = %(donor)s " if(filters.get('donor')) else ""
        conditions += " and p.equity_account = %(account)s " if(filters.get('account')) else ""
        return conditions
        
    data = frappe.db.sql(f""" 
    Select 
        ifnull(sum(case when (d.contribution_type='Donation' and d.status!='Return') then p.net_amount else 0 end),0) as donation_received,
        ifnull(sum(case when d.status='Return' then p.net_amount else 0 end),0) as donation_returned,
        ifnull(sum(case when d.contribution_type='Pledge' then (p.net_amount-p.base_outstanding_amount) else 0 end),0) as received_pledge,
        ifnull(sum(case when d.contribution_type='Pledge' then p.base_outstanding_amount else 0 end),0) as pending_pledge
    From
        `tabDonation` d
        INNER JOIN  
        `tabPayment Detail` p
        ON (d.name=p.parent)
    Where
        d.docstatus=1
        {get_conditions()}
        """, filters, as_dict=1)
    args = {
        "donation": 0.0, 
        "received_pledge": 0.0,
        "pending_pledge": 0.0,
    }
    for d in data:
        args.update({
            "donation": (d.donation_received - d.donation_returned), 
            "received_pledge": d.received_pledge,
            "pending_pledge": d.pending_pledge,
        })
    return args

def get_funds_transfer(filters):
    def get_transfered_funds():
        def get_conditions():
            conditions = " and ff_company = %(company)s " if(filters.get('company')) else ""
            conditions += " and ff_cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
            conditions += " and ff_service_area = %(service_area)s " if(filters.get('service_area')) else ""
            conditions += " and ff_subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
            conditions += " and ff_product = %(product)s " if(filters.get('product')) else ""
            conditions += " and project = %(project)s " if(filters.get('project')) else ""
            conditions += " and ff_donor = %(donor)s " if(filters.get('donor')) else ""
            conditions += " and ff_account = %(account)s " if(filters.get('account')) else ""
            return conditions
            
        return frappe.db.sql(f""" 
        Select 
            sum(ff_transfer_amount) as transfer_amount
        From
            `tabFunds Transfer From` 
        Where
            docstatus=1
            {get_conditions()}
        """, filters)[0][0] or 0.0
        
    def get_received_funds():
        def get_conditions():
            conditions = " and ft_company = %(company)s " if(filters.get('company')) else ""
            conditions += " and ft_cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
            conditions += " and ft_service_area = %(service_area)s " if(filters.get('service_area')) else ""
            conditions += " and ft_subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
            conditions += " and ft_product = %(product)s " if(filters.get('product')) else ""
            conditions += " and project = %(project)s " if(filters.get('project')) else ""
            conditions += " and ft_donor = %(donor)s " if(filters.get('donor')) else ""
            conditions += " and ft_account = %(account)s " if(filters.get('account')) else ""
            return conditions
        
        return frappe.db.sql(f""" 
        Select 
            sum(ft_amount) as transfer_amount
        From
            `tabFunds Transfer To`
        Where
            docstatus=1
            {get_conditions()}
        """, filters)[0][0] or 0.0

    return {
        "transfered_funds": get_transfered_funds(),
        "received_funds": get_received_funds()
    }

def get_purchasing(filters):
    def get_conditions():
        conditions = " and company = %(company)s " if(filters.get('company')) else ""
        conditions += " and cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
        conditions += " and program = %(service_area)s " if(filters.get('service_area')) else ""
        conditions += " and subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
        conditions += " and product = %(product)s " if(filters.get('product')) else ""
        conditions += " and project = %(project)s " if(filters.get('project')) else ""
        conditions += " and donor = %(donor)s " if(filters.get('donor')) else ""
        conditions += " and account = %(account)s " if(filters.get('account')) else ""
        return conditions
    return {
        "purchased_amount": frappe.db.sql(f"""
            Select 
                sum(debit) total_consumed
            From 
                `tabGL Entry` gl
            Where 
                is_cancelled=0
                and ifnull(party, '')!=''
                and voucher_type  in ('Purchase Invoice')
                and debit>0.0
                {get_conditions()}
            """, filters)[0][0] or 0.0
    }