# CRM Not Connected Auto Followup

This Odoo module automates email follow-ups for leads in the "Not Connected (NC)" stage. It helps maintain engagement with leads that couldn't be reached by phone, following a systematic approach to re-engage them.

## Features

- **Automatic Trigger**: When a lead enters the "Not Connected (NC)" stage, the system records the date and starts the follow-up sequence
- **Timed Email Series**: Sends 4 follow-up emails at specific intervals (Day 0, 2, 4, and 6)
- **Automatic Stage Change**: Moves leads to "Cold Lead" stage on Day 7 if there's no response
- **Email Tracking**: Uses boolean flags to track which emails have been sent
- **Customizable Templates**: 4 pre-configured email templates with placeholders for course name

## Technical Details

### Added Fields to CRM Lead

- `x_nc_stage_date`: Date when the lead entered the NC stage
- `x_nc_email_1_sent`, `x_nc_email_2_sent`, `x_nc_email_3_sent`, `x_nc_email_4_sent`: Boolean flags for tracking sent emails
- `x_moved_to_cold`: Boolean flag indicating if the lead was automatically moved to Cold Lead stage

### Daily Cron Job

A scheduled action runs daily to:
1. Check for leads in the "Not Connected (NC)" stage
2. Calculate how many days they've been in this stage
3. Send the appropriate email based on the day count
4. Move leads to "Cold Lead" stage after 7 days

## Configuration

The module will work out of the box if your CRM has stages named exactly:
- "Not Connected (NC)"
- "Cold Lead"

If your stage names are different, you may need to modify the code accordingly.

## Dependencies

- CRM module
- Mail module
