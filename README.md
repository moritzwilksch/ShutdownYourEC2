# Shut Down Your EC2 💸🤦🏼‍♂️
A deamon that periodically checks for EC2 instances that someone (aka. me) forgot to shut down.

### Environment Variables
| Variable | Notes |
| :---: | --- |
| `AWS_AK` | Your AWS Access Key ID |
| `AWS_SAK` | Your AWS Secret Access Key |
|`SLACK_WEBHOOK_URL` | URL of your Slack App to send notifications |
|`AWS_INSTANCE_ID` | ID of the AWS EC2 Instance to periodically check |
