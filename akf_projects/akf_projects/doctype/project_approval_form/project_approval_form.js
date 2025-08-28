// // Mubashir Bashir 19-04-2025

frappe.ui.form.on("Project Approval Form", {
    refresh: function(frm) {
        if (!frm.is_new() && frm.doc.docstatus == 1 && (frappe.user.has_role("Program Manager P&D") || frappe.user.has_role("Administrator"))) {
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
        /////////////////////////////
        // frm.trigger("showWorkFlowState");
		set_filters(frm);
		set_fund_class_permissions(frm);
    },
    onload: function(frm) {
        if (frm.is_new()) {
            frm.set_value('next_approver_id', '');
            frm.set_value('next_approver_name', '');
            frm.set_value('custom_state_data', '');
            frm.set_value('custom_state_html', '');
        }
		set_filters(frm);
		set_fund_class_permissions(frm);
    },
	region: function(frm) {
        // clearing dependent fields
        frm.set_value("district", "");
        frm.set_value("tehsil", "");
        set_filters(frm);
    },
    district: function(frm) {
        // clearing tehsil when district changes
        frm.set_value("tehsil", "");
        set_filters(frm);
    },

    showWorkFlowState: function(frm){
		if(frm.doc.custom_state_data==undefined) {
			frm.set_df_property('custom_state_html', 'options', '<p></p>')
		}else{
			const stateObj = JSON.parse(frm.doc.custom_state_data)
			
			const desiredOrder = [
				"Requested by Program Manager",
				"Recommended by Chairman",
				"Rejected by Chairman",
				"Returned by Chairman",
				"Recommended by Director Program",
				"Rejected by Director Program",
				"Returned by Director Program",
				"Recommended by General Manager P&D",
				"Rejected by General Manager P&D",
				"Returned by General Manager P&D",
				"Recommended by Director P&D",
				"Rejected by Director P&D",
				"Returned by Director P&D",
				"Recommended by Chairman P&D",
				"Returned by Chairman P&D",
				"Recommended to CEO",
				"Approved by Chief Executive Officer",
				"Returned by Chief Executive Officer",
			];

			const orderedStates = desiredOrder
				.filter(state => stateObj.hasOwnProperty(state)) 
				.map(state => ({ key: state, ...stateObj[state] })); 
			
			let rows = ``;
			let idx = 1
			for (const data of orderedStates) {
				const dt = moment(data.modified_on).format("DD-MM-YYYY hh:mm:ss a");

				rows += `
				<tr>
					<th scope="row">${idx}</th>	
					<td scope="row">${data.current_state}</td>
					<td scope="row">${data.current_user}</td>
					<td scope="row">${data.department}</td>
					<td class="">${dt}</td>
				</tr>`;
				idx += 1;
			}
			let _html_ = `
			<table class="table">
				<thead class="thead-dark">
					<tr>
					<th scope="col">#</th>
					<th class="text-left" scope="col">Approval State</th>
					<th class="text-left" scope="col">User</th>
					<th class="text-left" scope="col">Department</th>
					<th scope="col">DateTime</th>
					</tr>
				</thead>
				<tbody>
					${rows}
				</tbody>
			</table>`;
			frm.set_df_property('custom_state_html', 'options', _html_)
		}
	}

	
});


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
    if (frappe.user.has_role("Fund Class Officer")) {
        frm.set_df_property("fund_class", "reqd", 1);
        frm.set_df_property("fund_class", "read_only", 0);
    } else {
        frm.set_df_property("fund_class", "reqd", 0);
        frm.set_df_property("fund_class", "read_only", 1);
    }
}