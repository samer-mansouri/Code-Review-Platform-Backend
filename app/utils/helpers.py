from datetime import datetime
from app.models.log import Log
from flask import request
import requests
from dateutil import parser as date_parser

def paginate_query(queryset, request):
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    total = queryset.count()
    items = queryset.skip((page - 1) * limit).limit(limit)
    return {"items": items, "total": total, "page": page, "limit": limit}


def log_action(user_id, action, details):
    Log(user_id=str(user_id), action=action, details=details).save()


def is_gitlab_token_valid(token: str) -> bool:
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = requests.get("https://gitlab.com/api/v4/user", headers=headers)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_gitlab_project_by_url(project_url: str, token: str):
    try:
        # Extract path after domain
        path = project_url.replace("https://gitlab.com/", "").strip("/")
        api_url = f"https://gitlab.com/api/v4/projects/{requests.utils.quote(path, safe='')}"

        headers = {"Authorization": f"Bearer {token}"}
        print("token", token)
        print("api_url", api_url)
        res = requests.get(api_url, headers=headers)

        if res.status_code == 200:
            return res.json(), None
        return None, f"GitLab API error: {res.status_code}"
    except Exception as e:
        return None, str(e)
    
def get_gitlab_commits_with_diffs(project_id: int, token: str, limit: int = 5):
    headers = {"Authorization": f"Bearer {token}"}
    base_url = f"https://gitlab.com/api/v4/projects/{project_id}"

    # Step 1: Get recent commits
    commits_url = f"{base_url}/repository/commits?per_page={limit}"
    try:
        commits_res = requests.get(commits_url, headers=headers)
        commits_res.raise_for_status()
        commits = commits_res.json()
    except Exception as e:
        return None, f"Error fetching commits: {e}"

    # Step 2: Fetch diffs for each commit from /commits/:sha/diff
    full_commits = []
    for commit in commits:
        sha = commit["id"]
        diff_url = f"{base_url}/repository/commits/{sha}/diff"
        try:
            diff_res = requests.get(diff_url, headers=headers)
            diff_res.raise_for_status()
            diffs = diff_res.json()

            full_commits.append({
                "sha": sha,
                "title": commit.get("title"),
                "author_name": commit.get("author_name"),
                "created_at": date_parser.parse(commit.get("created_at")),
                "diffs": diffs
            })
        except Exception as e:
            full_commits.append({
                "sha": sha,
                "error": f"Failed to fetch diffs: {e}"
            })

    return full_commits, None

def get_gitlab_merge_requests_with_commits_and_diffs(project_id: int, token: str, limit: int = 10):
    headers = {"Authorization": f"Bearer {token}"}
    base_url = f"https://gitlab.com/api/v4/projects/{project_id}"

    # 1. Fetch MRs
    try:
        mr_url = f"{base_url}/merge_requests?per_page={limit}&order_by=created_at"
        mr_res = requests.get(mr_url, headers=headers)
        mr_res.raise_for_status()
        merge_requests = mr_res.json()
    except Exception as e:
        return None, f"Error fetching MRs: {e}"

    result = []

    for mr in merge_requests:
        iid = mr["iid"]
        commits_url = f"{base_url}/merge_requests/{iid}/commits"

        try:
            # 2. Get commits for MR
            commits_res = requests.get(commits_url, headers=headers)
            commits_res.raise_for_status()
            commits = commits_res.json()
        except Exception as e:
            result.append({"iid": iid, "error": f"Error fetching commits: {e}"})
            continue

        full_commits = []

        for commit in commits:
            sha = commit["id"]
            diff_url = f"{base_url}/repository/commits/{sha}/diff"

            try:
                diff_res = requests.get(diff_url, headers=headers)
                diff_res.raise_for_status()
                diffs = diff_res.json()
            except Exception as e:
                diffs = [{"error": str(e)}]

            full_commits.append({
                "id": sha,
                "title": commit.get("title"),
                "author_name": commit.get("author_name"),
                "created_at": commit.get("created_at"),
                "diffs": diffs
            })

        result.append({
            "iid": iid,
            "title": mr.get("title"),
            "description": mr.get("description"),
            "state": mr.get("state"),
            "created_at": date_parser.parse(mr.get("created_at")),
            "merged_at": date_parser.parse(mr.get("merged_at")) if mr.get("merged_at") else None,
            "source_branch": mr.get("source_branch"),
            "target_branch": mr.get("target_branch"),
            "author": mr.get("author", {}).get("username") if isinstance(mr.get("author"), dict) else None,
            "commits": full_commits
        })

    return result, None

