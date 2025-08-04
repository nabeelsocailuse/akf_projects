// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt
frappe.ui.form.on("Project", {
	setup(frm) {
		frm.make_methods = {
			'Timesheet': () => {
				open_form(frm, "Timesheet", "Timesheet Detail", "time_logs");
			},
			'Purchase Order': () => {
				open_form(frm, "Purchase Order", "Purchase Order Item", "items");
			},
			'Purchase Receipt': () => {
				open_form(frm, "Purchase Receipt", "Purchase Receipt Item", "items");
			},
			'Purchase Invoice': () => {
				open_form(frm, "Purchase Invoice", "Purchase Invoice Item", "items");
			},
		};
	},
	onload_post_render: function (frm) {
		// loadFundsDashboard(frm);
	},
	onload: function (frm) {
		setTimeout(() => toggle_risk_buttons(frm), 100); // Mubashir Bashir 22-04-2025

		const so = frm.get_docfield("sales_order");
		so.get_route_options_for_new_doc = () => {
			if (frm.is_new()) return {};
			return {
				"customer": frm.doc.customer,
				"project_name": frm.doc.name
			};
		};

		frm.set_query('customer', 'erpnext.controllers.queries.customer_query');

		frm.set_query("user", "users", function () {
			return {
				query: "erpnext.projects.doctype.project.project.get_users_for_project"
			};
		});

		frm.set_query("department", function (doc) {
			return {
				filters: {
					"company": doc.company,
				}
			};
		});

		// sales order
		frm.set_query('sales_order', function () {
			var filters = {
				'project': ["in", frm.doc.__islocal ? [""] : [frm.doc.name, ""]]
			};

			if (frm.doc.customer) {
				filters["customer"] = frm.doc.customer;
			}

			return {
				filters: filters
			};
		});

		frm.set_query('custom_survey_id', function(){		// Mubashir 4-12-24 
			return {
				filters: {
					approval_status: 'Approved By Head Office'
				}
			};
		});

	},

	refresh: function (frm) {

		if (frm.doc.__islocal) {
			frm.web_link && frm.web_link.remove();
		} else {
			frm.add_web_link("/projects?project=" + encodeURIComponent(frm.doc.name));

			frm.trigger('show_dashboard');
		}
		frm.trigger("set_custom_buttons");

		loadFundsDashboard(frm);
		loadOpenStreetMap();
		loadDonorsDashboard(frm);
		loadRisksConnection(frm); //  Mubashir Bashir 17-01-2025
		loadTaskStatsSection(frm); //  Mubashir Bashir 17-05-2025
		setTimeout(() => toggle_risk_buttons(frm), 100); // Mubashir Bashir 22-04-2025

		//  Mubashir Bashir 17-01-2025 Start
		// Set filter for task field in Risk Register Child table
        // frm.set_query("task", "custom_risk_register", function(doc, cdt, cdn) {
        //     return {
        //         filters: {
        //             "project": doc.name
        //         }
        //     };
        // });
		//  Mubashir Bashir 17-01-2025 End
	},

	set_custom_buttons: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Duplicate Project with Tasks'), () => {
				frm.events.create_duplicate(frm);
			}, __("Actions"));

			frm.add_custom_button(__('Update Total Purchase Cost'), () => {
				frm.events.update_total_purchase_cost(frm);
			}, __("Actions"));

			frm.trigger("set_project_status_button");
			
			frm.add_custom_button(__('Send Project Progress Report'), () => {
				frm.events.send_project_progress_report(frm);
			}, __("Actions"));
			
			frm.add_custom_button(__('Send Project Completion Report'), () => {
				frm.events.send_project_completion_report(frm);
			}, __("Actions"));

			frm.add_custom_button(__('Performance Report'), () => {
				show_performance_report(frm);
			}, __("Actions"));


			if (frappe.model.can_read("Task")) {
				frm.add_custom_button(__("Gantt Chart"), function () {
					frappe.route_options = {
						"project": frm.doc.name
					};
					frappe.set_route("List", "Task", "Gantt");
				}, __("View"));

				frm.add_custom_button(__("Kanban Board"), () => {
					frappe.call('erpnext.projects.doctype.project.project.create_kanban_board_if_not_exists', {
						project: frm.doc.name
					}).then(() => {
						frappe.set_route('List', 'Task', 'Kanban', frm.doc.project_name);
					});
				}, __("View"));
			}
		}


	},

	update_total_purchase_cost: function (frm) {
		frappe.call({
			method: "erpnext.projects.doctype.project.project.recalculate_project_total_purchase_cost",
			args: { project: frm.doc.name },
			freeze: true,
			freeze_message: __('Recalculating Purchase Cost against this Project...'),
			callback: function (r) {
				if (r && !r.exc) {
					frappe.msgprint(__('Total Purchase Cost has been updated'));
					frm.refresh();
				}
			}

		});
	},

	send_project_completion_report: function (frm) {
		frappe.call({
			method: "akf_projects.customizations.overrides.project.project_override.send_project_completion_report",
			args: { doc: frm.doc },
			freeze: true,
			freeze_message: __('Sending email to project donors...'),
			callback: function (r) {
				if (r && !r.exc) {
					frappe.msgprint(__('Email sent successfully to project donors.'));
					frm.refresh();
				} else {
					frappe.msgprint(__('An error occurred while sending the email.'));
				}
			}
		});
	},

	send_project_progress_report: function (frm) {
		frappe.call({
			method: "akf_projects.customizations.overrides.project.project_override.send_project_progress_report",
			args: { doc: frm.doc },
			freeze: true,
			freeze_message: __('Sending email to project donors...'),
			callback: function (r) {
				if (r && !r.exc) {
					frappe.msgprint(__('Email sent successfully to project donors.'));
					frm.refresh();
				} else {
					frappe.msgprint(__('An error occurred while sending the email.'));
				}
			}
		});
	},
	

	set_project_status_button: function (frm) {
		frm.add_custom_button(__('Set Project Status'), () => {
			let d = new frappe.ui.Dialog({
				"title": __("Set Project Status"),
				"fields": [
					{
						"fieldname": "status",
						"fieldtype": "Select",
						"label": "Status",
						"reqd": 1,
						"options": "Completed\nCancelled",
					},
				],
				primary_action: function () {
					frm.events.set_status(frm, d.get_values().status);
					d.hide();
				},
				primary_action_label: __("Set Project Status")
			}).show();
		}, __("Actions"));
	},

	create_duplicate: function (frm) {	// Mubashir
		return new Promise(resolve => {
			frappe.prompt('New Project Name', (data) => {
				frappe.xcall('akf_projects.customizations.overrides.project.project_override.create_duplicate_project', {
					prev_doc: frm.doc,
					project_name: data.value
				}).then((new_project_name) => {
					frappe.set_route('Form', "Project", new_project_name);
					frappe.show_alert(__("Duplicate project has been created"));
				});
				resolve();
			});
		});
	},
	
	set_status: function (frm, status) {
		frappe.confirm(__('Set Project and all Tasks to status {0}?', [status.bold()]), () => {
			frappe.xcall('erpnext.projects.doctype.project.project.set_project_status',
				{ project: frm.doc.name, status: status }).then(() => {
					frm.reload_doc();
				});
		});
	},

});

