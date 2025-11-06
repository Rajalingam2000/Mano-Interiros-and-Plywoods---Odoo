from odoo import models, fields, api


class InteriorQuotationMaterial(models.Model):
    _name = 'interior.quotation.material'
    _description = 'Interior Quotation Material Line'

    quotation_id = fields.Many2one(
        'interior.quotation',
        string='Quotation Reference',
        ondelete='cascade'
    )
    product_id = fields.Many2one('product.product', string='Product', required=True)
    qty = fields.Float(string='Quantity', default=1.0)
    width = fields.Float(string='Width (ft)', help='Width of the item in feet')
    height = fields.Float(string='Height (ft)', help='Height of the item in feet')

    sqft = fields.Float(string='Total Sqft', compute='_compute_sqft', store=True)
    rate = fields.Float(string='Rate per Sqft')
    amount = fields.Float(string='Amount', compute='_compute_amount', store=True)

    currency_id = fields.Many2one(
        related='quotation_id.currency_id',
        store=True,
        readonly=True
    )

    @api.depends('width', 'height', 'qty')
    def _compute_sqft(self):
        """Compute total square feet"""
        for rec in self:
            rec.sqft = (rec.width or 0.0) * (rec.height or 0.0) * (rec.qty or 1.0)

    @api.depends('sqft', 'rate')
    def _compute_amount(self):
        """Compute amount as sqft * rate"""
        for rec in self:
            rec.amount = (rec.sqft or 0.0) * (rec.rate or 0.0)
