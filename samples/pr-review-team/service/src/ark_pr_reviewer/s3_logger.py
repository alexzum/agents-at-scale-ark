import json
import logging
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from .config import settings
from .models import PRReviewResult

logger = logging.getLogger(__name__)


class S3Logger:
    def __init__(self) -> None:
        self.s3_client = boto3.client("s3", region_name=settings.aws_region)
        self.bucket = settings.s3_bucket
        self.prefix = settings.s3_prefix
    
    async def log_review(self, review: PRReviewResult) -> str:
        key = f"{self.prefix}/{review.repository}/{review.pr_number}/{review.review_id}.json"
        
        review_data = review.model_dump(mode="json")
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=json.dumps(review_data, indent=2),
                ContentType="application/json",
                Metadata={
                    "review-id": review.review_id,
                    "pr-number": str(review.pr_number),
                    "status": review.status.value,
                    "created-at": review.created_at.isoformat(),
                },
            )
            logger.info(f"Logged review to S3: s3://{self.bucket}/{key}")
            return f"s3://{self.bucket}/{key}"
        except ClientError as e:
            logger.error(f"Failed to log review to S3: {e}")
            raise
    
    async def get_review(self, repository: str, pr_number: int, review_id: str) -> PRReviewResult | None:
        key = f"{self.prefix}/{repository}/{pr_number}/{review_id}.json"
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            data = json.loads(response["Body"].read())
            return PRReviewResult(**data)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning(f"Review not found in S3: {key}")
                return None
            logger.error(f"Failed to retrieve review from S3: {e}")
            raise