function open_form(frm, doctype, child_doctype, parentfield) {
	frappe.model.with_doctype(doctype, () => {
		let new_doc = frappe.model.get_new_doc(doctype);

		// add a new row and set the project
		let new_child_doc = frappe.model.get_new_doc(child_doctype);
		new_child_doc.project = frm.doc.name;
		new_child_doc.parent = new_doc.name;
		new_child_doc.parentfield = parentfield;
		new_child_doc.parenttype = doctype;
		new_doc[parentfield] = [new_child_doc];
		new_doc.project = frm.doc.name;

		frappe.ui.form.make_quick_entry(doctype, null, null, new_doc);
	});

}

function loadFundsDashboard(frm) {
	if (!frm.is_new()) {
		frappe.call({
			"method": "akf_projects.customizations.overrides.project.financial_stats.get_transactions",
			// "method": "akf_projects.akf_projects.doctype.project.financial_stats.get_funds_detail",
			"args": {
				filters:{"project": frm.doc.name,}
				// "total_fund_allocated": frm.doc.total_fund_allocated
			},
			callback: function (r) {
				const data = r.message;
				frm.dashboard.refresh();
				
				frm.dashboard.add_indicator(__('Total Allocation: {0}',
					[format_currency(data.total_allocation)]), 'green');
				
				frm.dashboard.add_indicator(__('Pledge Amount: {0}',
					[format_currency(data.total_pledge)]),
					'yellow');
				frm.dashboard.add_indicator(__('Transfered Funds: {0}',
					[format_currency(data.transfered_funds)]),
					'grey');
				frm.dashboard.add_indicator(__('Received Funds: {0}',
					[format_currency(data.received_funds)]),
					'green');
				frm.dashboard.add_indicator(__('Consumed Funds: {0}',
					[format_currency(data.total_purchase)]),
					'red');
				
				frm.dashboard.add_indicator(__('Remaining Amount: {0}',
					[format_currency(data.remaining_amount)]),
					'blue');
			}
		});
	}
}

