from typing import Literal

#storing Help text seperatelly to simplify main code
project_help = '''
Your project code in <EPAM> system.\n 
it can be found under:\n 
    https://projects.epam.com/dashboard/projects\n 
\n 
"Only where I am Key Staff" toggle can help to narrow down.
'''

username_help = '''
Your username for Jira.\n 
Often it's email address.
'''

api_key_help = '''
Provide API Token for your user account.\n 
API token can be created here:\n 
https://id.atlassian.com/manage-profile/security/api-tokens
'''

jira_url_help = '''
Start of URL when opening Jira.\n 
Example:\n 
https://epam.atlassian.net/
'''

selected_project_option_help = '''
Select your Jira Project.\n
Selections are based by Project Key and Project Name.\n 
e.g. ADOM: Data Management Tool
'''

selected_board_option_help = '''
Select Jira board to collect metrics for.\n 
Selections are based by Board ID and Board name.\n 
e.g. 123: DMT Scrum Board\n 
\n 
To collect metrics for entire Project, select "Use whole Project"
'''

estimation_in_SP_help = '''
The value is used for calculating metrics in story points such as Burn Up in story points, Committed vs Completed & Commitment Rate, etc.
'''

estimation_in_OrgH_help = '''
The value is used for calculating metrics in original hours such as Burn Up in hours, Committed vs Completed & Commitment Rate, etc.
'''

def ttm_text(
        issue_type: Literal['Epic','Story'],
        metric_type: Literal['Lead','Cycle']
        ):
    txt = f'''
         Total time from {issue_type}'s creation to its delivery to end users. Defines how long it takes to the team to deliver tangible value. 
         Time in days from the {issue_type}'s creation to "Closed" status, last 12 months avg. 
    '''
    
    return txt