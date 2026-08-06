output "cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "configure_kubectl" {
  description = "Run this to point kubectl at the new cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

output "db_endpoint" {
  description = "RDS Postgres endpoint (connect via the app's DATABASE_URL secret, not directly)"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}
