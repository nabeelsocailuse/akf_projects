// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("erpnext.projects");

frappe.ui.form.on("Task", {
	setup: function (frm) {
		frm.make_methods = {
			'Timesheet': () => frappe.model.open_mapped_doc({
				method: 'erpnext.projects.doctype.task.task.make_timesheet',
				frm: frm
			})
		}
	},

	onload: function (frm) {
		
		frm.set_query("task", "depends_on", function () {
			let filters = {
				name: ["!=", frm.doc.name]
			};
			if (frm.doc.project) filters["project"] = frm.doc.project;
			return {
				filters: filters
			};
		})

		frm.set_query("parent_task", function () {
			let filters = {
				"is_group": 1,
				"name": ["!=", frm.doc.name]
			};
			if (frm.doc.project) filters["project"] = frm.doc.project;
			return {
				filters: filters
			}
		});
		// Mubashir Bashir 28-04-25 Start
		frm.set_query("custom_predecessor", function () {
			let filters = {
				"is_group": 0,
				"name": ["!=", frm.doc.name]
			};
			if (frm.doc.project) filters["project"] = frm.doc.project;
			return {
				filters: filters
			}
		});
		// Mubashir Bashir 28-04-25 End
	},

	is_group: function (frm) {
		frappe.call({
			method: "erpnext.projects.doctype.task.task.check_if_child_exists",
			args: {
				name: frm.doc.name
			},
			callback: function (r) {
				if (r.message.length > 0) {
					let message = __('Cannot convert Task to non-group because the following child Tasks exist: {0}.',
						[r.message.join(", ")]
					);
					frappe.msgprint(message);
					frm.reload_doc();
				}
			}
		})
	},

	validate: function (frm) {
		frm.doc.project && frappe.model.remove_from_locals("Project",
			frm.doc.project);
	},

	refresh: function (frm) {	// Mubbashir
		frm.trigger("set_custom_buttons");
    },

    set_custom_buttons: function (frm) {	// Mubbashir
        if (!frm.is_new() && frm.doc.is_group) {
            frm.add_custom_button(__('Duplicate Task with Sub-Tasks'), () => {
                frm.events.create_duplicate(frm);
            }, __("Actions"));
        }
    },

    create_duplicate: function (frm) {	// Mubbashir
		return new Promise(resolve => {
			frappe.prompt('Subject', (data) => {
				frappe.xcall('akf_projects.customizations.overrides.project.task_override.create_duplicate_tasks',
					{
						prev_doc: frm.doc,
						subject: data.value
					}).then((new_task_name) => {
						frappe.set_route('Form', "Task", new_task_name);
						frappe.show_alert(__("Duplicate tasks has been created"));
					});
				resolve();
			});
		});
	},
});


