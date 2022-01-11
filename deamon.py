#%%
import boto3
import os
from datetime import datetime, timedelta
from prefect import Flow, case, task
from prefect.tasks.control_flow import merge
from prefect.core.task import Task
from prefect.schedules import Schedule
from prefect.schedules.clocks import IntervalClock
import requests
import json
import random

COMMENTS = [
    "Did you forget your EC2 instance again? 🙄",
    "Bruh 🤦🏼‍♂️ your EC2 is still running!",
    "You stupid? EC2 is still running... 🙀",
    "Oh my god!!! If I'll have to remind you ONE MORE TIME.... 😤",
    "Just turn off your EC2 already 🙄",
    "Not again... 😒"
    "You're a bad person.",
    "You're the WORST!",
    "Guess what... 💸",
    "Guess what you are! An 🍞🙎🏼‍♂️🍞!"
]


cloudwatch_client = boto3.client(
    "cloudwatch",
    region_name="us-east-2",
    aws_access_key_id=os.getenv("AWS_AK"),
    aws_secret_access_key=os.getenv("AWS_SAK"),
)

ec2_client = boto3.client(
    "ec2",
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

        if len(data_points) < 6:
            self.logger.info("Returning cpu_util = 9999")
            return 9999  # machine just started < 30 min ago.

        avg_of_data_points = sum(data_points) / len(data_points)

        self.logger.info(f"Returning cpu_util = {avg_of_data_points}")
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

        comment = random.choice(COMMENTS)
        message = f"{comment} `cpu_util` = {util:.2}%"
        data = {"text": message}

        response = requests.post(
            os.getenv("SLACK_WEBHOOK_URL"), headers=headers, data=json.dumps(data)
        )

        print(response.text)


class EC2StateChecker(Task):
    def __init__(self, client, instance_id):
        super().__init__()
        self.client = client
        self.instance_id = instance_id

    def run(self):
        response = self.client.describe_instances(InstanceIds=[self.instance_id])
        instance_state = (
            response.get("Reservations")[0].get("Instances")[0].get("State").get("Name")
        )
        self.logger.info(f"Instance state: {instance_state}")
        print(instance_state)
        return instance_state == "stopped"


@task
def cpu_util_below_threshold(util, thresh):
    return util < thresh


# ---------------------------- Flow Definition ----------------------------
ec2_state_checker_task = EC2StateChecker(
    client=ec2_client, instance_id=os.getenv("AWS_INSTANCE_ID")
)
check_cpu_task = CloudWatchChecker(
    client=cloudwatch_client, instance_id=os.getenv("AWS_INSTANCE_ID")
)
notify_slack_task = SlackNotifier()

schedule = Schedule(clocks=[IntervalClock(interval=timedelta(minutes=5))])

#%%

with Flow("CloudWatchChecker", schedule=schedule) as f:
    instance_state_stopped = ec2_state_checker_task()

    with case(instance_state_stopped, False):
        cpu_util_avg = check_cpu_task()

        with case(cpu_util_below_threshold(cpu_util_avg, 1), True):
            _ = notify_slack_task(util=cpu_util_avg)


f.run()
