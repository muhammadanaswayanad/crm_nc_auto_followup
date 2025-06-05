from odoo import api, models
import logging

_logger = logging.getLogger(__name__)

class MailMessage(models.Model):
    _inherit = 'mail.message'
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override to detect WhatsApp messages and trigger lead re-engagement"""
        messages = super(MailMessage, self).create(vals_list)
        
        # Check each created message for WhatsApp engagement
        for message in messages:
            try:
                self.env['crm.lead']._detect_whatsapp_engagement(message)
            except Exception as e:
                _logger.error(f"Error detecting WhatsApp engagement: {str(e)}")
                
        return messages