def get_gitlab_mr_full_info(project_id: int, token: str, iid: int):
    headers = {"Authorization": f"Bearer {token}"}
    base = f"https://gitlab.com/api/v4/projects/{project_id}/merge_requests/{iid}"

    try:
        # 1. Metadata (title, state, mergeability, etc.)
        mr_res = requests.get(base, headers=headers)
        mr_res.raise_for_status()
        mr = mr_res.json()

        # 2. Commits
        commits_res = requests.get(f"{base}/commits", headers=headers)
        commits_res.raise_for_status()
        commits = commits_res.json()

        # 3. Code changes (diffs)
        changes_res = requests.get(f"{base}/changes", headers=headers)
        changes_res.raise_for_status()
        changes = changes_res.json().get("changes", [])

        # 4. Approvals (optional)
        approvals_res = requests.get(f"{base}/approvals", headers=headers)
        approvals = approvals_res.json() if approvals_res.status_code == 200 else {}

        return {
            "iid": mr["iid"],
            "title": mr.get("title"),
            "description": mr.get("description"),
            "state": mr.get("state"),
            "merge_status": mr.get("merge_status"),
            "source_branch": mr.get("source_branch"),
            "target_branch": mr.get("target_branch"),
            "author": mr.get("author", {}).get("username"),
            "commits": [
                {
                    "id": c["id"],
                    "title": c["title"],
                    "created_at": c["created_at"],
                    "author_name": c["author_name"]
                } for c in commits
            ],
            "diffs": changes,
            "approvals": approvals
        }, None

    except Exception as e:
        return None, str(e)


def get_all_gitlab_merge_requests_full(project_id: int, token: str, limit: int = 20):
    headers = {"Authorization": f"Bearer {token}"}
    base = f"https://gitlab.com/api/v4/projects/{project_id}"

    try:
        mr_url = f"{base}/merge_requests?per_page={limit}&order_by=created_at"
        res = requests.get(mr_url, headers=headers)
        res.raise_for_status()
        all_mrs = res.json()
    except Exception as e:
        return None, f"Error fetching MR list: {e}"

    full_mrs = []
    for mr in all_mrs:
        iid = mr.get("iid")
        full_data, err = get_gitlab_mr_full_info(project_id, token, iid)
        if err:
            full_mrs.append({"iid": iid, "error": err})
        else:
            full_mrs.append(full_data)

    return full_mrs, None

# GitHub related functions

def is_github_token_valid(token: str) -> bool:
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        print("response", response.text)
        return response.status_code == 200
    except requests.RequestException:
        return False


def get_github_project_by_url(repo_url: str, token: str):
    try:
        # Extract owner and repo name from URL
        path = repo_url.replace("https://github.com/", "").strip("/")
        owner, repo = path.split("/")[:2]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        res = requests.get(api_url, headers=headers)

        if res.status_code == 200:
            print("res", res.text)
            return res.json(), None
        return None, f"GitHub API error: {res.status_code}"
    except Exception as e:
        return None, str(e)
    
def get_github_commits_with_diffs(owner: str, repo: str, token: str, limit: int = 5):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    # Step 1: Get recent commits
    commits_url = f"{base_url}/commits?per_page={limit}"
    try:
        commits_res = requests.get(commits_url, headers=headers)
        commits_res.raise_for_status()
        commits = commits_res.json()
    except Exception as e:
        return None, f"Error fetching commits: {e}"

    # Step 2: Fetch diffs for each commit
    full_commits = []
    for commit in commits:
        sha = commit["sha"]
        commit_url = f"{base_url}/commits/{sha}"
        try:
            commit_res = requests.get(commit_url, headers=headers)
            commit_res.raise_for_status()
            commit_details = commit_res.json()
            
            # GitHub includes diffs in the commit details response
            full_commits.append({
                "sha": sha,
                "commit": {  # GitHub has commit info nested under 'commit'
                    "message": commit_details["commit"]["message"].split("\n")[0],
                    "author": commit_details["commit"]["author"],
                },
                "author": commit_details.get("author"),
                "stats": commit_details.get("stats"),
                "files": commit_details.get("files", [])  # This contains the diffs
            })
        except Exception as e:
            full_commits.append({
                "sha": sha,
                "error": f"Failed to fetch commit details: {e}"
            })

    print("full_commits", full_commits)

    return full_commits, None

def get_github_pull_requests_with_commits_and_diffs(owner: str, repo: str, token: str, limit: int = 10):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    # 1. Fetch PRs
    try:
        pr_url = f"{base_url}/pulls?per_page={limit}&state=all&sort=created&direction=desc"
        pr_res = requests.get(pr_url, headers=headers)
        pr_res.raise_for_status()
        pull_requests = pr_res.json()
    except Exception as e:
        return None, f"Error fetching PRs: {e}"

    result = []

    for pr in pull_requests:
        number = pr["number"]
        commits_url = f"{base_url}/pulls/{number}/commits"

        try:
            # 2. Get commits for PR
            commits_res = requests.get(commits_url, headers=headers)
            commits_res.raise_for_status()
            commits = commits_res.json()
        except Exception as e:
            result.append({"number": number, "error": f"Error fetching commits: {e}"})
            continue

        full_commits = []

        for commit in commits:
            sha = commit["sha"]
            commit_url = f"{base_url}/commits/{sha}"

            try:
                commit_res = requests.get(commit_url, headers=headers)
                commit_res.raise_for_status()
                commit_details = commit_res.json()
                
                full_commits.append({
                    "sha": sha,
                    "commit": {
                        "message": commit_details["commit"]["message"].split("\n")[0],
                        "author": commit_details["commit"]["author"],
                    },
                    "author": commit_details.get("author"),
                    "files": commit_details.get("files", [])  # Diffs are in 'files'
                })
            except Exception as e:
                full_commits.append({
                    "sha": sha,
                    "error": f"Failed to fetch commit details: {e}"
                })

        result.append({
            "number": number,
            "title": pr.get("title"),
            "body": pr.get("body"),
            "state": pr.get("state"),
            "created_at": date_parser.parse(pr.get("created_at")),
            "merged_at": date_parser.parse(pr.get("merged_at")) if pr.get("merged_at") else None,
            "head": {
                "ref": pr.get("head", {}).get("ref"),
                "sha": pr.get("head", {}).get("sha")
            },
            "base": {
                "ref": pr.get("base", {}).get("ref"),
                "sha": pr.get("base", {}).get("sha")
            },
            "user": pr.get("user", {}).get("login"),
            "commits": full_commits
        })

    print("result", len(result))
    print("result[0]", result[0])

    return result, None

def get_github_pr_full_info(owner: str, repo: str, token: str, pr_number: int):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    base_url = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        # 1. Fetch PR metadata
        pr_url = f"{base_url}/pulls/{pr_number}"
        pr_res = requests.get(pr_url, headers=headers)
        pr_res.raise_for_status()
        pr = pr_res.json()

        # 2. Get commits for PR with full details
        commits_url = f"{base_url}/pulls/{pr_number}/commits"
        commits_res = requests.get(commits_url, headers=headers)
        commits_res.raise_for_status()
        commits = commits_res.json()

        full_commits = []
        for commit in commits:
            sha = commit["sha"]
            commit_url = f"{base_url}/commits/{sha}"

            try:
                commit_res = requests.get(commit_url, headers=headers)
                commit_res.raise_for_status()
                commit_details = commit_res.json()
                
                full_commits.append({
                    "sha": sha,
                    "commit": {
                        "message": commit_details["commit"]["message"].split("\n")[0],
                        "author": commit_details["commit"]["author"],
                    },
                    "author": commit_details.get("author"),
                    "files": commit_details.get("files", [])  # Diffs are in 'files'
                })
            except Exception as e:
                full_commits.append({
                    "sha": sha,
                    "error": f"Failed to fetch commit details: {e}"
                })

        # 3. Get files changed (diff)
        files_url = f"{base_url}/pulls/{pr_number}/files"
        files_res = requests.get(files_url, headers=headers)
        files = files_res.json() if files_res.status_code == 200 else []

        # 4. Get reviews
        reviews_url = f"{base_url}/pulls/{pr_number}/reviews"
        reviews_res = requests.get(reviews_url, headers=headers)
        reviews = reviews_res.json() if reviews_res.status_code == 200 else []

        return {
            "number": pr["number"],
            "title": pr.get("title"),
            "state": pr.get("state"),
            "created_at": date_parser.parse(pr.get("created_at")),
            "merged_at": date_parser.parse(pr.get("merged_at")) if pr.get("merged_at") else None,
            "head_ref": pr.get("head", {}).get("ref"),
            "base_ref": pr.get("base", {}).get("ref"),
            "user_login": pr.get("user", {}).get("login"),
            "commits": full_commits,
            "files": files,
            "reviews": reviews
        }, None

    except Exception as e:
        return None, str(e)


def get_all_github_pull_requests_full(owner: str, repo: str, token: str, limit: int = 20):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    base = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        pr_url = f"{base}/pulls?per_page={limit}&state=all&sort=created&direction=desc"
        res = requests.get(pr_url, headers=headers)
        res.raise_for_status()
        all_prs = res.json()
    except Exception as e:
        return None, f"Error fetching PR list: {e}"

    full_prs = []
    for pr in all_prs:
        number = pr.get("number")
        full_data, err = get_github_pr_full_info(owner, repo, token, number)
        if err:
            full_prs.append({"number": number, "error": err})
        else:
            full_prs.append(full_data)

    return full_prs, None
