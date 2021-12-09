frappe.ui.form.on("Payroll Entry", {
    refresh: function (frm) {
        frm.fields_dict['employees'].grid.get_field('budget_line').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return {    
				filters:[
					['project_code', '=', frm.doc.project],
                    ['docstatus', '=', 1]
				]
			}
		}
    },

    project: (frm) => {
        if (!frm.doc.project){
            if (frm.doc.company){
                frappe.db.get_value("Company", {"name": frm.doc.company}, "cost_center", (r) => {
                    frm.set_value('cost_center', r.cost_center);  
                });
            } else {
                frm.set_value('cost_center', undefined);
            }
        } else {
            frappe.db.get_value("Project", {"name": frm.doc.project}, "cost_center", (r) => {
                frm.set_value('cost_center', r.cost_center);
                cur_frm.refresh();
            });         
        }
        cur_frm.refresh();
    },
});