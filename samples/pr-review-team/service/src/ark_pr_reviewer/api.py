import asyncio
import logging
import time
import uuid
from datetime import datetime, UTC

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from .ark_client import ARKClient
from .config import settings
from .github_client import GitHubClient
from .jira_client import JiraClient
from .models import (
    PRReviewRequest,
    PRReviewResponse,
    PRReviewResult,
    ReviewStatus,
)
from .s3_logger import S3Logger

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ARK PR Reviewer", version="0.1.0")

github_client = GitHubClient()
jira_client = JiraClient()
ark_client = ARKClient()
s3_logger = S3Logger()

review_counter = Counter("pr_reviews_total", "Total PR reviews", ["status"])
review_duration = Histogram("pr_review_duration_seconds", "PR review duration")
jira_success = Counter("jira_requests_total", "Jira API requests", ["status"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/review/pr", response_model=PRReviewResponse)
async def create_pr_review(
    request: PRReviewRequest, background_tasks: BackgroundTasks
) -> PRReviewResponse:
    review_id = str(uuid.uuid4())
    created_at = datetime.now(UTC)
    
    logger.info(f"Creating review {review_id} for PR {request.repository}#{request.pr_number}")
    
    background_tasks.add_task(
        process_pr_review,
        review_id,
        request,
        created_at,
    )
    
    return PRReviewResponse(
        review_id=review_id,
        status=ReviewStatus.PENDING,
        created_at=created_at,
        message=f"Review initiated for PR #{request.pr_number}",
    )


@app.get("/review/{review_id}", response_model=PRReviewResult)
async def get_review(review_id: str) -> PRReviewResult:
    logger.info(f"Fetching review {review_id}")
    
    raise HTTPException(
        status_code=501,
        detail="Review retrieval not yet implemented. Check S3 bucket for logs.",
    )


async def process_pr_review(
    review_id: str,
    request: PRReviewRequest,
    created_at: datetime,
) -> None:
    start_time = time.time()
    status = ReviewStatus.IN_PROGRESS
    error_msg = None
    
    try:
        pr_metadata = await github_client.get_pr_metadata(
            request.repository, request.pr_number
        )
        logger.info(f"Fetched PR metadata: {pr_metadata.title}")
        
        jira_key = jira_client.extract_jira_key(request.branch_name)
        jira_ticket = None
        
        if jira_key:
            try:
                jira_ticket = await jira_client.get_ticket(jira_key)
                if jira_ticket:
                    logger.info(f"Fetched Jira ticket: {jira_key}")
                    jira_success.labels(status="success").inc()
                else:
                    logger.warning(f"Jira ticket {jira_key} not found")
                    jira_success.labels(status="not_found").inc()
            except Exception as e:
                logger.error(f"Jira error: {e}")
                jira_success.labels(status="error").inc()
        else:
            logger.info("No Jira ticket in branch name (PROJ-000 or invalid format)")
        
        query_name = await ark_client.create_review_query(
            review_id, pr_metadata, jira_ticket
        )
        
        query_status, responses = await ark_client.wait_for_query_completion(
            query_name, timeout=settings.review_timeout
        )
        
        if query_status == "completed":
            status = ReviewStatus.COMPLETED
            logger.info(f"Review {review_id} completed successfully")
        elif query_status == "failed":
            status = ReviewStatus.FAILED
            error_msg = "ARK query failed"
            logger.error(f"Review {review_id} failed")
        else:
            status = ReviewStatus.FAILED
            error_msg = "Review timeout"
            logger.error(f"Review {review_id} timed out")
        
        code_quality = None
        functionality = None
        
        for response in responses:
            agent_name = response.get("target", {}).get("name", "")
            content = response.get("content", "")
            
            parsed = ark_client.parse_agent_response(agent_name, content)
            
            if parsed:
                from .models import CodeQualityReview, FunctionalityReview
                if isinstance(parsed, CodeQualityReview):
                    code_quality = parsed
                elif isinstance(parsed, FunctionalityReview):
                    functionality = parsed
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        result = PRReviewResult(
            review_id=review_id,
            repository=request.repository,
            pr_number=request.pr_number,
            branch_name=request.branch_name,
            jira_ticket=jira_key,
            status=status,
            code_quality=code_quality,
            functionality=functionality,
            execution_time_ms=execution_time_ms,
            created_at=created_at,
            completed_at=datetime.now(UTC),
            error=error_msg,
            ark_query_name=query_name,
        )
        
        await s3_logger.log_review(result)
        
        review_counter.labels(status=status.value).inc()
        review_duration.observe(execution_time_ms / 1000)
        
    except Exception as e:
        logger.exception(f"Error processing review {review_id}: {e}")
        status = ReviewStatus.FAILED
        error_msg = str(e)
        
        result = PRReviewResult(
            review_id=review_id,
            repository=request.repository,
            pr_number=request.pr_number,
            branch_name=request.branch_name,
            jira_ticket=None,
            status=status,
            execution_time_ms=int((time.time() - start_time) * 1000),
            created_at=created_at,
            completed_at=datetime.now(UTC),
            error=error_msg,
        )
        
        try:
            await s3_logger.log_review(result)
        except Exception as log_error:
            logger.error(f"Failed to log error review: {log_error}")
        
        review_counter.labels(status=status.value).inc()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)

