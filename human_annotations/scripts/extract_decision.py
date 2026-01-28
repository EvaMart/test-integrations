import requests, sys, os, re, json
from datetime import datetime, timezone

repo = sys.argv[1]
issue_number = sys.argv[2]
conflict_id = sys.argv[3]

token = os.environ['GITHUB_TOKEN']
api_base = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}


# Fetch body 
issue = requests.get(api_base, headers=headers).json()
body = issue.get("body", "")

conflict_id_match = re.search(r"^Conflict Id:\s*(\S+)\s*$", body, flags=re.MULTILINE)
file_url_match = re.search(r"^Conflict File:\s*(https?://\S+)\s*$", body, flags=re.MULTILINE)

if not conflict_id_match:
    raise ValueError("Conflict Id not found in issue body")
if not file_url_match:
    raise ValueError("Conflict File URL not found in issue body")

conflict_id = conflict_id_match.group(1)
conflict_file_url = file_url_match.group(1)

record = {
    'conflict_id': conflict_id,
    'date': datetime.now(timezone.utc).isoformat(),
    'conflict_name': conflict_id.split('_')[-1],
    'conflict_url': conflict_file_url
}


# Fetch comments
comments = requests.get(f"{api_base}/comments", headers=headers).json()

json_error = "No JSON block found in any comment."
human_annotations_path = 'human_annotations/human_conflicts_log.jsonl'
# Try to parse a JSON block from comments
for comment in reversed(comments):
    print("---- COMMENT BODY ----")
    print(comment['body'])

    matches = re.findall(r"```json\s*\n(.*?)```", comment['body'], re.DOTALL)
    print("Matches found:", len(matches))

    if matches:
        try:
            print("Trying to load JSON block:")
            print(matches[0])
            data = json.loads(matches[0])
            data['issue_url'] = f"https://github.com/inab/research-software-etl/issues/{issue_number}"
            
            record ['decision'] = data 
            #add_jsonl_record(human_annotations_path, record)

            print(record)
 
            sys.exit(0)
        except Exception as e:
            json_error = f"Error: {e}"

# If we reach here, parsing failed
comment_payload = {
    "body": f"⚠️ Failed to parse a valid JSON decision block from this issue.\nError: `{json_error}`\n\nPlease ensure the format is correct:\n```json\n{{ ... }}\n```"
}
requests.post(f"{api_base}/comments", headers=headers, data=json.dumps(comment_payload))

# Reopen the issue
reopen_payload = {"state": "open"}
requests.patch(api_base, headers=headers, data=json.dumps(reopen_payload))

print(json.dumps({"error": "No valid decision found"}))
sys.exit(1)