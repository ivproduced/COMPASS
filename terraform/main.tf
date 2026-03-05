# ============================================================
# COMPASS — Terraform Infrastructure
# Provisions all GCP resources required by the backend.
# ============================================================
terraform {
  required_version = ">= 1.7.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  backend "gcs" {
    bucket = "compass-fedramp-tfstate"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ---- Artifact Registry -----------------------------------------------
resource "google_artifact_registry_repository" "compass" {
  repository_id = "compass"
  format        = "DOCKER"
  location      = var.region
  description   = "COMPASS container images"
}

# ---- Cloud Run Service -----------------------------------------------
resource "google_cloud_run_v2_service" "backend" {
  name     = "compass-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/compass/compass-backend:latest"

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      env {
        name  = "ENV"
        value = "production"
      }

      ports {
        container_port = 8080
      }
    }
  }
}

# Allow unauthenticated (public demo)
resource "google_cloud_run_v2_service_iam_member" "allUsers" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# ---- Service Account -------------------------------------------------
resource "google_service_account" "backend" {
  account_id   = "compass-backend"
  display_name = "COMPASS Backend Service Account"
}

resource "google_project_iam_member" "firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "vertex_ai" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

# ---- GCS Buckets -----------------------------------------------------
resource "google_storage_bucket" "oscal" {
  name                        = "${var.project_id}-oscal"
  location                    = var.region
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition { age = 365 }
    action { type = "Delete" }
  }
}

resource "google_storage_bucket" "diagrams" {
  name                        = "${var.project_id}-diagrams"
  location                    = var.region
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition { age = 90 }
    action { type = "Delete" }
  }
}

resource "google_storage_bucket" "tfstate" {
  name                        = "${var.project_id}-tfstate"
  location                    = var.region
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

# ---- Firestore -------------------------------------------------------
resource "google_firestore_database" "compass" {
  name        = "compass"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# ---- Vertex AI Vector Search -----------------------------------------
# NOTE: Index creation takes 30-90 minutes. Manage separately if needed.
resource "google_vertex_ai_index" "controls" {
  region       = var.region
  display_name = "compass-controls-index"

  metadata {
    contents_delta_uri = "gs://${var.project_id}-oscal/vector-index/"
    config {
      dimensions                  = 768
      approximate_neighbors_count = 10
      distance_measure_type       = "COSINE_DISTANCE"
      algorithm_config {
        tree_ah_config {}
      }
    }
  }
  index_update_method = "BATCH_UPDATE"
}
