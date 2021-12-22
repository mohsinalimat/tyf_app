from __future__ import unicode_literals
from __future__ import division
import frappe
from frappe import _

def validate_jv(doc, method=None):
    bl_data = []
    for d in doc.get("accounts"):
        if d.budget_line_child:
            docstatus = frappe.db.get_value('Budget Line Child', {'name': d.budget_line_child}, ['docstatus'])
            if docstatus == 0:
                bl_data.append({
                    "idx": d.idx,
                    "bl_name": d.budget_line_child
                })
    if bl_data:
        msg = ''
        for bl in bl_data:
            msg += _('Row #{0}: The Budget Line "{1}" is not submited yet.').format(
                bl['idx'], frappe.bold(bl['bl_name']))
            msg += "<br><br>"
            
        frappe.throw(msg, title=_("Budget Lines Error"))