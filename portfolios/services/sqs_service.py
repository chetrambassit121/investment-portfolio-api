import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

logger = logging.getLogger(__name__)

'''
    Boto3 connects to AWS SQS using your configured AWS credentials.
    Python creates a dictionary describing the import job.
    json.dumps() converts the dictionary into a JSON string.
    send_message() sends the message to SQS.
    AWS returns a unique message ID.
    Django logs the result.
'''


def send_portfolio_import_message():
    """
    Send a portfolio import job to AWS SQS.
    """

    sqs = boto3.client(
        "sqs",
        region_name=settings.AWS_REGION,
    )

    message = {
        "job_type": "import_portfolios",
        "source": "s3",
        "file": "portfolios.json",
    }

    try:
        response = sqs.send_message(
            QueueUrl=settings.AWS_SQS_QUEUE_URL,
            MessageBody=json.dumps(message),
        )

        message_id = response["MessageId"]

        logger.info(
            "Portfolio import job queued: message_id=%s",
            message_id,
        )

        return message_id

    except (ClientError, BotoCoreError):
        logger.exception(
            "Failed to send portfolio import job to SQS"
        )
        raise