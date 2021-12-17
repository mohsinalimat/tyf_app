frappe.ui.form.on('Material Request', {
    // setup: function(frm) {
        
    // },
    onload: function(frm) {
        frm.events.set_filters(frm);
	},


    set_filters: (frm) => {
        console.log("yesss set_filters");
		frm.fields_dict['items'].grid.get_field('budget_line_child').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return {   
				filters:[
					['project_code', '=', child["project"]],
                    ['docstatus', '=', 1]
				]
			}
		}
        // if (frm.doc.project) {
        //     frappe.db.get_value('Project', {'name': frm.doc.project}, 'cost_center', (r) => {
        //         if (r && r.cost_center) {
        //             console.log("row.cost_center = " + r.cost_center);
        //             frm.fields_dict['items'].grid.get_field('cost_center').get_query = function(doc, cdt, cdn) {
        //                 var child = locals[cdt][cdn];
        //                 return {   
        //                     filters:[
        //                         ['name', '=', r.cost_center]
        //                     ]
        //                 }
        //             }
        //             // refresh_field('items');
        //         }
        //     });
        // }
        
    },
    // refresh: (frm) => {

    // },
    // project: function(doc, cdt, cdn) {
	// 	var item = frappe.get_doc(cdt, cdn);
	// 	if(item.project) {
	// 		$.each(this.frm.doc["items"] || [],
	// 			function(i, other_item) {
	// 				if(!other_item.project) {
	// 					other_item.project = item.project;
	// 					refresh_field("project", other_item.name, other_item.parentfield);
	// 				}
	// 			});
	// 	}
	// },

    project: (frm, cdt, cdn) => {
        var item = frappe.get_doc(cdt, cdn);
        if (!item.project){
            frm.set_value("cost_center", undefined);
        }

        
        // console.log("item = " + item.project);
        $.each(this.frm.doc["items"] || [],
        function(i, other_item) {
            other_item.cost_center = item.cost_center;
            other_item.project = item.project;
            refresh_field("cost_center", other_item.name, other_item.parentfield);
            refresh_field("project", other_item.name, other_item.parentfield);
        });
        // if (item.project || !item.project) {
        //     $.each(this.frm.doc["items"] || [],
        //     function(i, other_item) {
        //         other_item.cost_center = item.cost_center;
        //         refresh_field("cost_center", "project", other_item.name, other_item.parentfield);
        //         // if(!other_item.cost_center) {
        //         //     other_item.cost_center = item.cost_center;
        //         //     refresh_field("cost_center", other_item.name, other_item.parentfield);
        //         // }
        //     });
        // }
        //     } else {
        //         $.each(this.frm.doc["items"] || [],
        //             function(i, other_item) {
        //                 if(!other_item.cost_center && !other_item.project) {
        //                     other_item.cost_center = item.cost_center;
        //                     other_item.project = item.project;
        //                     refresh_field("cost_center", other_item.name, other_item.parentfield);
        //                 }
        //             });
        //     }
		// } 
        // refresh_field('items');
        // if (frm.doc.project) {
        //     frm.events.set_cost_center(frm, cdt, cdn);
        //     // frappe.db.get_value('Project', {'name': frm.doc.project}, 'cost_center', (r) => {
        //     //     if (r && r.cost_center) {
        //     //         console.log("row.cost_center = " + r.cost_center);
                    
        //     //         // frm.fields_dict['items'].grid.get_field('cost_center').get_query = function(doc, cdt, cdn) {
        //     //         //     var child = locals[cdt][cdn];
        //     //         //     return {   
        //     //         //         filters:[
        //     //         //             ['name', '=', r.cost_center]
        //     //         //         ]
        //     //         //     }
        //     //         // }
        //     //         frm.set_query("cost_center", "items", () => {
        //     //             return {
        //     //                 filters: {
        //     //                     'name': r.cost_center
        //     //                 }
        //     //             };
        //     //         });
        //     //         // refresh_field('items');
        //     //     }
        //     // });
        // }
    },

    // set_cost_center: (frm, cdt, cdn) => {
    //     // let row = locals[cdt][cdn];
        
    //     frappe.db.get_value('Project', {'name': frm.doc.project}, 'cost_center', (r) => {
    //         if (r && r.cost_center) {
    //             console.log("r.cost_center = " + r.cost_center);
    //             frappe.model.set_value(cdt, cdn, "cost_center", r.cost_center);
    //             // console.log("r.cost_center = " + r.cost_center);
    //             // frm.fields_dict['items'].grid.get_field('cost_center').get_query = function(doc, cdt, cdn) {
    //             //     var child = locals[cdt][cdn];
    //             //     return {   
    //             //         filters:[
    //             //             ['name', '=', r.cost_center]
    //             //         ]
    //             //     }
    //             // }
    //             // refresh_field('items');
    //         }
    //     });
    // },

    get_bl_account: (frm, cdt,cdn) => {
        let row = locals[cdt][cdn];
        frappe.xcall('tyf_app.tyf_app.doctype.budget_line.budget_line.get_bl_account', {
            'bl_name': row.budget_line_child
          }).then(r => {
              console.log("r = " + r);
              frappe.model.set_value(cdt, cdn, "expense_account", r);
          });
    },

});

frappe.ui.form.on("Material Request Item", {
    
    project: (frm, cdt, cdn) => {
        let row = locals[cdt][cdn];
        if (!row.project) {
            frappe.model.set_value(cdt, cdn, "cost_center", undefined);
            frappe.model.set_value(cdt, cdn, "budget_line_child", undefined);
            frappe.model.set_value(cdt, cdn, "expense_account", undefined);

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