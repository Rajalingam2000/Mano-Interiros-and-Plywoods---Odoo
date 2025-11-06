from odoo import http
from odoo.http import request, Response
import json


class InteriorQuotationController(http.Controller):

    @http.route('/api/interior_quotation/create', type='json', auth='user', methods=['POST'], csrf=False)
    def create_interior_quotation(self, **kwargs):
        try:
            data = request.jsonrequest

            # Required fields
            project_name = data.get('project_name')
            partner_id = data.get('partner_id')

            if not project_name or not partner_id:
                return {
                    'success': False,
                    'message': 'project_name and partner_id are required.'
                }

            # Create record
            quotation = request.env['interior.quotation'].sudo().create({
                'project_name': project_name,
                'partner_id': partner_id,
                'address': data.get('address'),
                'quotation_title': data.get('quotation_title'),
                'validity_days': data.get('validity_days', 30),
            })

            return {
                'success': True,
                'message': 'Quotation created successfully',
                'id': quotation.id,
                'name': quotation.name,
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
