import json
import logging
import time
from typing import Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .config import settings
from .models import CodeQualityReview, FunctionalityReview, PRMetadata, JiraTicket

logger = logging.getLogger(__name__)


class ARKClient:
    def __init__(self) -> None:
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        self.custom_api = client.CustomObjectsApi()
        self.namespace = settings.kubernetes_namespace
    
    async def create_review_query(
        self,
        review_id: str,
        pr_metadata: PRMetadata,
        jira_ticket: JiraTicket | None,
    ) -> str:
        query_name = f"pr-{pr_metadata.number}-{int(time.time())}"
        
        jira_info = ""
        if jira_ticket:
            jira_info = f"""
Jira Ticket: {jira_ticket.key}
Summary: {jira_ticket.summary}
Description: {jira_ticket.description or 'N/A'}
Status: {jira_ticket.status}
Acceptance Criteria: {jira_ticket.acceptance_criteria or 'Not specified'}
"""
        else:
            jira_info = "Jira ticket: Not available (using PROJ-000 or ticket not found)"
        
        query_input = f"""Review this pull request:

PR #{pr_metadata.number}: {pr_metadata.title}
Branch: {pr_metadata.head_branch} → {pr_metadata.base_branch}
Commit: {pr_metadata.commit_sha}

{jira_info}

PR Description:
{pr_metadata.body or 'No description provided'}

Files Changed ({pr_metadata.changed_files_count}):
{chr(10).join(f"  - {f}" for f in pr_metadata.files_changed[:20])}
{f"  ... and {pr_metadata.changed_files_count - 20} more files" if pr_metadata.changed_files_count > 20 else ""}

Diff:
{pr_metadata.diff[:15000]}
{"... (diff truncated)" if len(pr_metadata.diff) > 15000 else ""}

Please provide your analysis in JSON format.
"""
        
        query_spec = {
            "apiVersion": "ark.mckinsey.com/v1alpha1",
            "kind": "Query",
            "metadata": {
                "name": query_name,
                "namespace": self.namespace,
                "labels": {
                    "app": "ark-pr-reviewer",
                    "review-id": review_id,
                    "pr-number": str(pr_metadata.number),
                },
            },
            "spec": {
                "input": query_input,
                "targets": [
                    {
                        "type": "team",
                        "name": settings.team_name,
                    }
                ],
            },
        }
        
        try:
            self.custom_api.create_namespaced_custom_object(
                group="ark.mckinsey.com",
                version="v1alpha1",
                namespace=self.namespace,
                plural="queries",
                body=query_spec,
            )
            logger.info(f"Created ARK Query: {query_name}")
            return query_name
        except ApiException as e:
            logger.error(f"Failed to create ARK Query: {e}")
            raise
    
    async def get_query_status(self, query_name: str) -> dict[str, Any]:
        try:
            query = self.custom_api.get_namespaced_custom_object(
                group="ark.mckinsey.com",
                version="v1alpha1",
                namespace=self.namespace,
                plural="queries",
                name=query_name,
            )
            return query
        except ApiException as e:
            logger.error(f"Failed to get Query status: {e}")
            raise
    
    async def wait_for_query_completion(
        self, query_name: str, timeout: int = 300
    ) -> tuple[str, list[dict[str, Any]]]:
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            query = await self.get_query_status(query_name)
            status = query.get("status", {})
            phase = status.get("phase")
            
            if phase == "done":
                responses = status.get("responses", [])
                return "completed", responses
            elif phase == "error":
                return "failed", []
            
            await asyncio.sleep(2)
        
        return "timeout", []
    
    def parse_agent_response(
        self, agent_name: str, response_content: str
    ) -> CodeQualityReview | FunctionalityReview | None:
        try:
            json_start = response_content.find("{")
            json_end = response_content.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning(f"No JSON found in {agent_name} response")
                return None
            
            json_str = response_content[json_start:json_end]
            data = json.loads(json_str)
            
            if "code-quality" in agent_name.lower():
                return CodeQualityReview(**data)
            elif "functionality" in agent_name.lower():
                return FunctionalityReview(**data)
            
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse {agent_name} response: {e}")
            return None


import asyncio

