import boto3
from botocore.exceptions import BotoCoreError, ClientError

BUCKET_NAME = (
    "investment-portfolio-data-2026-unique-772325759101-us-east-2-an"
)


def test_s3_connection():
    session = boto3.Session(profile_name="investment-dev")
    s3 = session.client("s3", region_name="us-east-2")

    try:
        response = s3.list_objects_v2(
            Bucket=BUCKET_NAME,
            MaxKeys=10
        )

        print("Successfully connected to AWS S3!")

        for obj in response.get("Contents", []):
            print("File:", obj["Key"])

    except (ClientError, BotoCoreError) as error:
        print("AWS S3 connection failed:", error)


if __name__ == "__main__":
    test_s3_connection()