"""Sessions API endpoints."""
import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from ark_sdk.client import with_ark_client

from ...models.sessions import SessionResponse, SessionListResponse
from ...utils.memory_client import (
    get_memory_service_address,
    fetch_memory_service_data,
    get_all_memory_resources
)
from .exceptions import handle_k8s_errors

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/sessions", tags=["sessions"])

# CRD configuration
VERSION = "v1alpha1"


@router.get("", response_model=SessionListResponse)
@handle_k8s_errors(operation="list", resource_type="sessions")
async def list_sessions(
    namespace: Optional[str] = Query(None, description="Namespace for this request (defaults to current context)"),
    memory: Optional[str] = Query(None, description="Filter by memory name")
) -> SessionListResponse:
    """List all sessions in a namespace, optionally filtered by memory."""
    async with with_ark_client(namespace, VERSION) as client:
        memory_dicts = await get_all_memory_resources(client, memory)
        
        all_sessions = []
        
        for memory_dict in memory_dicts:
            memory_name = memory_dict.get("metadata", {}).get("name", "")
            
            try:
                service_url = get_memory_service_address(memory_dict)
                
                data = await fetch_memory_service_data(
                    service_url,
                    "/sessions", 
                    memory_name=memory_name
                )
                
                sessions = data.get("sessions", [])
                
                # Handle null sessions (empty database)
                if sessions is None:
                    sessions = []
                
                # Convert to our response format - only include actual data
                for session_id in sessions:
                    all_sessions.append(SessionResponse(
                        sessionId=session_id,
                        memoryName=memory_name
                    ))
                        
            except Exception as e:
                logger.error(f"Failed to get sessions from memory {memory_name}: {e}")
                # Continue processing other memories
                continue
        
        return SessionListResponse(
            items=all_sessions,
            total=len(all_sessions)
        )


@router.delete("/{session_id}")
@handle_k8s_errors(operation="delete", resource_type="session")
async def delete_session(
    session_id: str,
    namespace: Optional[str] = Query(None, description="Namespace for this request (defaults to current context)")
) -> dict:
    """Delete a specific session and all its messages."""
    async with with_ark_client(namespace, VERSION) as client:
        memory_dicts = await get_all_memory_resources(client)
        
        deleted_count = 0
        
        for memory_dict in memory_dicts:
            memory_name = memory_dict.get("metadata", {}).get("name", "")
            
            try:
                service_url = get_memory_service_address(memory_dict)
                
                # Make DELETE request to memory service
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.delete(
                        f"{service_url}/sessions/{session_id}",
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        deleted_count += 1
                    elif response.status_code != 404:  # 404 is OK if session doesn't exist
                        logger.warning(f"Failed to delete session {session_id} from memory {memory_name}: {response.status_code}")
                        
            except Exception as e:
                logger.error(f"Failed to delete session {session_id} from memory {memory_name}: {e}")
                continue
        
        return {"message": f"Session {session_id} deleted successfully"}


@router.delete("")
@handle_k8s_errors(operation="delete", resource_type="sessions")
async def delete_all_sessions(
    namespace: Optional[str] = Query(None, description="Namespace for this request (defaults to current context)")
) -> dict:
    """Delete all sessions and their messages."""
    async with with_ark_client(namespace, VERSION) as client:
        memory_dicts = await get_all_memory_resources(client)
        
        deleted_count = 0
        
        for memory_dict in memory_dicts:
            memory_name = memory_dict.get("metadata", {}).get("name", "")
            
            try:
                service_url = get_memory_service_address(memory_dict)
                
                # Make DELETE request to memory service
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.delete(
                        f"{service_url}/sessions",
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        deleted_count += 1
                        
            except Exception as e:
                logger.error(f"Failed to delete all sessions from memory {memory_name}: {e}")
                continue
        
        return {"message": f"All sessions deleted successfully from {deleted_count} memory services"}


@router.delete("/{session_id}/queries/{query_id}/messages")
@handle_k8s_errors(operation="delete", resource_type="query_messages")
async def delete_query_messages(
    session_id: str,
    query_id: str,
    namespace: Optional[str] = Query(None, description="Namespace for this request (defaults to current context)")
) -> dict:
    """Delete messages for a specific query within a session."""
    async with with_ark_client(namespace, VERSION) as client:
        memory_dicts = await get_all_memory_resources(client)
        
        deleted_count = 0
        
        for memory_dict in memory_dicts:
            memory_name = memory_dict.get("metadata", {}).get("name", "")
            
            try:
                service_url = get_memory_service_address(memory_dict)
                
                # Make DELETE request to memory service
                async with httpx.AsyncClient() as http_client:
                    response = await http_client.delete(
                        f"{service_url}/sessions/{session_id}/queries/{query_id}/messages",
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        deleted_count += 1
                    elif response.status_code != 404:  # 404 is OK if query doesn't exist
                        logger.warning(f"Failed to delete query {query_id} messages from session {session_id} in memory {memory_name}: {response.status_code}")
                        
            except Exception as e:
                logger.error(f"Failed to delete query {query_id} messages from session {session_id} in memory {memory_name}: {e}")
                continue
        
        return {"message": f"Query {query_id} messages deleted successfully from session {session_id}"}