# Mertic explanation, formulas, considerations

## Epic/Story Lead Time (days):
Date to show on graph based on date Epic/Story is completed. Any non-completed items are excluded.  
**Calclucation:** `Date completed - Date created`  
**Jira Data Filtering:** `field = 'resolutiondate' AND field_value <> 'None'`  
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

## Epic/Story Cucle Time (days):
Date to show on graph based on date Epic/Story is completed. Any non-completed items are excluded.  
**Calclucation:** `Date completed - First "In Progress" date`