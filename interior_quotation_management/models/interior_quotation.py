from urllib import request

from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import base64


class InteriorQuotation(models.Model):
    _name = 'interior.quotation'
    _description = 'Interior Quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    # -------------------------------------------------------------------------
    # BASIC INFO
    # -------------------------------------------------------------------------
    name = fields.Char(
        string='Quotation Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: 'New'
    )
    quotation_title = fields.Char(default="Approximate Quotation")
    project_name = fields.Char(string='Project Name', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    address = fields.Char(string='Site Location')

    # -------------------------------------------------------------------------
    # COMPANY & USER
    # -------------------------------------------------------------------------
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user
    )

    # -------------------------------------------------------------------------
    # DATES
    # -------------------------------------------------------------------------
    date = fields.Date(string='Quotation Date', default=fields.Date.context_today)
    validity_days = fields.Integer(string='Validity (Days)', default=30)
    date_deadline = fields.Date(string='Valid Until', compute='_compute_deadline', store=True)

    # -------------------------------------------------------------------------
    # STATE MANAGEMENT
    # -------------------------------------------------------------------------
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='draft', tracking=True)

    # -------------------------------------------------------------------------
    # LINES & TOTALS
    # -------------------------------------------------------------------------
    material_line_ids = fields.One2many(
        'interior.quotation.material',
        'quotation_id',
        string='Material Details'
    )

    material_total = fields.Monetary(
        string='Material Total',
        currency_field='currency_id',
        compute='_compute_material_total',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # -------------------------------------------------------------------------
    # NOTES & REVISIONS
    # -------------------------------------------------------------------------
    note = fields.Html(
        string='Internal Notes',
        default=lambda self: """
            <p><strong>Materials</strong></p>
            <ul style="margin-left:15px;">
                <li>19mm Water Proof 710 Plywood</li>
                <li>Fevicol Hi-per Star</li>
                <li>Inner Mica 0.8mm</li>
                <li>Sleek Hydraulic Hinges (1st Quality)</li>
                <li>Handle Loft 200 / Cupboard 350</li>
                <li>Cupboard Outer Laminate</li>
                <li>Lock: Godrej or Dorset</li>
                <li>Sleek Telescopic Channel</li>
            </ul>
        """
    )

    revision = fields.Integer(string='Revision No.', default=0, tracking=True)
    previous_quotation_id = fields.Many2one('interior.quotation', string='Previous Revision')

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends('date', 'validity_days')
    def _compute_deadline(self):
        """Compute validity deadline"""
        for rec in self:
            rec.date_deadline = fields.Date.add(rec.date, days=rec.validity_days) if rec.date else False

    @api.depends('material_line_ids.amount')
    def _compute_material_total(self):
        """Sum total amount from material lines"""
        for rec in self:
            rec.material_total = sum(rec.material_line_ids.mapped('amount'))

    # -------------------------------------------------------------------------
    # ACTION METHODS
    # -------------------------------------------------------------------------
    import requests
    import base64

    def action_send(self):
        pass


    def action_approve(self):
        self.write({'state': 'approved'})
        return True

    def action_reject(self):
        self.write({'state': 'rejected'})
        return True

    def action_draft(self):
        self.write({'state': 'draft'})
        return True

    def action_duplicate_revision(self):
        """Create a new revision version of this quotation, including material lines"""
        self.ensure_one()  # Ensure only one record is processed

        # Create a copy of the quotation
        new_rev = self.copy({
            'name': 'New',  # You can update this later to auto-increment name if needed
            'previous_quotation_id': self.id,
            'revision': self.revision + 1,
            'state': 'draft',
        })

        # Duplicate all material lines
        if hasattr(self, 'material_line_ids'):
            new_lines = []
            for line in self.material_line_ids:
                line_vals = line.copy_data()[0]  # Copy all field values from the line
                line_vals.update({
                    'quotation_id': new_rev.id,  # Link line to the new quotation
                })
                new_lines.append((0, 0, line_vals))

            new_rev.write({'material_line_ids': new_lines})

        # Return action to open the new quotation form
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'interior.quotation',
            'view_mode': 'form',
            'res_id': new_rev.id,
            'target': 'current',
        }

    # -------------------------------------------------------------------------
    # CREATE & SEQUENCE
    # -------------------------------------------------------------------------
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('interior.quotation') or 'New'
        return super().create(vals)
