"""A2ATask models for API responses."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class A2ATaskPart(BaseModel):
    """Part of an A2ATask artifact or message."""
    kind: str
    text: Optional[str] = None
    data: Optional[str] = None  # base64 encoded
    uri: Optional[str] = None
    mime_type: Optional[str] = None


class A2ATaskArtifact(BaseModel):
    """Artifact in an A2ATask."""
    artifact_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    parts: List[A2ATaskPart]
    metadata: Optional[Dict[str, str]] = None


class A2ATaskMessage(BaseModel):
    """Message in A2ATask history."""
    role: str
    parts: List[A2ATaskPart]
    metadata: Optional[Dict[str, str]] = None


class A2ATaskStatus(BaseModel):
    """Status message of an A2ATask."""
    state: str
    message: Optional[A2ATaskMessage] = None
    timestamp: Optional[datetime] = None


class A2ATaskTask(BaseModel):
    """Task details in A2ATask status."""
    id: str
    session_id: Optional[str] = None
    status: A2ATaskStatus
    artifacts: List[A2ATaskArtifact] = []
    history: List[A2ATaskMessage] = []
    metadata: Optional[Dict[str, str]] = None


class A2ATaskAssignedAgent(BaseModel):
    """Assigned agent information."""
    name: str
    namespace: str


class A2ATaskQueryRef(BaseModel):
    """Reference to the originating query."""
    name: str
    namespace: str


class A2ATaskResponse(BaseModel):
    """Response model for a single A2ATask."""
    name: str
    namespace: str
    task_id: str
    phase: str
    priority: int
    timeout: Optional[str] = None
    query_ref: Optional[A2ATaskQueryRef] = None
    assigned_agent: Optional[A2ATaskAssignedAgent] = None
    start_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    creation_timestamp: Optional[datetime] = None
    progress: Optional[int] = None


class A2ATaskDetailResponse(A2ATaskResponse):
    """Detailed response model for a single A2ATask with full task data."""
    task: Optional[A2ATaskTask] = None


class A2ATaskListResponse(BaseModel):
    """Response model for listing A2ATasks."""
    items: List[A2ATaskResponse]
    total: int


def a2atask_to_response(a2atask_dict: Dict[str, Any]) -> A2ATaskResponse:
    """Convert Kubernetes A2ATask dict to A2ATaskResponse."""
    metadata = a2atask_dict.get("metadata", {})
    spec = a2atask_dict.get("spec", {})
    status = a2atask_dict.get("status", {})
    
    # Parse timestamps
    creation_timestamp = None
    if "creationTimestamp" in metadata:
        creation_timestamp = datetime.fromisoformat(
            metadata["creationTimestamp"].replace("Z", "+00:00")
        )
    
    start_time = None
    if "startTime" in status:
        start_time = datetime.fromisoformat(
            status["startTime"].replace("Z", "+00:00")
        )
    
    completion_time = None
    if "completionTime" in status:
        completion_time = datetime.fromisoformat(
            status["completionTime"].replace("Z", "+00:00")
        )
    
    # Parse query ref
    query_ref = None
    if "queryRef" in spec:
        query_ref_data = spec["queryRef"]
        query_ref = A2ATaskQueryRef(
            name=query_ref_data.get("name", ""),
            namespace=query_ref_data.get("namespace", "")
        )
    
    # Parse assigned agent
    assigned_agent = None
    if "assignedAgent" in status:
        agent_data = status["assignedAgent"]
        assigned_agent = A2ATaskAssignedAgent(
            name=agent_data.get("name", ""),
            namespace=agent_data.get("namespace", "")
        )
    
    return A2ATaskResponse(
        name=metadata.get("name", ""),
        namespace=metadata.get("namespace", ""),
        task_id=spec.get("taskId", ""),
        phase=status.get("phase", ""),
        priority=spec.get("priority", 0),
        timeout=spec.get("timeout"),
        query_ref=query_ref,
        assigned_agent=assigned_agent,
        start_time=start_time,
        completion_time=completion_time,
        creation_timestamp=creation_timestamp,
        progress=status.get("progress")
    )


def a2atask_to_detail_response(a2atask_dict: Dict[str, Any]) -> A2ATaskDetailResponse:
    """Convert Kubernetes A2ATask dict to A2ATaskDetailResponse with full task data."""
    base_response = a2atask_to_response(a2atask_dict)
    
    # Convert to detail response
    detail_response = A2ATaskDetailResponse(**base_response.model_dump())
    
    # Parse task data if present
    status = a2atask_dict.get("status", {})
    if "task" in status:
        task_data = status["task"]
        
        # Parse artifacts
        artifacts = []
        for artifact_data in task_data.get("artifacts", []):
            parts = []
            for part_data in artifact_data.get("parts", []):
                part = A2ATaskPart(
                    kind=part_data.get("kind", "text"),
                    text=part_data.get("text"),
                    data=part_data.get("data"),
                    uri=part_data.get("uri"),
                    mime_type=part_data.get("mimeType")
                )
                parts.append(part)
            
            artifact = A2ATaskArtifact(
                artifact_id=artifact_data.get("artifactId", ""),
                name=artifact_data.get("name"),
                description=artifact_data.get("description"),
                parts=parts,
                metadata=artifact_data.get("metadata", {})
            )
            artifacts.append(artifact)
        
        # Parse history
        history = []
        for msg_data in task_data.get("history", []):
            parts = []
            for part_data in msg_data.get("parts", []):
                part = A2ATaskPart(
                    kind=part_data.get("kind", "text"),
                    text=part_data.get("text"),
                    data=part_data.get("data"),
                    uri=part_data.get("uri"),
                    mime_type=part_data.get("mimeType")
                )
                parts.append(part)
            
            message = A2ATaskMessage(
                role=msg_data.get("role", "agent"),
                parts=parts,
                metadata=msg_data.get("metadata", {})
            )
            history.append(message)
        
        # Parse status
        task_status_data = task_data.get("status", {})
        status_message = None
        if "message" in task_status_data:
            msg_data = task_status_data["message"]
            parts = []
            for part_data in msg_data.get("parts", []):
                part = A2ATaskPart(
                    kind=part_data.get("kind", "text"),
                    text=part_data.get("text"),
                    data=part_data.get("data"),
                    uri=part_data.get("uri"),
                    mime_type=part_data.get("mimeType")
                )
                parts.append(part)
            
            status_message = A2ATaskMessage(
                role=msg_data.get("role", "agent"),
                parts=parts,
                metadata=msg_data.get("metadata", {})
            )
        
        # Parse timestamp
        task_timestamp = None
        if "timestamp" in task_status_data:
            task_timestamp = datetime.fromisoformat(
                task_status_data["timestamp"].replace("Z", "+00:00")
            )
        
        task_status = A2ATaskStatus(
            state=task_status_data.get("state", ""),
            message=status_message,
            timestamp=task_timestamp
        )
        
        # Create task object
        task = A2ATaskTask(
            id=task_data.get("id", ""),
            session_id=task_data.get("sessionId"),
            status=task_status,
            artifacts=artifacts,
            history=history,
            metadata=task_data.get("metadata", {})
        )
        
        detail_response.task = task
    
    return detail_response