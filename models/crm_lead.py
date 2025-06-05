from odoo import api, fields, models
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    x_nc_stage_date = fields.Date(
        string='NC Stage Date',
        help='Date when lead entered Not Connected (NC) stage'
    )
    x_nc_email_1_sent = fields.Boolean(
        string='NC Email 1 Sent',
        default=False,
        help='Whether the first follow-up email has been sent'
    )
    x_nc_email_2_sent = fields.Boolean(
        string='NC Email 2 Sent',
        default=False,
        help='Whether the second follow-up email has been sent'
    )
    x_nc_email_3_sent = fields.Boolean(
        string='NC Email 3 Sent',
        default=False,
        help='Whether the third follow-up email has been sent'
    )
    x_nc_email_4_sent = fields.Boolean(
        string='NC Email 4 Sent',
        default=False,
        help='Whether the fourth follow-up email has been sent'
    )
    x_moved_to_cold = fields.Boolean(
        string='Moved to Cold Lead',
        default=False,
        help='Whether the lead has been automatically moved to Cold Lead stage'
    )

    @api.model
    def _cron_process_nc_followups(self):
        """
        Cron job to process follow-up emails and stage changes for leads
        in Not Connected (NC) stage.
        """
        _logger.info("Starting NC follow-up processing")
        
        # Find NC and Cold Lead stage IDs by name
        nc_stage = self.env['crm.stage'].search([('name', '=', 'Not Connected (NC)')], limit=1)
        cold_stage = self.env['crm.stage'].search([('name', '=', 'Cold Lead')], limit=1)
        
        if not nc_stage:
            _logger.error("'Not Connected (NC)' stage not found")
            return
            
        if not cold_stage:
            _logger.error("'Cold Lead' stage not found")
            return
            
        today = fields.Date.today()
        
        # Process leads in NC stage with a stored NC stage date
        nc_leads = self.search([
            ('stage_id', '=', nc_stage.id),
            ('x_nc_stage_date', '!=', False),
            ('x_moved_to_cold', '=', False)
        ])
        
        for lead in nc_leads:
            days_in_nc = (today - lead.x_nc_stage_date).days
            _logger.info(f"Processing lead {lead.id} - {lead.name}, days in NC: {days_in_nc}")
            
            # Day 0 - First email
            if days_in_nc == 0 and not lead.x_nc_email_1_sent:
                self._send_nc_followup_email(lead, 1)
                
            # Day 2 - Second email
            elif days_in_nc == 2 and not lead.x_nc_email_2_sent:
                self._send_nc_followup_email(lead, 2)
                
            # Day 4 - Third email
            elif days_in_nc == 4 and not lead.x_nc_email_3_sent:
                self._send_nc_followup_email(lead, 3)
                
            # Day 6 - Fourth email
            elif days_in_nc == 6 and not lead.x_nc_email_4_sent:
                self._send_nc_followup_email(lead, 4)
                
            # Day 7 - Move to Cold Lead stage
            elif days_in_nc >= 7:
                _logger.info(f"Moving lead {lead.id} to Cold Lead stage")
                lead.write({
                    'stage_id': cold_stage.id,
                    'x_moved_to_cold': True
                })

    def _send_nc_followup_email(self, lead, email_num):
        """
        Send a follow-up email to the lead based on the template number.
        
        :param lead: The lead record to send the email to
        :param email_num: The email template number (1-4)
        """
        template_xml_id = f'crm_nc_auto_followup.email_template_nc_followup_{email_num}'
        try:
            template = self.env.ref(template_xml_id)
            if template:
                _logger.info(f"Sending follow-up email {email_num} to lead {lead.id}")
                template.send_mail(lead.id, force_send=True)
                lead.write({f'x_nc_email_{email_num}_sent': True})
            else:
                _logger.error(f"Email template {template_xml_id} not found")
        except Exception as e:
            _logger.error(f"Failed to send follow-up email {email_num}: {str(e)}")

    @api.model
    def create(self, vals):
        """Override to check for NC stage on creation"""
        res = super(CrmLead, self).create(vals)
        # Check if created with NC stage
        self._check_nc_stage(res)
        return res

    def write(self, vals):
        """Override to check for NC stage change"""
        res = super(CrmLead, self).write(vals)
        # Check if stage is changed to NC
        if 'stage_id' in vals:
            for lead in self:
                self._check_nc_stage(lead)
        return res

    def _check_nc_stage(self, lead):
        """
        Check if lead is in NC stage and set the NC stage date if needed
        
        :param lead: The lead record to check
        """
        nc_stage = self.env['crm.stage'].search([('name', '=', 'Not Connected (NC)')], limit=1)
        if nc_stage and lead.stage_id.id == nc_stage.id and not lead.x_nc_stage_date:
            _logger.info(f"Lead {lead.id} entered NC stage, setting date")
            lead.write({'x_nc_stage_date': fields.Date.today()})
