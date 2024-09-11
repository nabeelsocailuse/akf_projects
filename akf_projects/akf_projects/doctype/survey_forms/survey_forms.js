// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on('Survey Forms', {
	// refresh: function(frm) {

	// }
	onload: function(frm) {
		// fetchAndSaveAPIData(frm)
        if (frm.doc.html_content) {
			console.log('///////////////////////////////////////');
			console.log(frm.doc.html_content);
			
            frm.set_df_property('forms_data', 'options', frm.doc.html_content);
            frm.save();
        }
    }
});

