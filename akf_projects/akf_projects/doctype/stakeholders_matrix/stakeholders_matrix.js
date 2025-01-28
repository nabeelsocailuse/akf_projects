// Developer Mubashir Bashir

frappe.ui.form.on('Stakeholders Matrix', {
    onload: function(frm) {
        populate_internal_stakeholders(frm);
    },
    project_id: function(frm) {        
        populate_internal_stakeholders(frm);
    }
});

function populate_internal_stakeholders(frm) {
    if (!frm.doc.project_id) return;

    // Clear the existing rows in the child table
    frm.clear_table('internal_stakeholder');

    // Fetch the users from the 'Project User' child table in the selected Project
    frappe.db.get_doc('Project', frm.doc.project_id).then(project => {
        let user_ids = project.users.map(row => row.user);

        if (user_ids.length === 0) return;

        // Fetch Employees whose user_id matches the users in the Project
        return frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Employee',
                filters: {
                    user_id: ['in', user_ids],
                    status: 'Active'
                },
                fields: ['name', 'employee_name', 'designation', 'user_id']
            }
        });
    }).then(r => {
        if (!r.message) return;

        // Create an array of promises for all task fetching operations
        const promises = r.message.map(employee => {
            return new Promise((resolve) => {
                frappe.call({
                    method: 'frappe.client.get_list',
                    args: {
                        doctype: 'Task',
                        filters: {
                            _assign: ['like', `%${employee.user_id}%`],
                            project: frm.doc.project_id
                        },
                        fields: ['exp_start_date', 'exp_end_date']
                    },
                    callback: function(task_response) {
                        let tasks = task_response.message || [];
                        let no_of_tasks_assigned = tasks.length;
                        let first_task_start_date = null;
                        let last_task_end_date = null;

                        // Calculate start and end dates
                        if (tasks.length > 0) {
                            first_task_start_date = tasks.reduce((min, task) => 
                                task.exp_start_date < min ? task.exp_start_date : min, 
                                tasks[0].exp_start_date
                            );
                            last_task_end_date = tasks.reduce((max, task) => 
                                task.exp_end_date > max ? task.exp_end_date : max, 
                                tasks[0].exp_end_date
                            );
                        }

                        // Add a row to the child table
                        let child = frm.add_child('internal_stakeholder');
                        child.stakeholder = employee.name;
                        child.name1 = employee.employee_name;
                        child.designation = employee.designation;
                        child.no_of_tasks_assigned = no_of_tasks_assigned;
                        child.start_date = first_task_start_date;
                        child.end_date = last_task_end_date;

                        resolve();
                    }
                });
            });
        });

        // Wait for all task fetching operations to complete
        Promise.all(promises).then(() => {
            frm.refresh_field('internal_stakeholder');
            frm.save();
        });
    }).catch(err => {
        console.error("Error in populate_internal_stakeholders:", err);
    });
}