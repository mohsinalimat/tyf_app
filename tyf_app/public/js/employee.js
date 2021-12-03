frappe.ui.form.on("Employee", {
    refresh: function (frm) {
        frm.events.set_filters(frm)
    },

    project: (frm) => {
        frm.events.get_cost_center(frm);
    },

    department: (frm) => {
        frm.events.get_cost_center(frm);
    },

    get_cost_center: (frm) => {
        if (frm.doc.project){
            frappe.db.get_value('Project', frm.doc.project, 'cost_center', (values) => {
                frm.set_value("payroll_cost_center", values.cost_center);
            });
        } else if (frm.doc.department){
            frappe.db.get_value('Department', frm.doc.department, 'payroll_cost_center', (values) => {
                if (values.payroll_cost_center) {
                    frm.set_value("payroll_cost_center", values.payroll_cost_center);
                } else {
                    frappe.db.get_value('Company', frm.doc.company, 'cost_center', (values) => {
                        frm.set_value("payroll_cost_center", values.cost_center);
                    });
                }
            });
        } else {
            frappe.db.get_value('Company', frm.doc.company, 'cost_center', (values) => {
                frm.set_value("payroll_cost_center", values.cost_center);
            });
        }
    },

    set_filters: (frm) => {
        frm.set_query("budget_line", function () {
            let project_code = null;
            if (frm.doc.project){
                project_code = frm.doc.project
            }
			return {
				filters: {
					"project_code": project_code
				}
			};
		});
    }
});