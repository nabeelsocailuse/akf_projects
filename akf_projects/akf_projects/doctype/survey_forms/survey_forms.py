# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
import requests
from datetime import datetime
from frappe.exceptions import DocumentLockedError

from frappe.model.document import Document

class SurveyForms(Document):
	pass

@frappe.whitelist()
def fetch_api_data():
    """
    Fetches data from the API, processes it, and inserts or updates records in 'Survey Forms' documents.
    """
    # API endpoint and token
    url = "https://kf.alkhidmat.org/api/v2/assets.json"
    api_token = "4db5afa38c481278d65595e6ac8fe143938c1835"

    # Set headers with Authorization
    headers = {
        "Authorization": f"Token {api_token}"
    }

    # Make the API request
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code != 200:
        print(f"Failed to fetch data from API. Status code: {response.status_code}")
        return

    # Load the JSON data
    data = response.json()
    results = data['results']

    count = 0

    for form in results:
        form_url = form.get("data")
        
        if form_url:       
            form_id = form.get("uid")
            form_label = form.get("name")

            form_data_response = requests.get(form_url, headers=headers, verify=False)
            if form_data_response.status_code != 200:
                print(f"Failed to fetch form data from {form_url}. Status code: {form_data_response.status_code}")
                continue

            form_data = form_data_response.json()
                       
            for record in form_data.get('results', []):
                # Extract the record ID (_uuid) and other necessary fields
                record_id = record.get('_uuid')
                id = record.get('_id')
                start_time = convert_to_datetime(record.get('start'))
                end_time = convert_to_datetime(record.get('end'))
                version = record.get('_version')
                status = record.get('_status')
                validation_status = record.get('_validation_status')
                submission_time = convert_to_datetime(record.get('_submission_time'))
                submitted_by = record.get('_submitted_by')
                
                if not record_id:
                    continue
                if not isinstance(validation_status, str):
                    validation_status = None

                # Convert record to HTML table
                html_table = generate_html_table_for_record(record)

                # Check if a document with the same name (record_id) already exists
                survey_form = frappe.get_doc('Survey Forms', record_id) if frappe.db.exists('Survey Forms', record_id) else frappe.new_doc('Survey Forms')
                
                # Update or create the new document
                survey_form.update({
                    'name': record_id,
                    'form_id': form_id,
                    'form_label': form_label,
                    'record_id': record_id,
                    'html_content': html_table,
                    'id': id,
                    'start_time': start_time,
                    'end_time': end_time,
                    'version': version,
                    'status': status,
                    'validation_status': validation_status,
                    'submitted_by': submitted_by,
                    'submission_time': submission_time,
                })

                # Save the document to insert or update
                try:
                    survey_form.save(ignore_permissions=True)
                    frappe.db.commit()
                    count += 1
                    print(f"Inserted/Updated record {record_id}.")
                except Exception as e:
                    print(f"Error saving document {record_id}: {e}")
                    frappe.db.rollback()
                    continue

    print(f"Data fetched and {count} records inserted or updated in 'Survey Forms'.")

@frappe.whitelist()
def convert_to_datetime(iso_datetime_str):
    """
    Converts ISO 8601 datetime string to a Python datetime object and formats it.
    The output format is "%Y-%m-%d %H:%M:%S".
    """
    if iso_datetime_str:
        try:
            # Parse the ISO datetime string, including timezone info
            parsed_datetime = datetime.fromisoformat(iso_datetime_str.replace("Z", "+00:00"))
            # Return the datetime in the format 'YYYY-MM-DD HH:MM:SS'
            return parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            print(f"Error parsing datetime string: {iso_datetime_str} -> {e}")
            return None


@frappe.whitelist()
def generate_html_table_for_record(record):
    """
    Generates an HTML table for a single record.
    """
    if not isinstance(record, dict):
        return "<p>No valid data available for this record.</p>"

    # Initialize HTML table
    html = """
    <div style="overflow: auto; max-width: 100%; max-height: 500px; border: 1px solid #ddd; padding: 5px;">
        <table border='1' style="border-collapse: collapse; width: 100%;">
    """

    # Add table headers and rows
    html += "<thead><tr><th>Field</th><th>Value</th></tr></thead>"
    html += "<tbody>"

    for key, value in record.items():
        # Convert lists and dictionaries to readable string format
        if isinstance(value, list):
            value = ', '.join(map(str, value))
        elif isinstance(value, dict):
            value = ', '.join(f"{k}: {v}" for k, v in value.items())
        html += f"<tr><td>{key}</td><td>{value}</td></tr>"

    html += "</tbody></table></div>"
    
    return html





