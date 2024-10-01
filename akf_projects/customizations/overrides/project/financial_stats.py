import frappe

@frappe.whitelist()
def get_funds_detail(project: str | None = None, total_fund_allocated: float | None = None):
    if (project):
        allocated_fund = frappe.db.get_value(
            "GL Entry",
            {"voucher_type": ["in", ["Donation", "Fund Transfer"]],"is_cancelled": 0, "project": project},
            "sum(credit)",
        ) or 0.0

        consumed_fund = frappe.db.get_value(
            "GL Entry",
            {"voucher_type": "Purchase Invoice","is_cancelled": 0, "project": project},
            "sum(debit)",
        ) or 0.0

        return {
            "allocated_fund": allocated_fund,
            "consumed_fund": consumed_fund,
        }