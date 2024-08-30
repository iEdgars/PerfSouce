## Mertic explanation, formulas, considerations

# Time to market

### Epic/Story Lead Time (days):
Date to show on graph based on date Epic/Story is completed. Any non-completed items are excluded.  
**Calclucation:** `Date completed - Date created`, data limited to 365 days based on resolution date
```
SELECT *
FROM issues
WHERE field IN('resolutiondate', 'created')
	AND issue_status_cat_name = 'Done'
	AND issue_status <> 'Rejected'
	AND field_value <> 'None'
--	AND issue_type_name = 'Epic' --for Epic Lead Time
--	AND issue_type_name <> 'Epic' --for Story Lead Time
```

**Considerations:** Taken are only Done items, Rejected or ToDo/InProgress are discarded.

### Epic/Story Cycle Time (days):
Date to show on graph based on date Epic/Story is completed. Any non-completed items are excluded.  
**Calclucation:** `Date completed - First "In Progress" date`, data limited to 365 days based on resolution date
```
SELECT ic.the_project, ic.jira_project, ic.issue_id, ic."key", MIN(ic.change_date_time) first_in_progress
FROM issue_changelog ic
	JOIN project_issues_and_statuses pis ON ic.value_to = pis.untranslated_name
WHERE ic.issue_status_cat_name = 'Done'
	AND ic.issue_status <> 'Rejected'
	AND ic.field = 'status'
--	AND issue_type_name = 'Epic' --for Epic Lead Time
--	AND issue_type_name <> 'Epic' --for Story Lead Time
	AND pis.category_name = 'In Progress'
GROUP BY ic.the_project, ic.jira_project, ic.issue_id, ic."key"
```

**Considerations:** Taken are only items having InProgress. Some items that has a lot of changes are missing `expand=changelog` records, therefore missing date it went to **In Progress** and therfore is discarded in Cycle time calculations even though it was completed. **Possible option** in such cases to include Lead time when Cycle time is not available. *(example of such behaviour -3780)*  

### Time in Status by month:
Show average time per each status or status group for items within the month.
**Calclucation:** `vizDataJira.ttm_calculate_time_in_status()` exports all status changes from `issue_changelog` adding row for creation date for time in first status and row of today's date for time between latest change for current status.  
Dataset is then calculated to take dates for each assignment start, end or both within the month. **Time In Status** then is calculated as difference between: 
- `Status End - Status Start` - When Status started and ended within the month
- `Status End - Month Start` - When Status started in previous month, but ended in current
- `Month End - Status Start` - When Status started in current month and has not ended will end of month
- `Month End - Month Start` - When Status started in previous month and has not ended will end of month

**Visual filtering:** Issue type (*Story, Bug*), Status Group (all *To Do, In Progress* statuses), Status (lowest status level as *Backlog, UAT, Ready*) 

**Considerations:** Items in ***Done*** Status Group, as well in ***NaN*** *(when corresponding status group not found due to item brought in from different project with status not existing on project we are looking at)* are excluded.  
Months are represented as 12 months back from now. Date picker could be added to serve as stating date, so if Feb 1 is selected, it would show 12 months back from it up to Feb  
Time of issue in status is calculated in hours that are summarized and represented in days. Calculating full days between status change would increase value as some items might change several times within a day *(example of such behaviour -4778)*  

### Story Spillover:

**Calclucation:** Tickets in **Done** state and their changes in Sprint assigment. Represented on Sprint it was closed.

**Visual filtering:** Board id; Change between list of sprints vs **3+ Sprints**

**Considerations:**  
- Sprint assignment must be within sprint timeframe
- **Commited items only** - Periods without sprint assigment are not included. For example if issue was assigned to to *Sprint 9*, and finished to *Sprint 11*, but was never assigned to *Sprint 10*, would be considered as 2 sprints. Items commited regardless of status (except in Done statuses) would be condidered included. e.g. if item was commited into Sprint's 9 as Ready; Sprint 10, it went though Ready > In Progress > Blocked; Sprint 11 Blocked > In Progress > Done; would be considered as **3+ sprints**.  
- Not sure if `x axis` by sprints is really correct way for this visual, or would it better be monthly.  
  
#  
# Throughput / Productivity

### # of Story points released per month:
