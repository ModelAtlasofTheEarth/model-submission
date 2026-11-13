import os
from github import Github, Auth
from parse_issue import parse_issue
from crosswalks import dict_to_report

# Environment variables
token = os.environ.get("GITHUB_TOKEN")
issue_number = int(os.environ.get("ISSUE_NUMBER"))
if os.environ.get("COMMENT_ID"):
    comment_id = int(os.environ.get("COMMENT_ID"))
else:
    comment_id = None

# Get issue
auth = Auth.Token(token)
g = Github(auth=auth)
repo = g.get_repo(os.environ.get("GITHUB_REPOSITORY", "ModelAtlasofTheEarth/model-submission"))
issue = repo.get_issue(number = issue_number)
if comment_id:
    comment = issue.get_comment(id = comment_id)

# Parse issue
data, error_log = parse_issue(issue)

# Write report
report = """### Model Report
Thank you for submitting. \n
Using Github actions, we have regenerated a report summarising information about your model \n
* Please check the report below, including the Errors and Warnings section \n
* You can update any information, by editing the markdown file at the top of the issue \n
* these edits will trigger the report will be regenerated \n
* once you are satisfied with the results, please add a https://github.com/ModelAtlasofTheEarth/model_submission/labels/review%20requested label \n"""

report += f"### Parsed data \n {dict_to_report(data)} \n\n"

report += f"### Errors and Warnings \n {error_log} \n\n"

report += """### Next steps
* once the `model_reviewers` team has approved the model, we will create a repository for your model \n\n"""

# Post report to issue as a comment
if comment_id:
    comment.edit(report)
else:
    issue.create_comment(report)

# Add an embargo label if required
if data["embargo"][0]:
    issue.add_to_labels('embargo requested')