"""The below function is inserting the records in batches with frappe.db.sql method"""
# @frappe.whitelist()
# def fetch_api_data():
#     """
#     Fetches data from the API, processes it, and inserts or updates records in 'Survey Forms' documents.
#     """
#     # API endpoint and token
#     url = "https://kf.alkhidmat.org/api/v2/assets.json"
#     api_token = "4db5afa38c481278d65595e6ac8fe143938c1835"

#     # Set headers with Authorization
#     headers = {
#         "Authorization": f"Token {api_token}"
#     }

#     # Make the API request
#     response = requests.get(url, headers=headers, verify=False)
#     if response.status_code != 200:
#         print(f"Failed to fetch data from API. Status code: {response.status_code}")
#         return

#     # Load the JSON data
#     data = response.json()
#     results = data['results']

#     # Batch size for insertion and update
#     batch_size = 1000
#     insert_data = []    
#     count = 0 

#     for form in results:
#         form_url = form.get("data")
        
#         if form_url:       
#             form_id = form.get("uid")
#             form_label = form.get("name")

#             form_data_response = requests.get(form_url, headers=headers, verify=False)
#             if form_data_response.status_code != 200:
#                 print(f"Failed to fetch form data from {form_url}. Status code: {form_data_response.status_code}")
#                 continue

#             form_data = form_data_response.json()
                       
#             for record in form_data.get('results', []):
#                 # Extract the record ID (_uuid) and other necessary fields
#                 record_id = record.get('_uuid')
#                 id = record.get('_id')
#                 start_time = convert_to_datetime(record.get('start'))
#                 end_time = convert_to_datetime(record.get('end'))
#                 version = record.get('_version')
#                 status = record.get('_status')
#                 validation_status = record.get('_validation_status')
#                 submission_time = convert_to_datetime(record.get('_submission_time'))
#                 submitted_by = record.get('_submitted_by')
                
#                 if not record_id:
#                     continue
#                 if not isinstance(validation_status, str):
#                     validation_status = None

#                 # Convert record to HTML table
#                 html_table = generate_html_table_for_record(record)

#                 # Prepare data for insert (upsert logic)
#                 insert_data.append((
#                     record_id, form_id, form_label, record_id, html_table, id, start_time, end_time, version, 
#                     status, validation_status, submitted_by, submission_time
#                 ))
                
#                 if len(insert_data) >= batch_size:
#                     # Batch insert using SQL with ON DUPLICATE KEY UPDATE to handle duplicates
#                     try:
#                         frappe.db.sql("""
#                             INSERT INTO `tabSurvey Forms` 
#                             (name, form_id, form_label, record_id, html_content, id, start_time, end_time, version, status, validation_status, submitted_by, submission_time)
#                             VALUES {values}
#                             ON DUPLICATE KEY UPDATE 
#                                 form_label=VALUES(form_label),
#                                 html_content=VALUES(html_content),
#                                 id=VALUES(id),
#                                 start_time=VALUES(start_time),
#                                 end_time=VALUES(end_time),
#                                 version=VALUES(version),
#                                 status=VALUES(status),
#                                 validation_status=VALUES(validation_status),
#                                 submitted_by=VALUES(submitted_by),
#                                 submission_time=VALUES(submission_time)
#                         """.format(values=', '.join(['%s'] * len(insert_data))), tuple(insert_data))
#                         count += len(insert_data)
#                         print(f"Inserted/Updated batch of {len(insert_data)} documents.")
#                         insert_data = []
#                     except Exception as e:
#                         print(f"Error inserting batch: {e}")
#                         frappe.db.rollback()
#                         continue

#     # Final batch insert with upsert
#     if insert_data:
#         try:
#             frappe.db.sql("""
#                 INSERT INTO `tabSurvey Forms` 
#                 (name, form_id, form_label, record_id, html_content, id, start_time, end_time, version, status, validation_status, submitted_by, submission_time)
#                 VALUES {values}
#                 ON DUPLICATE KEY UPDATE 
#                     form_label=VALUES(form_label),
#                     html_content=VALUES(html_content),
#                     id=VALUES(id),
#                     start_time=VALUES(start_time),
#                     end_time=VALUES(end_time),
#                     version=VALUES(version),
#                     status=VALUES(status),
#                     validation_status=VALUES(validation_status),
#                     submitted_by=VALUES(submitted_by),
#                     submission_time=VALUES(submission_time)
#             """.format(values=', '.join(['%s'] * len(insert_data))), tuple(insert_data))
#             count += len(insert_data)
#             print(f"Inserted/Updated final batch of {len(insert_data)} documents.")
#         except Exception as e:
#             print(f"Error inserting remaining documents: {e}")
#             frappe.db.rollback()

#     frappe.db.commit()
#     print(f"Data fetched and {count} records inserted or updated in 'Survey Forms'.")


