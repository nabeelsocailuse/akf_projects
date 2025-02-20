// Copyright (c) 2025, Mubarrim Iqbal and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project Approval Form", {
    refresh: function(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button("Create Project", function() {
                frappe.call({
                    method: "frappe.client.insert",
                    args: {
                        doc: {
                            doctype: "Project",
                            project_name: frm.doc.project_title,
                            custom_region: frm.doc.region2,
                            custom_district: frm.doc.district2,
                            custom_tehsil: frm.doc.tehsil,
                            custom_uc: frm.doc.uc,
                            custom_latitude: frm.doc.latitude,
                            custom_longitude: frm.doc.longitude
                        }
                    },
                    callback: function(response) {
                        if (response && response.message) {
                            let project_id = response.message.name; 

                            frm.set_value("project_code", project_id);
                            frm.save().then(() => {
                                frappe.msgprint({
                                    title: __('Success'),
                                    indicator: 'green',
                                    message: __('Project Created: {0}', [project_id])
                                });
                            }); 
                        }
                    }
                });
            }).addClass("btn-primary");
        }
    }
});
