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
	# total_allocation = args['donation'] + args['received_pledge'] +  args['received_funds']
	# total_allocation = args['donation']
	total_allocation = get_remaining_balance(filters)
	total_pledge = args['pending_pledge']
	transfered_funds = args['transfered_funds']
	received_funds = args['received_funds']
	total_purchase = args['purchased_amount']
	# balance_amount = (total_allocation + received_funds -( transfered_funds + total_purchase ))
	# balance_amount = (total_allocation -( transfered_funds + total_purchase ))
	balance_amount = get_remaining_balance(filters)
	balance_amount = (balance_amount - total_purchase )
	filters.update({
		"total_allocation": total_allocation,
		"total_purchase": total_purchase,
		"balance_amount": balance_amount,
	})

	set_project_allocation(filters)

	return{
		"total_allocation": total_allocation,
		"total_pledge": total_pledge,
		"transfered_funds": transfered_funds,
		"received_funds": received_funds,
		"total_purchase": total_purchase,
		"remaining_amount": balance_amount
	}

def set_project_allocation(filters):
	frappe.db.sql(""" Update `tabProject`
				Set custom_total_allocation = %(total_allocation)s,
					custom_total_purchase = %(total_purchase)s,
					custom_remaining_allocation = %(balance_amount)s
				Where
					name = %(project)s
				""",filters )

def get_donation(filters):
	def get_conditions_donations():
		conditions = " and company = %(company)s " if(filters.get('company')) else ""
		conditions += " and cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
		conditions += " and service_area = %(service_area)s " if(filters.get('service_area')) else ""
		conditions += " and subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
		conditions += " and product = %(product)s " if(filters.get('product')) else ""
		conditions += " and project = %(project)s " if(filters.get('project')) else ""
		conditions += " and donor = %(donor)s " if(filters.get('donor')) else ""
		conditions += " and account = %(account)s " if(filters.get('account')) else ""
		return conditions

	donation = frappe.db.sql(f"""
 		Select
			sum(credit-debit) as balance
		From
  			`tabGL Entry` gl
		Where
  			docstatus=1
			and is_cancelled=0
			and account in (select name from tabAccount where account_type="Equity")
			{get_conditions_donations()}
		-- Group By
			-- cost_center, account, donor
		-- Having
			-- balance>0
		-- Order By
			-- balance desc
	""", filters, as_dict=0)
	# frappe.throw(f"{donation}")
	def get_conditions_pledge():
		conditions = " and d.company = %(company)s " if(filters.get('company')) else ""
		conditions += " and p.cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
		conditions += " and p.pay_service_area = %(service_area)s " if(filters.get('service_area')) else ""
		conditions += " and p.pay_subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
		conditions += " and p.pay_product = %(product)s " if(filters.get('product')) else ""
		conditions += " and p.project = %(project)s " if(filters.get('project')) else ""
		conditions += " and p.donor = %(donor)s " if(filters.get('donor')) else ""
		conditions += " and p.equity_account = %(account)s " if(filters.get('account')) else ""
		return conditions

	pledge = frappe.db.sql(f"""
		Select
			ifnull(sum(case when (d.contribution_type='Donation' and d.status!='Return') then p.net_amount else 0 end),0) as donation_received,
			ifnull(sum(case when d.status='Return' then p.net_amount else 0 end),0) as donation_returned,
			ifnull(sum(case when d.contribution_type='Pledge' then (p.net_amount-p.outstanding_amount) else 0 end),0) as received_pledge,
			ifnull(sum(case when d.contribution_type='Pledge' then p.outstanding_amount else 0 end),0) as pending_pledge
		From
			`tabDonation` d
			INNER JOIN
			`tabPayment Detail` p
			ON (d.name=p.parent)
		Where
			d.docstatus=1
			{get_conditions_pledge()}
	""", filters, as_dict=1)

	args = {
		"donation": donation[0][0] or 0.0,
		"received_pledge": 0.0,
		"pending_pledge": 0.0,
	}
	for d in pledge:
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
		conditions += " and service_area = %(service_area)s " if(filters.get('service_area')) else ""
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

def get_remaining_balance(filters):
	def get_conditions():
		conditions = " and company = %(company)s " if(filters.get('company')) else ""
		conditions += " and cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
		conditions += " and service_area = %(service_area)s " if(filters.get('service_area')) else ""
		conditions += " and subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
		conditions += " and product = %(product)s " if(filters.get('product')) else ""
		conditions += " and project = %(project)s " if(filters.get('project')) else ""
		conditions += " and donor = %(donor)s " if(filters.get('donor')) else ""
		conditions += " and account = %(account)s " if(filters.get('account')) else ""
		return conditions
	return frappe.db.sql(f""" Select
			sum(credit-debit) as balance
		From
  			`tabGL Entry` gl
		Where
  			docstatus=1
			and is_cancelled=0
			and account in (select name from tabAccount where account_type="Equity")
			{get_conditions()}
	""", filters)[0][0] or 0.0