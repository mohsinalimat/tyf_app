// Copyright (c) 2021, Tamdeen Youth Foundation and contributors
// For license information, please see license.txt

frappe.ui.form.on('Employee Payroll Details', {
	onload_post_render: function (frm) {
        frm.events.set_filters(frm);
    },

    set_filters: (frm) => {
        frm.fields_dict['project_share'].grid.get_field('project').get_query = function() {
			return {    
				filters:[
					['company', '=', frm.doc.company],
                    ['status', 'not in', 'Completed, Cancelled']
				]
			}
		};
		frm.fields_dict['project_share'].grid.get_field('budget_line').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return {    
				filters:[
					['project_code', '=', child["project"]],
					['docstatus', '=', 1]
				]
			}
		};
    },

	get_bl_account: (frm, cdt,cdn) => {
        let row = locals[cdt][cdn];
        frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_bl_account', {
            'bl_name': row.budget_line
          }).then(r => {
              frappe.model.set_value(cdt, cdn, "account", r);
          });
    },
});


frappe.ui.form.on("Project Share", {
    
    project: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "budget_line", undefined);
        frappe.model.set_value(cdt, cdn, "account", undefined);
		frappe.model.set_value(cdt, cdn, "share", 0);
        if (!row.project) {
            frappe.model.set_value(cdt, cdn, "cost_center", undefined);
        }
    },

    budget_line: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "share", 0);
        if (!row.budget_line) {
            frappe.model.set_value(cdt, cdn, "account", undefined);
        } else {
            frm.events.get_bl_account(frm, cdt, cdn);
        }
    },

});