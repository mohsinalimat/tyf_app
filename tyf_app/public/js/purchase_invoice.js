frappe.ui.form.on("Purchase Invoice", {
    onload_post_render: function (frm) {
        frm.events.set_filters(frm);
    },

    set_filters: (frm) => {
        frm.set_query("project", function() {
			return {
				filters: [
					['company', '=', frm.doc.company],
                    ['status', 'not in', 'Completed, Cancelled']
                ]
			};
        });

        frm.set_query("budget_line_child", function() {
			return {
				filters: [
					['project_code', '=', frm.doc.project],
                    ['docstatus', '=', 1]
                ]
			};
        });

        frm.fields_dict['items'].grid.get_field('budget_line_child').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return {
				filters:[
					['project_code', '=', child["project"]],
                    ['docstatus', '=', 1]
				]
			}
		}

        frm.fields_dict['items'].grid.get_field('project').get_query = function() {
			return {    
				filters:[
					['company', '=', frm.doc.company],
                    ['status', 'not in', 'Completed, Cancelled']
				]
			}
		};
    },

    project: (frm) => {
        frm.set_value("budget_line_child", undefined);
        // frm.set_value("account", undefined);
		// frm.set_value(cdt, cdn, "share", 0);
        if (!frm.doc.project) {
            frm.set_value("cost_center", undefined);
        }
    },

	get_bl_account: (frm, cdt,cdn) => {
        let row = locals[cdt][cdn];
        frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_bl_account', {
            'bl_name': row.budget_line_child
          }).then(r => {
              frappe.model.set_value(cdt, cdn, "expense_account", r);
          })
    }
});

frappe.ui.form.on("Purchase Invoice Item", {
    
    project: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, "budget_line_child", undefined);
        frappe.model.set_value(cdt, cdn, "expense_account", undefined);
        if (!row.project) {
            frappe.model.set_value(cdt, cdn, "cost_center", undefined);
        }
    },

    budget_line_child: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        if (!row.budget_line_child) {
            frappe.model.set_value(cdt, cdn, "expense_account", undefined);
        } else {
            frm.events.get_bl_account(frm, cdt, cdn);
        }
    },

});