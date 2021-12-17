frappe.ui.form.on("Journal Entry", {

    onload_post_render: function (frm) {
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
    },

	get_bl_account: (frm, cdt,cdn) => {
        let row = locals[cdt][cdn];
        frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_bl_account', {
            'bl_name': row.budget_line_child
          }).then(r => {
              frappe.model.set_value(cdt, cdn, "account", r);
          });
    },
});

frappe.ui.form.on("Journal Entry Account", {

	project: (frm, cdt, cdn) => {
		let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "budget_line_child", undefined);
		frappe.model.set_value(cdt, cdn, "account", undefined);
		if(!row.project){
			frappe.model.set_value(cdt, cdn, "cost_center", undefined);
		}
		cur_frm.refresh();
	},

	budget_line_child: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        if (!row.budget_line_child) {
            frappe.model.set_value(cdt, cdn, "account", undefined);
        } else {
            frm.events.get_bl_account(frm, cdt, cdn);
        }
    },
});