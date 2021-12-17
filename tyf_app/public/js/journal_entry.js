frappe.ui.form.on("Journal Entry", {

    onload: function (frm) {
        frm.events.set_filters(frm);
    },

    set_filters: (frm) => {
        frm.fields_dict['accounts'].grid.get_field('budget_line_child').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return {    
				filters:[
					['project_code', '=', child["project"]]
				]
			}
		}
    }
});

frappe.ui.form.on("Journal Entry Account", {

	project: (frm, cdt, cdn) => {
		let row = frm.selected_doc;
		if(!row.project){
			frappe.model.set_value(cdt, cdn, "budget_line_child", undefined);
			frappe.model.set_value(cdt, cdn, "cost_center", undefined);
			frappe.model.set_value(cdt, cdn, "account", undefined);
			cur_frm.refresh();
		} 
	}
});