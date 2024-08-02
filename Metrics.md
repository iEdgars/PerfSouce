# Mertic explanation, formulas, considerations

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