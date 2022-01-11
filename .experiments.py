import boto3
import os
from datetime import datetime, timedelta

# client = boto3.client(
#     "ec2",
#     region_name="us-east-2",
#     aws_access_key_id=os.getenv("AWS_AK"),
#     aws_secret_access_key=os.getenv("AWS_SAK"),
# )

# response = client.describe_instances(InstanceIds=[os.getenv("AWS_INSTANCE_ID")])
# instance_state = response.get("Reservations")[0].get("Instances")[0].get("State").get("Name")

# print(response)
# print("end")

cloudwatch_client = boto3.client(
    "cloudwatch",
    region_name="us-east-2",
    aws_access_key_id=os.getenv("AWS_AK"),
    aws_secret_access_key=os.getenv("AWS_SAK"),
)

response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": os.getenv("AWS_INSTANCE_ID")},],
            StartTime=datetime.utcnow() - timedelta(hours=1),
            EndTime=datetime.utcnow(),
            Period=60,  # one data point per minute, although free tier defaults to 1 per 5 minutes
            Statistics=["Average"],
            Unit="Percent",
        )

data_points = [p["Average"] for p in response["Datapoints"]]
print(response)
print(data_points)


import requests
import json
import os
def send_slack():
    headers = {
                "Content-type": "application/json",
            }

    comment = "Bruh 🤦🏼‍♂️ your EC2 is still running!"
    message = f"{comment} `cpu_util` = {42.0:.2}%"
    data = {"text": message}

    response = requests.post(
        os.getenv("SLACK_WEBHOOK_URL"), headers=headers, data=json.dumps(data)
    )

    print(response.text)