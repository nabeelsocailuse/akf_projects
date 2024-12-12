#main-dashboard
import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_information(project=None):
    return {
        "region_wise_survey": get_region_wise_survey(project),
        "district_wise_survey": get_district_wise_survey(project),
        "tehsil_wise_survey": get_tehsil_wise_survey(project),
        "product_wise_survey": get_product_wise_survey(project),
        "survey_forms_count": get_total_survey_forms(project),
        "project_status": get_project_status(project),
        "approved_vs_unapproved_projects": get_approved_vs_unapproved_projects(project),
    }

def get_region_wise_survey(project=None):
    query = """
        SELECT 
            CASE
                WHEN custom_region IS NULL OR custom_region = '' THEN 'N/A'
                ELSE custom_region
            END AS custom_region,
            COUNT(name) as survey_count
        FROM `tabProject`
        GROUP BY 
            CASE
                WHEN custom_region IS NULL OR custom_region = '' THEN 'N/A'
                ELSE custom_region
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
                WHEN custom_district IS NULL OR custom_district = '' THEN 'N/A'
                ELSE custom_district
            END AS custom_district,
            COUNT(name) as survey_count
        FROM `tabProject`
        GROUP BY 
            CASE
                WHEN custom_district IS NULL OR custom_district = '' THEN 'N/A'
                ELSE custom_district
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
                WHEN custom_tehsil IS NULL OR custom_tehsil = '' THEN 'N/A'
                ELSE custom_tehsil
            END AS custom_tehsil,
            COUNT(name) as survey_count
        FROM `tabProject`
        GROUP BY 
            CASE
                WHEN custom_tehsil IS NULL OR custom_tehsil = '' THEN 'N/A'
                ELSE custom_tehsil
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
                WHEN custom_product IS NULL OR custom_product = '' THEN 'N/A'
                ELSE custom_product
            END AS custom_product,
            COUNT(name) as survey_count
        FROM `tabProject`
        GROUP BY 
            CASE
                WHEN custom_product IS NULL OR custom_product = '' THEN 'N/A'
                ELSE custom_product
            END      
    """
    result = frappe.db.sql(query, as_dict=False)
    # frappe.msgprint("product:")
    # frappe.msgprint(frappe.as_json(result))
    
    # total_surveys = sum(row[1] for row in result)
    total_surveys = 0
    return {"data": result, "total_surveys": total_surveys}

def get_project_status(project=None):
    # Query for projects with completed and in-progress status
    project_query = """
        SELECT 
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) AS completed,
            COUNT(CASE WHEN status = 'Open' THEN 1 END) AS in_progress
        FROM `tabProject`
    """
    project_result = frappe.db.sql(project_query, as_dict=1)

    # Query to count projects that have any overdue tasks
    delayed_query = """
        SELECT COUNT(DISTINCT project) as delayed_project
        FROM `tabTask`
        WHERE status = 'Overdue'
        AND project IS NOT NULL
    """
    delayed_result = frappe.db.sql(delayed_query, as_dict=1)
    # frappe.msgprint(frappe.as_json(delayed_result))
    
    return {
        "completed": project_result[0].completed or 0,
        "in_progress": project_result[0].in_progress or 0,
        "delayed": delayed_result[0].delayed_project or 0
    }

def get_approved_vs_unapproved_projects(project=None):
    query = """
        SELECT 
            COUNT(CASE WHEN approval_status = 'Pending' THEN 1 END) AS pending,
            COUNT(CASE WHEN approval_status = 'Approved By Program Manager' THEN 1 END) AS approved_by_pm,
            COUNT(CASE WHEN approval_status = 'Approved by the CEO' THEN 1 END) AS approved_by_ceo
        FROM `tabProject`
    """
    result = frappe.db.sql(query, as_dict=False)
    
    pending = result[0][0] if result else 0
    approved_by_pm = result[0][1] if result else 0
    approved_by_ceo = result[0][2] if result else 0
    
    return {
        "pending": pending,
        "approved_by_pm": approved_by_pm,
        "approved_by_ceo": approved_by_ceo
    }

def get_total_survey_forms(project=None):
    query = """
        SELECT 
            COUNT(name) as survey_count
        FROM `tabProject`
    """
    result = frappe.db.sql(query, as_dict=False)
    
    return result[0][0] if result else 0