function loadOpenStreetMap() {
	openStreetMapFunc(1);
}

function openStreetMapFunc(position) {
	const latitude = cur_frm.doc.custom_latitude;
	const longitude = cur_frm.doc.custom_longitude;
	if ((latitude != "" && latitude != undefined) && longitude != "" && longitude != undefined) {
		var curLocation = [latitude, longitude];
		$("#map_id").empty();
		$("#var_map").html(`<div id="map_id" style="height:400px"></div>`);
		setTimeout(() => {
			map = window.L.map('map_id').setView(curLocation, 16);
			const tiles = window.L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
				maxZoom: 19,
				attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
			}).addTo(map);
			const marker = window.L.marker(curLocation).addTo(map);
			map.panTo(new window.L.LatLng(latitude, longitude));
		}, 500);
	}
}

function loadDonorsDashboard(frm) {
	if (frm.is_new()) { return }
	frm.set_df_property('custom_donors_table', "options",
		`<div class="row">
			<div class="col-xs-12">
				<p>Not Found! </p>
			</div>
		</div>`
	);

	frappe.call({
		method: "akf_projects.customizations.overrides.project.donors_detail.get_donors",
		args: {
			filters: {
				"project_id": frm.doc.name,
				"docstatus": 1
			}
		},
		callback: function (r) {
			let data = r.message;
			let rows = ``;
			let idx = 1
			data.forEach(element => {
				let log = moment(element.log).format("DD-MM-YYYY hh:mm:ss a")
				rows += `
					<tr>
						<td>${idx}</td>
						<th scope="row"><a href="/app/donor/${element.donor_id}">${element.donor_id}</a></th>
						<td class="">${element.donor_name}</td>
						<td><a href="/app/donation/${element.donation}">${element.donation}</a></td>
						<td class="">${element.status}</td>
					</tr>`;
				idx += 1;
			});
			let _html_ = `
				<table class="table">
					<thead class="thead-dark">
						<tr>
						<th>#</th>
						<th class="" scope="col">Donor ID</th>
						<th class="" scope="col">Donor Name</th>
						<th scope="col">Donation ID</th>
						<th scope="col">Status</th>
						</tr>
					</thead>
					<tbody>
						${rows}
					</tbody>
				</table>`;
			frm.set_df_property("custom_donors_table", "options", _html_);
		}
	})
}

