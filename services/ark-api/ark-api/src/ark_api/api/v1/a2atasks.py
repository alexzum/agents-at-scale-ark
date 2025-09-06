"""A2ATask API endpoints."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from kubernetes_asyncio import client
from kubernetes_asyncio.client.api_client import ApiClient
from kubernetes_asyncio.client.rest import ApiException

from ...models.a2atasks import (
    A2ATaskListResponse, 
    A2ATaskDetailResponse, 
    a2atask_to_response, 
    a2atask_to_detail_response
)
from .exceptions import handle_k8s_errors

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/namespaces/{namespace}/a2atasks", tags=["a2atasks"])


def _matches_phase_filter(a2atask_dict: dict, phase_filter: Optional[str]) -> bool:
    """Check if A2ATask matches phase filter."""
    if not phase_filter:
        return True
    status = a2atask_dict.get("status", {})
    return status.get("phase") == phase_filter


def _matches_agent_filter(a2atask_dict: dict, agent_filter: Optional[str]) -> bool:
    """Check if A2ATask matches agent filter."""
    if not agent_filter:
        return True
    # Check assigned agent
    status = a2atask_dict.get("status", {})
    assigned_agent = status.get("assignedAgent", {})
    agent_name = assigned_agent.get("name", "")
    
    # Also check labels for agent name
    metadata = a2atask_dict.get("metadata", {})
    labels = metadata.get("labels", {})
    label_agent = labels.get("ark.mckinsey.com/agent", "")
    
    return (agent_filter.lower() in agent_name.lower() or 
            agent_filter.lower() in label_agent.lower())


def _matches_task_id_filter(a2atask_dict: dict, task_id_filter: Optional[str]) -> bool:
    """Check if A2ATask matches task ID filter."""
    if not task_id_filter:
        return True
    spec = a2atask_dict.get("spec", {})
    task_id = spec.get("taskId", "")
    return task_id_filter.lower() in task_id.lower()


def _should_include_a2atask(a2atask_dict: dict, phase_filter: Optional[str], 
                           agent_filter: Optional[str], task_id_filter: Optional[str]) -> bool:
    """Check if A2ATask should be included based on all filters."""
    return (_matches_phase_filter(a2atask_dict, phase_filter) and
            _matches_agent_filter(a2atask_dict, agent_filter) and
            _matches_task_id_filter(a2atask_dict, task_id_filter))


def _paginate_a2atasks(a2atasks: list, page_num: int, limit_num: int) -> tuple[list, int]:
    """Apply pagination to A2ATasks list and return paginated items with total count."""
    total_count = len(a2atasks)
    start_index = (page_num - 1) * limit_num
    end_index = start_index + limit_num
    paginated_a2atasks = a2atasks[start_index:end_index]
    return paginated_a2atasks, total_count


@router.get("", response_model=A2ATaskListResponse)
@handle_k8s_errors(operation="list", resource_type="a2atask")
async def list_a2atasks(
    namespace: str,
    phase: Optional[str] = Query(None, description="Filter by task phase (assigned, running, completed, failed, cancelled)"),
    agent: Optional[str] = Query(None, description="Filter by agent name"),
    task_id: Optional[str] = Query(None, alias="taskId", description="Filter by task ID"),
    limit: Optional[int] = Query(200, description="Maximum number of A2ATasks to return"),
    page: Optional[int] = Query(1, description="Page number for pagination (1-based)")
) -> A2ATaskListResponse:
    """
    List all A2ATasks in a namespace with optional filtering.
    
    Args:
        namespace: The namespace to list A2ATasks from
        phase: Filter by task phase (assigned, running, completed, failed, cancelled)
        agent: Filter by agent name
        task_id: Filter by task ID
        limit: Maximum number of A2ATasks to return (default: 200)
        page: Page number for pagination (1-based, default: 1)
        
    Returns:
        A2ATaskListResponse: List of A2ATasks in the namespace
    """
    async with ApiClient() as api_client:
        # Create custom objects API client
        custom_api = client.CustomObjectsApi(api_client)
        
        try:
            page_num = page or 1
            limit_num = limit or 200
            
            # List A2ATasks using custom resource API
            result = await custom_api.list_namespaced_custom_object(
                group="ark.mckinsey.com",
                version="v1alpha1",
                namespace=namespace,
                plural="a2atasks"
            )
            
            filtered_a2atasks = []
            for item in result.get("items", []):
                if _should_include_a2atask(item, phase, agent, task_id):
                    filtered_a2atasks.append(a2atask_to_response(item))
            
            # Sort by creation timestamp, newest first
            filtered_a2atasks.sort(key=lambda x: x.creation_timestamp or datetime.min, reverse=True)
            
            paginated_a2atasks, total_count = _paginate_a2atasks(filtered_a2atasks, page_num, limit_num)
            
            return A2ATaskListResponse(
                items=paginated_a2atasks,
                total=total_count
            )
            
        except ApiException as e:
            logger.error(f"Failed to list A2ATasks: {e}")
            raise


@router.get("/{a2atask_name}", response_model=A2ATaskDetailResponse)
@handle_k8s_errors(operation="get", resource_type="a2atask")
async def get_a2atask(
    namespace: str,
    a2atask_name: str
) -> A2ATaskDetailResponse:
    """
    Get a specific A2ATask by name with full details including history and artifacts.
    
    Args:
        namespace: The namespace containing the A2ATask
        a2atask_name: The name of the A2ATask to retrieve
        
    Returns:
        A2ATaskDetailResponse: The requested A2ATask with full details
    """
    async with ApiClient() as api_client:
        # Create custom objects API client
        custom_api = client.CustomObjectsApi(api_client)
        
        try:
            # Get the specific A2ATask
            result = await custom_api.get_namespaced_custom_object(
                group="ark.mckinsey.com",
                version="v1alpha1",
                namespace=namespace,
                plural="a2atasks",
                name=a2atask_name
            )
            
            # Convert to detailed response
            return a2atask_to_detail_response(result)
            
        except ApiException as e:
            logger.error(f"Failed to get A2ATask {a2atask_name}: {e}")
            raise