# QFA feature database AWS runbook

## Table

Default stack/table:

- Stack: `qfa-feature-database`
- Region: `us-west-2` unless `QFA_AWS_REGION` says otherwise
- Table: `qfa-feature-observations`
- Template: `infra/aws/qfa-feature-database.yaml`

The table uses DynamoDB pay-per-request billing, server-side encryption, point-in-time recovery, and CloudFormation retain policies to reduce accidental data loss.

## Deploy

```bash
export QFA_AWS_REGION=us-west-2
aws cloudformation deploy \
  --stack-name qfa-feature-database \
  --template-file infra/aws/qfa-feature-database.yaml \
  --parameter-overrides TableName=qfa-feature-observations \
  --region "$QFA_AWS_REGION"
```

## CLI runtime config

```bash
export QFA_FEATURE_BACKEND=dynamodb
export QFA_FEATURE_TABLE=qfa-feature-observations
export QFA_AWS_REGION=us-west-2
```

## Minimum normal-use IAM policy

Replace account/region/table if needed. The index ARN is required for cross-entity `qfa features query --name ...` calls.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeTable",
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-west-2:061039762362:table/qfa-feature-observations",
        "arn:aws:dynamodb:us-west-2:061039762362:table/qfa-feature-observations/index/FeatureTimestampIndex"
      ]
    }
  ]
}
```

Deployment through CloudFormation also requires stack permissions and DynamoDB create/update/delete/describe permissions. Current `devbot` access was verified but does not include DynamoDB `DescribeTable`, so live deployment is blocked until IAM is updated or the owner deploys the stack.

## Smoke test

```bash
qfa features put --backend dynamodb \
  --name news.sentiment.industry \
  --entity semiconductors \
  --timestamp 2026-07-01 \
  --value 0.55 \
  --metadata-json '{"keyword":"chips"}' \
  --source smoke

qfa features get --backend dynamodb \
  --name news.sentiment.industry \
  --entity semiconductors \
  --timestamp 2026-07-01
```
