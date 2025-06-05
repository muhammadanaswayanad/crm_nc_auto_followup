{
    'name': 'CRM Not Connected Auto Followup',
    'version': '17.0.1.0.0',
    'summary': 'Automates email follow-ups for leads in Not Connected (NC) stage',
    'description': '''
        This module automates the follow-up process for leads in the "Not Connected (NC)" stage:
        - Sends scheduled follow-up emails on days 0, 2, 4, and 6
        - Automatically moves leads to "Cold Lead" stage after 7 days
        - Tracks email status with boolean flags
    ''',
    'category': 'Sales/CRM',
    'author': 'Tiju\'s Academy',
    'depends': ['crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/email_templates.xml',
        'data/ir_cron_data.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
