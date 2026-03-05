output "backend_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.backend.uri
}

output "oscal_bucket" {
  description = "GCS bucket for OSCAL outputs"
  value       = google_storage_bucket.oscal.name
}

output "diagrams_bucket" {
  description = "GCS bucket for architecture diagrams"
  value       = google_storage_bucket.diagrams.name
}

output "backend_service_account" {
  description = "Backend service account email"
  value       = google_service_account.backend.email
}

output "artifact_registry_url" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/compass"
}