// Mubashir Bashir 17-01-2025 Start
function loadRisksConnection(frm) {
    if (frm.is_new()) return;

	$('.custom-risks-section').remove();
    
    frappe.call({
        method: 'akf_projects.customizations.overrides.project.project_override.get_project_risks',
        args: {
            project: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.length) {
                let risks_html = `
                    <div class="form-dashboard-section custom-risks-section">
                        <div class="section-head" data-toggle="collapse" data-target="#risks-section" 
                            style="cursor: pointer;">
                            Risks
                            <span class="collapse-indicator mb-1">
                                <i class="fa fa-chevron-up"></i>
                            </span>
                        </div>
                        <div id="risks-section" class="collapse">
                            <div class="row">`;
                
                r.message.forEach(risk => {
                    let ratingClass = getRatingClass(risk.rating);
                    risks_html += `
                        <div class="col-sm-6 mb-2">
                            <div style="background: var(--card-bg); border-radius: 8px; padding: 12px 15px; border: 1px solid var(--border-color);">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                                    <a href="/app/risk-register/${risk.risk}" class="text-primary" style="font-size: 14px; font-weight: 500;">
                                        ${risk.risk}
                                    </a>
                                    <span class="indicator-pill ${ratingClass}" style="padding: 4px 8px;">
                                        Rating: ${risk.rating}
                                    </span>
                                </div>
                                <div style="display: flex; justify-content: space-between; color: var(--text-muted); font-size: 13px;">
                                    <div>
                                        <i class="fa fa-exclamation-triangle" style="color: var(--yellow-500); margin-right: 4px;"></i>
                                        Severity: ${risk.severity}
                                    </div>
                                    <div>
                                        <i class="fa fa-chart-line" style="color: var(--blue-500); margin-right: 4px;"></i>
                                        Likelihood: ${risk.likelihood}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                risks_html += `
                            </div>
                        </div>
                    </div>`;
                
                $('.form-dashboard-section').last().after(risks_html);
                
                $('.custom-risks-section .section-head').on('click', function() {
                    $(this).find('.collapse-indicator i').toggleClass('fa-chevron-up fa-chevron-down');
                });
            }
        }
    });
}

function getRatingClass(rating) {
    rating = parseInt(rating) || 0;
    if (rating >= 75) return 'red';
    if (rating >= 50) return 'orange';
    if (rating >= 25) return 'yellow';
    return 'green';
}

function loadTaskStatsSection(frm) {
    if (frm.is_new()) return;

    $('.custom-task-stats-section').remove();

    frappe.call({
        method: 'akf_projects.customizations.overrides.project.project_override.get_project_task_stats',
        args: {
            project: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                let stats = r.message;
                let completion = stats.total > 0 ? ((stats.completed / stats.total) * 100).toFixed(1) : 0;

                let html = `
                    <div class="form-dashboard-section custom-task-stats-section" style="margin-bottom: 16px;">
                        <div class="section-head" data-toggle="collapse" data-target="#task-stats-section" style="cursor: pointer; display: flex; align-items: center;">
                            <span style="font-weight: 600;">Task Overview</span>
                            <span class="collapse-indicator mb-1">
                                <i class="fa fa-chevron-up"></i>
                            </span>
                        </div>
                        <div id="task-stats-section" class="collapse show">
                            <div class="row" style="margin-top: 12px;">
                                ${renderStatCard("Total Tasks", stats.total, "fa-tasks", "#6c757d")}
                                ${renderStatCard("Open", stats.open, "fa-folder-open", "#007bff")}
                                ${renderStatCard("Working", stats.working, "fa-spinner", "#17a2b8")}
                                ${renderStatCard("Pending Review", stats.pending_review, "fa-hourglass-half", "#ffc107")}
                                ${renderStatCard("Completed", stats.completed, "fa-check-circle", "#28a745")}
                                ${renderStatCard("Overdue", stats.overdue, "fa-exclamation-circle", "#dc3545")}

                                <div class="col-sm-12 mt-3">
                                    <div style="background: var(--card-bg); padding: 16px; border-radius: 8px; border: 1px solid var(--border-color);">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <strong style="font-size: 14px;">Completion</strong>
                                            <span style="font-size: 14px;">${completion}%</span>
                                        </div>
                                        <div class="progress mt-2" style="height: 8px;">
                                            <div class="progress-bar bg-success" role="progressbar" style="width: ${completion}%"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;

                $('.form-dashboard-section').last().after(html);

                $('.custom-task-stats-section .section-head').on('click', function() {
                    $(this).find('.collapse-indicator i').toggleClass('fa-chevron-up fa-chevron-down');
                });
            }
        }
    });

    function renderStatCard(label, value, icon, color) {
        return `
            <div class="col-sm-4 mb-2">
                <div style="
                    background: var(--card-bg); 
                    border-radius: 8px; 
                    padding: 12px 15px; 
                    border: 1px solid var(--border-color);
                    display: flex;
                    align-items: center;
                    gap: 12px;
                ">
                    <i class="fa ${icon}" style="color: ${color}; font-size: 18px;"></i>
                    <div>
                        <div style="font-size: 13px; color: var(--text-muted);">${label}</div>
                        <div style="font-size: 16px; font-weight: 600;">${value}</div>
                    </div>
                </div>
            </div>
        `;
    }
}


function toggle_risk_buttons(frm) {
    const is_new = frm.is_new();

    const risk_table = frm.fields_dict['custom_risk_register'];
    if (risk_table && risk_table.grid) {

        const addBtn = risk_table.grid.fields_map['add_tasks'];
        const viewBtn = risk_table.grid.fields_map['view_tasks'];

        if (addBtn) addBtn.hidden = is_new;
        else console.warn('add_tasks button not found in child table');

        if (viewBtn) viewBtn.hidden = is_new;
        else console.warn('view_tasks button not found in child table');

        risk_table.refresh();
    }
}

frappe.ui.form.on('Risk Register Child', {
    severity: function (frm, cdt, cdn) {
        calculate_ratings(frm, cdt, cdn);
    },
    likelihood: function (frm, cdt, cdn) {
        calculate_ratings(frm, cdt, cdn);
    },
	add_tasks: function (frm, cdt, cdn) {
		redirect_to_task(frm, cdt, cdn);
	},
	view_tasks: function (frm, cdt, cdn) {
		redirect_to_task_list(frm, cdt, cdn);
	}
});

function calculate_ratings(frm, cdt, cdn) {
    let child = locals[cdt][cdn];
    if (child.severity && child.likelihood) {
        let rating = child.severity * child.likelihood;
        frappe.model.set_value(cdt, cdn, 'rating', rating);
    } else {
        frappe.model.set_value(cdt, cdn, 'rating', '');
    }
}

function redirect_to_task(frm, cdt, cdn) {
    let child = locals[cdt][cdn];

    if (!child.risk) {
        frappe.msgprint(__('Please fill in the Risk field before adding a task.'));
        return;
    }

    frappe.new_doc('Task', {
        project: frm.doc.name,
        custom_risk_id: child.risk
    });
}

function redirect_to_task_list(frm, cdt, cdn) {
	let child = locals[cdt][cdn];

	if (!child.risk) {
        frappe.msgprint(__('Please fill in the Risk field before adding a task.'));
        return;
    }

	frappe.set_route('List', 'Task', {
        project: frm.doc.name,
        custom_risk_id: child.risk
    });
}







// function show_performance_report(frm) {
//     frappe.call({
//         method: "akf_projects.customizations.overrides.project.project_override.get_project_performance_metrics",
//         args: {
//             project: frm.doc.name,
//             budget: frm.doc.estimated_costing
//         },
//         callback: function (r) {
//             if (r.message) {
//                 const data = r.message;

//                 let content_html = `
//                     <div style="font-family: 'Segoe UI', Roboto, sans-serif; font-size: 14px; color: #333;">
//                         <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 4px;">📊 Performance Summary</h3>

//                         <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
//                             <tr>
//                                 <td><b>Total Tasks:</b></td>
//                                 <td>${data.total_tasks}</td>
//                             </tr>
//                             <tr>
//                                 <td><b>Completed Tasks:</b></td>
//                                 <td>${data.completed_tasks}</td>
//                             </tr>
//                             <tr>
//                                 <td><b>Tasks Due Till Today:</b></td>
//                                 <td>${data.tasks_due_till_today}</td>
//                             </tr>
//                             <tr>
//                                 <td><b>Budget (D):</b></td>
//                                 <td>${format_currency(data.budget)}</td>
//                             </tr>
//                             <tr>
//                                 <td><b>Actual Cost (AC):</b></td>
//                                 <td>${format_currency(data.actual_cost)}</td>
//                             </tr>
//                             <tr>
//                                 <td><b>Earned Value (EV):</b></td>
//                                 <td>${format_currency(data.earned_value)}</td>
//                             </tr>
//                             <tr>
//                                 <td><b>Planned Value (PV):</b></td>
//                                 <td>${format_currency(data.planned_value)}</td>
//                             </tr>
//                             <tr style="color: ${data.cost_variance >= 0 ? 'green' : 'red'};">
//                                 <td><b>Cost Variance (CV):</b></td>
//                                 <td>${format_currency(data.cost_variance)} (${data.cost_variance >= 0 ? '🟢 Under budget' : '🔴 Over budget'})</td>
//                             </tr>
//                             <tr style="color: ${data.schedule_variance >= 0 ? 'green' : 'red'};">
//                                 <td><b>Schedule Variance (SV):</b></td>
//                                 <td>${format_currency(data.schedule_variance)} (${data.schedule_variance >= 0 ? '🟢 Ahead of schedule' : '🔴 Behind schedule'})</td>
//                             </tr>
//                         </table>
//                     </div>
//                 `;

//                 let d = new frappe.ui.Dialog({
//                     title: 'Project Performance Report',
//                     size: 'large',
//                     primary_action_label: 'Close',
//                     primary_action() {
//                         d.hide();
//                     }
//                 });

//                 d.$body.append(content_html);
//                 d.show();
//             }
//         }
//     });
// }

function show_performance_report(frm) {
    frappe.call({
        method: "akf_projects.customizations.overrides.project.project_override.get_project_performance_metrics",
        args: {
            project: frm.doc.name,
            budget: frm.doc.estimated_costing
        },
        callback: function (r) {
            if (r.message) {
                const data = r.message;
                const completion_ratio = data.total_tasks ? (data.completed_tasks / data.total_tasks) * 100 : 0;

                let content_html = `
                    <div style="font-family:'Segoe UI', Roboto, sans-serif; font-size:14px; color:#333;">
                        <h3 style="border-bottom: 1px solid #ccc; padding-bottom: 4px;">📊 Project Performance Summary</h3>

                        <div style="margin-top: 12px;">
                            <label><b>Task Completion:</b></label>
                            <div style="background:#eee; border-radius:6px; overflow:hidden; height:20px; margin-bottom:10px;">
                                <div style="width:${completion_ratio}%; background:linear-gradient(to right, #4caf50, #81c784); height:100%; text-align:center; color:white; font-size:12px;">
                                    ${completion_ratio.toFixed(1)}%
                                </div>
                            </div>

                            <table style="width:100%; border-collapse:collapse;">
                                <tr><td><b>Total Tasks:</b></td><td>${data.total_tasks}</td></tr>
                                <tr><td><b>Completed Tasks:</b></td><td>${data.completed_tasks}</td></tr>
                                <tr><td><b>Tasks Due Till Today:</b></td><td>${data.tasks_due_till_today}</td></tr>
                                <tr><td><b>Budget (D):</b></td><td>${format_currency(data.budget)}</td></tr>
                                <tr><td><b>Actual Cost (AC):</b></td><td>${format_currency(data.actual_cost)}</td></tr>
                                <tr><td><b>Earned Value (EV):</b></td><td>${format_currency(data.earned_value)}</td></tr>
                                <tr><td><b>Planned Value (PV):</b></td><td>${format_currency(data.planned_value)}</td></tr>
                                <tr style="color:${data.cost_variance >= 0 ? 'green' : 'red'};">
                                    <td><b>Cost Variance (CV):</b></td>
                                    <td>${format_currency(data.cost_variance)} (${data.cost_variance >= 0 ? '🟢 Under budget' : '🔴 Over budget'})</td>
                                </tr>
                                <tr style="color:${data.schedule_variance >= 0 ? 'green' : 'red'};">
                                    <td><b>Schedule Variance (SV):</b></td>
                                    <td>${format_currency(data.schedule_variance)} (${data.schedule_variance >= 0 ? '🟢 Ahead of schedule' : '🔴 Behind schedule'})</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                `;

                let d = new frappe.ui.Dialog({
                    title: 'Project Performance Report',
                    size: 'large',
                    primary_action_label: 'Close',
                    primary_action() {
                        d.hide();
                    }
                });

                d.$body.append(content_html);
                d.show();
            }
        }
    });
}
