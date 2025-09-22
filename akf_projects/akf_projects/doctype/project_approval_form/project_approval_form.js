// // Mubashir Bashir 19-04-2025

frappe.ui.form.on("Project Approval Form", {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.docstatus == 1) {
            frappe.db.get_list("ToDo", {
                filters: {
                    reference_type: frm.doctype,
                    reference_name: frm.doc.name,
                    allocated_to: frappe.session.user
                },
                fields: ["name"]
            }).then(r => {
                if (r.length > 0 && (frappe.user.has_role("Program Manager P&D") || frappe.user.has_role("Administrator"))) {
                    let btn = frm.add_custom_button("Create Project", function() {
                        frappe.route_options = {
                            project_name: frm.doc.project_title,
                            custom_region: frm.doc.region,
                            custom_district: frm.doc.district,
                            custom_tehsil: frm.doc.tehsil,
                            custom_uc: frm.doc.uc,
                            custom_latitude: frm.doc.latitude,
                            custom_longitude: frm.doc.longitude,
                            estimated_costing: frm.doc.estimated_project_budget,
                            custom_project_approval_form: frm.doc.name,
                            project_type: frm.doc.project_type,
                            fund_class: frm.doc.fund_class,
                        };
                        frappe.set_route("Form", "Project", "new-project");
                    });
                    btn.addClass("btn-primary");
                }
            });
        }

        empty_fields(frm);
        set_filters(frm);
        block_fields(frm);
        set_fund_class_permissions(frm);
        render_state_table(frm);
    },
    onload: function(frm) {
        empty_fields(frm);
		set_filters(frm);
		set_fund_class_permissions(frm);
        render_state_table(frm);
    },
	region: function(frm) {
        frm.set_value("district", "");
        frm.set_value("tehsil", "");
        set_filters(frm);
    },
    district: function(frm) {
        frm.set_value("tehsil", "");
        set_filters(frm);
    }	
});


function empty_fields(frm) {
    if (frm.is_new()) {
        frm.set_value('next_approver_id', '');
        frm.set_value('next_approver_name', '');
        frm.set_value('custom_state_data', '');
        frm.set_value('custom_state_html', '');

        frm.set_df_property("custom_state_html", "hidden", 1);
    }
    else {
        frm.set_df_property("custom_state_html", "hidden", 0); 
    }
}

function set_filters(frm) {
    // Filter District by Region
    frm.set_query("district", function() {
        return {
            filters: {
                region: frm.doc.region
            }
        };
    });

    // Filter Tehsil by Region + District
    frm.set_query("tehsil", function() {
        return {
            filters: {
                district: frm.doc.district
            }
        };
    });
}

function set_fund_class_permissions(frm) {
    console.log("checking fund class permissions");
    console.log(frappe.user.roles);
    
    
    if (frappe.user.has_role("Fund Class Officer")) {
        console.log("fund class officer - making fund class editable and required");
        
        frm.set_df_property("fund_class", "reqd", 1);
        frm.set_df_property("fund_class", "read_only", 0);
    } else {
        frm.set_df_property("fund_class", "reqd", 0);
        frm.set_df_property("fund_class", "read_only", 1);
    }
}

function block_fields(frm) {
    // states where Program Manager should be able to edit
    const editable_states = [
        "Draft",
        "Returned by Chairman",
        "Returned by Director Program",
        "Returned by CEO"
    ];

    if (editable_states.includes(frm.doc.workflow_state) 
        && frappe.user_roles.includes("Program Manager") || frappe.user_roles.includes("Administrator")) {
        console.log("making fields editable for Program Manager");
            

        // make all fields editable
        Object.keys(frm.fields_dict).forEach(f => {
            frm.set_df_property(f, "read_only", 0);
        });

    } else {
        // lock all fields except workflow_state
        Object.keys(frm.fields_dict).forEach(f => {
            if (f !== "workflow_state" && f !== "fund_class") {
                frm.set_df_property(f, "read_only", 1);
            }
        });
    }
}

function render_state_table(frm) {
    if (!frm.doc.custom_state_data) return;

    let rows = "";
    let data_list = [];
    try {
        data_list = JSON.parse(frm.doc.custom_state_data);
    } catch(e) {
        console.log("Invalid JSON in custom_state_data");
        return;
    }

    let idx = 1;
    data_list.forEach(data => {
        let dt = frappe.datetime.str_to_user(data.datetime);
        let next_info = "";

        if (data.next_user || data.next_role) {
            let user_name = data.next_user || "";
            let role = data.next_role || "";
            next_info = `${frappe.utils.escape_html(user_name)} (${frappe.utils.escape_html(role)})`;
        }

        rows += `
            <tr>
                <th scope="row">${idx}</th>
                <td>${frappe.utils.escape_html(data.employee_name || "")}</td>
                <td>${frappe.utils.escape_html(data.current_state || "")}</td>
                <td>${dt}</td>
                <td>${next_info}</td>
            </tr>`;
        idx++;
    });

    let html = `
    <table class="table table-bordered table-sm">
        <thead class="thead-dark">
            <tr>
                <th>#</th>
                <th>Employee Name</th>
                <th>Current State</th>
                <th>DateTime</th>
                <th>Next State</th>
            </tr>
        </thead>
        <tbody>${rows}</tbody>
    </table>`;

    frm.set_df_property("custom_state_html", "options", html);
}


