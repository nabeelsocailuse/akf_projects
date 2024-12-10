#main-dashboard
import frappe
from frappe import _
from frappe.utils import getdate, add_days, nowdate


@frappe.whitelist(allow_guest=True)
def get_information(project=None):
    return {
        "region_wise_survey": get_region_wise_survey(project),
        "district_wise_survey": get_district_wise_survey(project),
        "tehsil_wise_survey": get_tehsil_wise_survey(project),
        "product_wise_survey": get_product_wise_survey(project),
        "allocated_vs_unallocated_survey": get_allocated_vs_unallocated_survey(project),
        "approved_vs_unapproved_survey": get_approved_vs_unapproved_survey(project),
        "survey_forms_count": get_total_survey_forms(project),
    }

def get_region_wise_survey(project=None):
    query = """
        SELECT 
            CASE
                WHEN region IS NULL OR region = '' THEN 'N/A'
                ELSE region
            END AS region,
            COUNT(name) as survey_count
        FROM `tabProject Survey Forms`
        GROUP BY 
            CASE
                WHEN region IS NULL OR region = '' THEN 'N/A'
                ELSE region
            END      
    """
    result = frappe.db.sql(query, as_dict=False)
    # frappe.msgprint("Region:")
    # frappe.msgprint(frappe.as_json(result))
    
    # total_surveys = sum(row[1] for row in result)
    total_surveys = 0
    return {"data": result, "total_surveys": total_surveys}

def get_district_wise_survey(project=None):
    query = """
        SELECT 
            CASE
                WHEN district IS NULL OR district = '' THEN 'N/A'
                ELSE district
            END AS district,
            COUNT(name) as survey_count
        FROM `tabProject Survey Forms`
        GROUP BY 
            CASE
                WHEN district IS NULL OR district = '' THEN 'N/A'
                ELSE district
            END      
    """
    result = frappe.db.sql(query, as_dict=False)
    # frappe.msgprint("district:")
    # frappe.msgprint(frappe.as_json(result))
    
    # total_surveys = sum(row[1] for row in result)
    total_surveys = 0
    return {"data": result, "total_surveys": total_surveys}

def get_tehsil_wise_survey(project=None):
    query = """
        SELECT 
            CASE
                WHEN tehsil IS NULL OR tehsil = '' THEN 'N/A'
                ELSE tehsil
            END AS tehsil,
            COUNT(name) as survey_count
        FROM `tabProject Survey Forms`
        GROUP BY 
            CASE
                WHEN tehsil IS NULL OR tehsil = '' THEN 'N/A'
                ELSE tehsil
            END      
    """
    result = frappe.db.sql(query, as_dict=False)
    # frappe.msgprint("tehsil:")
    # frappe.msgprint(frappe.as_json(result))
    
    # total_surveys = sum(row[1] for row in result)
    total_surveys = 0
    return {"data": result, "total_surveys": total_surveys}

def get_product_wise_survey(project=None):
    query = """
        SELECT 
            CASE
                WHEN product IS NULL OR product = '' THEN 'N/A'
                ELSE product
            END AS product,
            COUNT(name) as survey_count
        FROM `tabProject Survey Forms`
        GROUP BY 
            CASE
                WHEN product IS NULL OR product = '' THEN 'N/A'
                ELSE product
            END      
    """
    result = frappe.db.sql(query, as_dict=False)
    # frappe.msgprint("product:")
    # frappe.msgprint(frappe.as_json(result))
    
    # total_surveys = sum(row[1] for row in result)
    total_surveys = 0
    return {"data": result, "total_surveys": total_surveys}

def get_allocated_vs_unallocated_survey(project=None):
    query = """
        SELECT 
            COUNT(CASE WHEN allocation_status = 'Allocated' THEN 1 END) AS allocated,
            COUNT(CASE WHEN allocation_status = 'Unallocated' THEN 1 END) AS unallocated
        FROM `tabProject Survey Forms`
    """
    result = frappe.db.sql(query, as_dict=False)
    
    allocated = result[0][0] if result else 0
    unallocated = result[0][1] if result else 0

    
    return {
        "allocated": allocated,
        "unallocated": unallocated
    }

def get_approved_vs_unapproved_survey(project=None):
    query = """
        SELECT 
            COUNT(CASE WHEN approval_status = 'Pending' THEN 1 END) AS pending,
            COUNT(CASE WHEN approval_status = 'Verified By Regional' THEN 1 END) AS verified,
            COUNT(CASE WHEN approval_status = 'Approved By Head Office' THEN 1 END) AS approved
        FROM `tabProject Survey Forms`
    """
    result = frappe.db.sql(query, as_dict=False)
    
    pending = result[0][0] if result else 0
    verified = result[0][1] if result else 0
    approved = result[0][2] if result else 0

    
    return {
        "pending": pending,
        "verified": verified,
        "approved": approved
    }

def get_total_survey_forms(project=None):
    query = """
        SELECT 
            COUNT(name) as survey_count
        FROM `tabProject Survey Forms`
    """
    result = frappe.db.sql(query, as_dict=False)
    
    return result[0][0] if result else 0

