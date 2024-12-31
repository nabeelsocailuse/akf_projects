// Developer Mubashir Bashir

frappe.ui.form.on("Project Survey Forms", {
	// refresh: function(frm) {

	// }
	onload: function(frm) {
        render_form_data(frm);
        frm.save();
    }
});

function render_form_data(frm){
    if (frm.doc.survey_form_json) {
        frappe.call({
            method: 'akf_projects.akf_projects.doctype.project_survey_forms.project_survey_forms.generate_html_table_for_record',
            args: {
                json_data: frm.doc.survey_form_json
            },
            callback: function(r) {
                if (r.message) {
                    frm.set_df_property('forms_data', 'options', r.message);
                    frm.refresh_field('forms_data');
                }
            }
        });
    }
}