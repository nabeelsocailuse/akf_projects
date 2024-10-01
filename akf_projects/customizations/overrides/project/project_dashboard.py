from frappe import _


def get_dashboard_data(data):
    data["transactions"].append(
        {
            "label": _("Donation Details"), 
            "items": ["Donation", "Funds Transfer", "Payment Entry"]
        }
    )
    return data
