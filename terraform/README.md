# Infrastructure (Terraform)

Provisions the AWS infrastructure the app runs on:

- **VPC** — 2 AZs, public + private subnets, single NAT gateway (cost-optimized for staging)
- **EKS** — managed Kubernetes cluster with a managed node group, IRSA enabled
- **RDS Postgres** — private-subnet database with an RDS-managed master password (no plaintext secrets in state)

## Usage

```bash
cd terraform
terraform init
terraform plan -var="environment=staging"
terraform apply -var="environment=staging"

# Point kubectl at the new cluster
$(terraform output -raw configure_kubectl)

# Then apply the Kubernetes manifests
kubectl apply -f ../k8s/
```

## Remote state

For anything beyond a personal demo, uncomment the `s3` backend block in `main.tf`
and create the bucket + DynamoDB lock table first:

```bash
aws s3api create-bucket --bucket task-manager-tfstate --region us-east-1
aws dynamodb create-table --table-name task-manager-tf-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

## Cost note

`t3.medium` nodes + `db.t3.micro` + a single NAT gateway run roughly $70-100/month
on AWS. Destroy the stack when you're done demoing it: `terraform destroy`.
