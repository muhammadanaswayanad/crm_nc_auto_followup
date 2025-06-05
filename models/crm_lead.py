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
        
        # Initialize NC Stage Date for leads that don't have it set
        self._initialize_nc_stage_date(nc_stage)
        
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

    @api.model
    def _initialize_nc_stage_date(self, nc_stage=None):
        """
        Initialize NC Stage Date for existing leads in NC stage that don't have it set.
        This is useful for leads that were in the NC stage before module installation.
        
        :param nc_stage: The NC stage record, if already known
        """
        if not nc_stage:
            nc_stage = self.env['crm.stage'].search([('name', '=', 'Not Connected (NC)')], limit=1)
            if not nc_stage:
                _logger.error("'Not Connected (NC)' stage not found")
                return
        
        # Find leads in NC stage without NC Stage Date
        leads_without_date = self.search([
            ('stage_id', '=', nc_stage.id),
            ('x_nc_stage_date', '=', False)
        ])
        
        if leads_without_date:
            current_date = fields.Date.today()
            _logger.info(f"Setting NC Stage Date to {current_date} for {len(leads_without_date)} leads")
            
            # Set current date as NC Stage Date for these leads
            for lead in leads_without_date:
                lead.write({'x_nc_stage_date': current_date})

    @api.model
    def action_set_nc_stage_date_today(self):
        """
        Action to set the NC Stage Date to today for all leads in 'Not Connected (NC)' stage 
        that don't have an NC Stage Date.
        This can be called manually through the UI to handle existing leads.
        """
        nc_stage = self.env['crm.stage'].search([('name', '=', 'Not Connected (NC)')], limit=1)
        if not nc_stage:
            _logger.error("'Not Connected (NC)' stage not found")
            return {'type': 'ir.actions.act_window_close'}
            
        # Find leads in NC stage without NC Stage Date
        leads_without_date = self.search([
            ('stage_id', '=', nc_stage.id),
            ('x_nc_stage_date', '=', False)
        ])
        
        if leads_without_date:
            today = fields.Date.today()
            count = len(leads_without_date)
            _logger.info(f"Setting NC Stage Date to {today} for {count} leads")
            
            # Set today as NC Stage Date for these leads
            leads_without_date.write({'x_nc_stage_date': today})
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'NC Stage Date Set',
                    'message': f'Set NC Stage Date to today for {count} leads',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Leads Updated',
                    'message': 'No leads in NC stage found without an NC Stage Date',
                    'type': 'info',
                    'sticky': False,
                }
            }

    @api.model
    def _process_cold_leads(self):
        """
        Process cold leads that were previously in NC stage.
        This method can be extended to implement additional handling for cold leads.
        Currently, it just logs the cold leads and provides a hook for future functionality.
        
        Possible future enhancements:
        1. Periodic (e.g., monthly) re-engagement emails
        2. Assignment to a specific salesperson for final review
        3. Archiving leads after a certain period
        4. Moving to a marketing automation campaign for nurturing
        5. Generating reports on conversion rates from NC to customers
        """
        cold_stage = self.env['crm.stage'].search([('name', '=', 'Cold Lead')], limit=1)
        if not cold_stage:
            _logger.error("'Cold Lead' stage not found")
            return
            
        # Find leads that were moved from NC to Cold
        cold_leads = self.search([
            ('stage_id', '=', cold_stage.id),
            ('x_moved_to_cold', '=', True)
        ])
        
        _logger.info(f"Found {len(cold_leads)} cold leads that were previously in NC stage")
        
        # Placeholder for future cold lead processing
        # Currently no additional actions are taken with cold leads
        return cold_leads

    @api.model
    def _detect_whatsapp_engagement(self, message):
        """
        Detect WhatsApp engagement from message and move lead to Email Re-engaged stage
        
        :param message: The mail.message record that was created
        """
        if not message or not message.body or not isinstance(message.body, str):
            return False
            
        # Check if this is a WhatsApp message
        if "WhatsApp Message:" in message.body:
            _logger.info(f"WhatsApp engagement detected in message {message.id}")
            
            # Find the related lead
            lead = False
            if message.model == 'crm.lead' and message.res_id:
                lead = self.browse(message.res_id)
            
            if not lead:
                _logger.warning(f"Could not find lead for WhatsApp message {message.id}")
                return False
                
            # Find Email Re-engaged stage
            reengaged_stage = self.env['crm.stage'].search([('name', '=', 'Email Re-engaged')], limit=1)
            if not reengaged_stage:
                _logger.error("'Email Re-engaged' stage not found")
                return False
                
            # Move to Email Re-engaged stage if the lead is in NC or Cold stage
            nc_stage = self.env['crm.stage'].search([('name', '=', 'Not Connected (NC)')], limit=1)
            cold_stage = self.env['crm.stage'].search([('name', '=', 'Cold Lead')], limit=1)
            
            if lead.stage_id.id in [nc_stage.id, cold_stage.id]:
                _logger.info(f"Moving lead {lead.id} to Email Re-engaged stage due to WhatsApp engagement")
                lead.write({
                    'stage_id': reengaged_stage.id,
                    'x_moved_to_cold': False  # Reset the moved to cold flag if it was set
                })
                
                # Add an internal note about the stage change
                lead.message_post(
                    body=f"Lead automatically moved to 'Email Re-engaged' stage due to WhatsApp message.",
                    message_type='notification',
                    subtype_id=self.env.ref('mail.mt_note').id
                )
                
                return True
        
        return False
