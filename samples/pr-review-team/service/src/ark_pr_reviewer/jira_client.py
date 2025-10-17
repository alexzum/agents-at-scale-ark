import logging
import re
from typing import Any

import httpx

from .config import settings
from .models import JiraTicket

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(self) -> None:
        self.base_url = settings.jira_base_url.rstrip("/")
        self.timeout = settings.jira_timeout
        self.auth = None
        
        if settings.jira_username and settings.jira_api_token:
            self.auth = (settings.jira_username, settings.jira_api_token)
    
    def extract_jira_key(self, branch_name: str) -> str | None:
        match = re.search(r"\b([A-Z]+-\d+)\b", branch_name)
        if match:
            key = match.group(1)
            if key.endswith("-000"):
                return None
            return key
        return None
    
    async def get_ticket(self, ticket_key: str) -> JiraTicket | None:
        if not settings.jira_fallback_enabled:
            raise RuntimeError("Jira integration disabled")
        
        url = f"{self.base_url}/rest/api/3/issue/{ticket_key}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, auth=self.auth)
                
                if response.status_code == 404:
                    logger.warning(f"Jira ticket {ticket_key} not found")
                    return None
                
                if response.status_code == 401:
                    logger.error("Jira authentication failed")
                    raise RuntimeError("Jira authentication failed")
                
                response.raise_for_status()
                
                data = response.json()
                fields = data.get("fields", {})
                
                description = fields.get("description", "")
                if isinstance(description, dict):
                    description = self._extract_text_from_adf(description)
                
                custom_fields = {}
                for key, value in fields.items():
                    if key.startswith("customfield_"):
                        custom_fields[key] = value
                
                acceptance_criteria = None
                for key, value in custom_fields.items():
                    if value and isinstance(value, str) and "acceptance" in value.lower():
                        acceptance_criteria = value
                        break
                
                return JiraTicket(
                    key=ticket_key,
                    summary=fields.get("summary", ""),
                    description=description,
                    status=fields.get("status", {}).get("name", ""),
                    labels=fields.get("labels", []),
                    acceptance_criteria=acceptance_criteria,
                )
        
        except httpx.TimeoutException:
            logger.error(f"Jira request timeout for {ticket_key}")
            if not settings.jira_fallback_enabled:
                raise
            return None
        except httpx.HTTPError as e:
            logger.error(f"Jira HTTP error: {e}")
            if not settings.jira_fallback_enabled:
                raise
            return None
        except Exception as e:
            logger.error(f"Unexpected Jira error: {e}")
            if not settings.jira_fallback_enabled:
                raise
            return None
    
    def _extract_text_from_adf(self, adf: dict[str, Any]) -> str:
        if not isinstance(adf, dict):
            return str(adf)
        
        text_parts = []
        
        def extract(node: dict[str, Any]) -> None:
            if node.get("type") == "text":
                text_parts.append(node.get("text", ""))
            
            if "content" in node:
                for child in node["content"]:
                    extract(child)
        
        extract(adf)
        return " ".join(text_parts)

