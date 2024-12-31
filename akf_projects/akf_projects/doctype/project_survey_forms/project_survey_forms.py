# Developer Mubashir Bashir

import frappe
import requests
from datetime import datetime
import json
import uuid
from frappe.exceptions import DocumentLockedError

from frappe.model.document import Document

class ProjectSurveyForms(Document):
	pass

# Frappe ORM Method
@frappe.whitelist()
def fetch_api_data():
    """
    Fetches data from the API, processes it, and inserts or updates records in 'Survey Forms' documents.
    """
    try:
        # API endpoint and token
        url = "https://kf.alkhidmat.org/api/v2/assets.json"
        api_token = "4db5afa38c481278d65595e6ac8fe143938c1835"

        headers = {
            "Authorization": f"Token {api_token}"
        }

        # Make the API request
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        data = response.json()
        results = data.get('results', [])

        count_updated = 0
        count_forms = 0
        count_failed = 0

        for form in results:
            form_url = form.get("data")
            
            if not form_url:
                continue
                
            count_forms += 1      
            form_id = form.get("uid")
            form_label = form.get("name")

            try:
                form_data_response = requests.get(form_url, headers=headers, verify=False)
                form_data_response.raise_for_status()
                form_data = form_data_response.json()
            except Exception as e:
                count_failed += 1
                frappe.log_error(f"Failed to fetch form data: {str(e)}", "Survey Form API Error")
                continue

            for record in form_data.get('results', []):
                try:
                    # Convert keys to lowercase
                    record = {key.lower(): value for key, value in record.items()}
                    
                    # Skip if no record_id
                    record_id = record.get('_uuid')
                    if not record_id:
                        continue

                    geolocation = record.get('_geolocation')
                    latitude = geolocation[0] if len(geolocation) >= 1 else None
                    longitude = geolocation[1] if len(geolocation) >= 2 else None

                    # Prepare document data
                    doc_data = {
                        'form_id': form_id,
                        'form_label': form_label,
                        'record_id': record_id,
                        'survey_form_json': frappe.as_json(record),
                        'id': record.get('_id'),
                        'start_time': convert_to_datetime(record.get('start')),
                        'end_time': convert_to_datetime(record.get('end')),
                        'version': record.get('_version'),
                        'status': record.get('_status'),
                        'validation_status': record.get('_validation_status') if isinstance(record.get('_validation_status'), str) else None,
                        'submitted_by': record.get('_submitted_by'),
                        'submission_time': convert_to_datetime(record.get('_submission_time')),
                        'region': record.get('region', ''),
                        'district': record.get('district', ''),
                        'teh,sil': record.get('tehsil', ''),
                        'uc': record.get('uc', ''),
                        'product': record.get('product', ''),
                        'longitude': longitude,
                        'latitude': latitude,
                        'village': record.get('village', '')
                    }

                    # Get or create document
                    existing_record = frappe.get_all('Project Survey Forms', 
                                                   filters={'record_id': record_id}, 
                                                   limit=1)
                    
                    if existing_record:
                        doc = frappe.get_doc('Project Survey Forms', existing_record[0].name)
                        doc.update(doc_data)
                    else:
                        doc = frappe.get_doc({
                            'doctype': 'Project Survey Forms',
                            **doc_data
                        })

                    doc.save(ignore_permissions=True)
                    count_updated += 1
                    print(f'form name: {form_label}, form id: {form_id}, record id: {record_id}')

                except Exception as e:
                    frappe.log_error(
                        f"Error processing record {record_id}: {str(e)}", 
                        "Survey Form Processing Error"
                    )
                    continue

            # Commit after each form's records are processed
            frappe.db.commit()

        print(
            f"Data fetched successfully:\n"
            f"- {count_updated} records inserted/updated\n"
            f"- {count_forms} forms processed\n"
            f"- {count_failed} forms failed to fetch"
        )

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(str(e), "Survey Form API Main Error")
        frappe.throw("Error fetching survey form data. Check error logs for details.")


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
def generate_html_table_for_record(json_data):
    """
    Generates an HTML table for a single record.
    """
    try:
        # Convert string JSON to dict if needed
        if isinstance(json_data, str):
            json_data = frappe.parse_json(json_data)
            
        if not isinstance(json_data, dict):
            return "<p>No valid data available for this record.</p>"

        # CSS styles
        styles = """
            <style>
                .survey-table-container {
                    overflow: auto;
                    max-width: 100%;
                    max-height: 500px;
                    border: 1px solid #ddd;
                    padding: 10px;
                    margin: 10px 0;
                }
                .survey-table {
                    border-collapse: collapse;
                    width: 100%;
                    font-size: 13px;
                }
                .survey-table th {
                    background-color: #f8f9fa;
                    padding: 8px;
                    text-align: left;
                    border: 1px solid #ddd;
                }
                .survey-table td {
                    padding: 8px;
                    border: 1px solid #ddd;
                    word-break: break-word;
                }
                .survey-table tr:nth-child(even) {
                    background-color: #f9f9f9;
                }
                .attachment-link {
                    display: inline-block;
                    margin: 2px 0;
                    color: #0066cc;
                    text-decoration: none;
                }
                .attachment-link:hover {
                    text-decoration: underline;
                }
            </style>
        """

        # Initialize HTML table with styles
        html = f"""
            {styles}
            <div class="survey-table-container">
                <table class="survey-table">
                    <thead>
                        <tr>
                            <th>Field</th>
                            <th>Value</th>
                        </tr>
                    </thead>
                    <tbody>
        """

        # Process and sort fields
        for key in sorted(json_data.keys()):
            value = json_data[key]
            
            # Format field name
            display_key = key.replace('_', ' ').strip().title()

            # Special handling for attachments
            if key == "_attachments" and isinstance(value, list):
                links = []
                for attachment in value:
                    download_url = attachment.get("download_url")
                    filename = attachment.get("filename", "Unnamed File")
                    mimetype = attachment.get("mimetype", "")
                    
                    if download_url:
                        icon = "📄"  # Default icon
                        if mimetype.startswith("image/"):
                            icon = "🖼️"
                        elif mimetype.startswith("video/"):
                            icon = "🎥"
                            
                        links.append(
                            f'<a href="{download_url}" target="_blank" '
                            f'class="attachment-link">{icon} {filename}</a>'
                        )
                value = "<br>".join(links)

            # Handle other data types
            elif isinstance(value, list):
                value = ', '.join(map(str, value))
            elif isinstance(value, dict):
                value = '<br>'.join(f"{k}: {v}" for k, v in value.items())
            elif value is None:
                value = ""
            else:
                value = str(value)

            # Add row to table
            html += f"<tr><td>{display_key}</td><td>{value}</td></tr>"

        html += "</tbody></table></div>"
        return html

    except Exception as e:
        frappe.log_error(f"Error generating HTML table: {str(e)}")
        return f"<p>Error generating table: {str(e)}</p>"
    
# bench --site al-khidmat.com execute akf_projects.akf_projects.doctype.project_survey_forms.project_survey_forms.fetch_api_data