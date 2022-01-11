import boto3
import os
from datetime import datetime, timedelta
from prefect import Flow, case
from prefect.core.task import Task
from prefect.schedules import Schedule
from prefect.schedules.clocks import IntervalClock
import requests
import json

client = boto3.client(
    "cloudwatch",
    region_name="us-east-2",
    aws_access_key_id=os.getenv("AWS_AK"),
    aws_secret_access_key=os.getenv("AWS_SAK"),
)


class CloudWatchChecker(Task):
    def __init__(self, client, instance_id):
        super().__init__()
        self.client = client
        self.instance_id = instance_id

    def get_cpu_util(self, start_time, end_time):
        response = self.client.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": self.instance_id},],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,  # one data point per minute, although free tier defaults to 1 per 5 minutes
            Statistics=["Average"],
            Unit="Percent",
        )

        data_points = [p["Average"] for p in response["Datapoints"]]
        avg_of_data_points = sum(data_points) / len(data_points)

        print(f"AVG = {avg_of_data_points}")
        return avg_of_data_points

    def run(self):
        return self.get_cpu_util(
            start_time=datetime.utcnow() - timedelta(hours=1), end_time=datetime.utcnow(),
        )


class SlackNotifier(Task):
    def run(self, util):
        headers = {
            "Content-type": "application/json",
        }

        message = f"Did you forget your EC2 instance again? 🙄 `cpu_util` = {util:.2}%"
        data = {"text": message}

        response = requests.post(
            os.getenv("SLACK_WEBHOOK_URL"), headers=headers, data=json.dumps(data)
        )

        print(response.text)


# ---------------------------- Flow Definition ----------------------------
check_cpu_task = CloudWatchChecker(client=client, instance_id=os.getenv("AWS_INSTANCE_ID"))
notify_slack_task = SlackNotifier()

schedule = Schedule(clocks=[IntervalClock(interval=timedelta(seconds=5))])

with Flow("CloudWatchChecker", schedule=schedule) as f:
    cpu_util_avg = check_cpu_task()

    with case(cpu_util_avg < 1, True):
        _ = notify_slack_task(util=cpu_util_avg)
    
    with case(cpu_util_avg >= 1, True):
        _ = notify_slack_task(util=cpu_util_avg)


f.run()
