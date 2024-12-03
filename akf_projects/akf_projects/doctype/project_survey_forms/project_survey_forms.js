// Developer Mubashir Bashir

frappe.ui.form.on("Project Survey Forms", {
	// refresh: function(frm) {

	// }
	onload: function(frm) {
        if (frm.doc.html_content) {			
            frm.set_df_property('forms_data', 'options', frm.doc.html_content);
            frm.save();
        }
    }
});