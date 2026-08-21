import boto3


sts = boto3.client("sts")
identity = sts.get_caller_identity()
print(
    {
        "Account": identity["Account"],
        "Arn": identity["Arn"],
    }
)

s3 = boto3.client("s3")
s3.download_file(
    "mlops-wine-long-2026-320628059591",
    "models/latest/model.pkl",
    "/tmp/model.pkl",
)
print("S3 model download OK")
