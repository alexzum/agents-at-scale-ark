import logging
from typing import Any

from github import Auth, Github, GithubException

from .config import settings
from .models import PRMetadata

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self) -> None:
        auth = Auth.Token(settings.github_token)
        self.client = Github(auth=auth, base_url=settings.github_api_url)
    
    async def get_pr_metadata(self, repository: str, pr_number: int) -> PRMetadata:
        try:
            repo = self.client.get_repo(repository)
            pr = repo.get_pull(pr_number)
            
            files_changed = [f.filename for f in pr.get_files()]
            
            diff_text = ""
            for file in pr.get_files():
                if file.patch:
                    diff_text += f"\n--- {file.filename}\n{file.patch}\n"
            
            return PRMetadata(
                number=pr.number,
                title=pr.title,
                body=pr.body or "",
                head_branch=pr.head.ref,
                base_branch=pr.base.ref,
                commit_sha=pr.head.sha,
                files_changed=files_changed,
                diff=diff_text,
                additions=pr.additions,
                deletions=pr.deletions,
                changed_files_count=pr.changed_files,
            )
        except GithubException as e:
            logger.error(f"Failed to fetch PR metadata: {e}")
            raise
    
    async def get_file_content(
        self, repository: str, path: str, ref: str
    ) -> str | None:
        try:
            repo = self.client.get_repo(repository)
            content = repo.get_contents(path, ref=ref)
            
            if isinstance(content, list):
                return None
            
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            logger.warning(f"Failed to fetch file {path}: {e}")
            return None
    
    def close(self) -> None:
        self.client.close()

