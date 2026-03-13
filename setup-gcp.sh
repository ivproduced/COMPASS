#!/usr/bin/env bash
# ============================================================
# COMPASS — GCP Infrastructure Setup via gcloud CLI
#
# This script provisions everything COMPASS needs:
#   1. Enables required GCP APIs
#   2. Creates Firestore database
#   3. Creates Cloud Storage buckets
#   4. Creates service account + IAM bindings
#   5. Creates Artifact Registry repository
#   6. (Optional) Deploys to Cloud Run
#
# Usage:
#   chmod +x setup-gcp.sh
#   ./setup-gcp.sh                    # Full setup
#   ./setup-gcp.sh --deploy           # Setup + build + deploy
#   ./setup-gcp.sh --status           # Check what exists
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - A GCP project created (or use the default below)
# ============================================================
set -euo pipefail

# ---- Configuration (edit these or set via environment) ----
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-compass-fedramp}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
SERVICE_ACCOUNT_NAME="compass-backend"
FIRESTORE_DB="compass"
BUCKET_OSCAL="${PROJECT_ID}-oscal"
BUCKET_DIAGRAMS="${PROJECT_ID}-diagrams"
AR_REPO="compass"
CLOUD_RUN_SERVICE="compass-backend"

# ---- Colors ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }
info() { echo -e "${CYAN}→${NC} $1"; }
err()  { echo -e "${RED}✗${NC} $1"; }

# ============================================================
# Pre-flight checks
# ============================================================
preflight() {
    echo ""
    echo "=========================================="
    echo " COMPASS — GCP Setup"
    echo "=========================================="
    echo ""

    # Check gcloud is available
    if ! command -v gcloud &>/dev/null; then
        err "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
        exit 1
    fi

    # Check authentication
    ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || true)
    if [[ -z "$ACCOUNT" ]]; then
        warn "Not authenticated. Running gcloud auth login..."
        gcloud auth login
        gcloud auth application-default login
    else
        log "Authenticated as: $ACCOUNT"
    fi

    # Set project
    info "Setting project to: $PROJECT_ID"
    gcloud config set project "$PROJECT_ID" 2>/dev/null

    # Verify project exists
    if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
        err "Project '$PROJECT_ID' not found. Create it first:"
        echo "    gcloud projects create $PROJECT_ID --name='COMPASS FedRAMP'"
        echo "    gcloud billing projects link $PROJECT_ID --billing-account=YOUR_BILLING_ACCOUNT"
        exit 1
    fi
    log "Project '$PROJECT_ID' exists"
    echo ""
}

# ============================================================
# 1. Enable APIs
# ============================================================
enable_apis() {
    info "Enabling required GCP APIs..."
    APIS=(
        "aiplatform.googleapis.com"           # Vertex AI (Gemini + Vector Search)
        "firestore.googleapis.com"            # Firestore
        "storage.googleapis.com"              # Cloud Storage
        "run.googleapis.com"                  # Cloud Run
        "cloudbuild.googleapis.com"           # Cloud Build
        "artifactregistry.googleapis.com"     # Artifact Registry
        "iam.googleapis.com"                  # IAM
        "generativelanguage.googleapis.com"   # Gemini API (non-Vertex)
    )

    for api in "${APIS[@]}"; do
        if gcloud services list --enabled --filter="name:$api" --format="value(name)" 2>/dev/null | grep -q "$api"; then
            log "API already enabled: $api"
        else
            gcloud services enable "$api" --quiet
            log "Enabled API: $api"
        fi
    done
    echo ""
}

# ============================================================
# 2. Firestore
# ============================================================
setup_firestore() {
    info "Setting up Firestore..."

    # Check if default database exists (Firestore needs at least the default first)
    if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q "(default)"; then
        log "Default Firestore database exists"
    else
        info "Creating default Firestore database..."
        gcloud firestore databases create --location="$REGION" --type=firestore-native --quiet 2>/dev/null || true
        log "Default Firestore database created"
    fi

    # Create the named 'compass' database
    if gcloud firestore databases list --format="value(name)" 2>/dev/null | grep -q "$FIRESTORE_DB"; then
        log "Firestore database '$FIRESTORE_DB' exists"
    else
        info "Creating Firestore database '$FIRESTORE_DB'..."
        gcloud firestore databases create \
            --database="$FIRESTORE_DB" \
            --location="$REGION" \
            --type=firestore-native \
            --quiet
        log "Firestore database '$FIRESTORE_DB' created"
    fi
    echo ""
}

# ============================================================
# 3. Cloud Storage buckets
# ============================================================
setup_storage() {
    info "Setting up Cloud Storage buckets..."

    for BUCKET in "$BUCKET_OSCAL" "$BUCKET_DIAGRAMS"; do
        if gcloud storage buckets describe "gs://$BUCKET" &>/dev/null 2>&1; then
            log "Bucket gs://$BUCKET exists"
        else
            gcloud storage buckets create "gs://$BUCKET" \
                --location="$REGION" \
                --uniform-bucket-level-access \
                --quiet
            log "Created bucket gs://$BUCKET"
        fi
    done

    # Set lifecycle: OSCAL docs expire after 1 year, diagrams after 90 days
    echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":365}}]}' | \
        gcloud storage buckets update "gs://$BUCKET_OSCAL" --lifecycle-file=/dev/stdin --quiet 2>/dev/null || true
    echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":90}}]}' | \
        gcloud storage buckets update "gs://$BUCKET_DIAGRAMS" --lifecycle-file=/dev/stdin --quiet 2>/dev/null || true

    echo ""
}

# ============================================================
# 4. Service Account + IAM
# ============================================================
setup_iam() {
    info "Setting up service account and IAM..."

    SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

    # Create service account
    if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null 2>&1; then
        log "Service account $SA_EMAIL exists"
    else
        gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
            --display-name="COMPASS Backend Service Account" \
            --quiet
        log "Created service account $SA_EMAIL"
    fi

    # Grant roles
    ROLES=(
        "roles/datastore.user"          # Firestore read/write
        "roles/storage.objectAdmin"     # GCS read/write/sign
        "roles/aiplatform.user"         # Vertex AI (Gemini + embeddings + Vector Search)
        "roles/run.invoker"             # Allow self-invocation if needed
    )

    for ROLE in "${ROLES[@]}"; do
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:$SA_EMAIL" \
            --role="$ROLE" \
            --quiet
        log "Granted $ROLE → $SA_EMAIL"
    done

    echo ""
    info "For local dev with this service account:"
    echo "    gcloud iam service-accounts keys create key.json \\"
    echo "      --iam-account=$SA_EMAIL"
    echo "    export GOOGLE_APPLICATION_CREDENTIALS=\$(pwd)/key.json"
    echo ""
}

# ============================================================
# 5. Artifact Registry
# ============================================================
setup_artifact_registry() {
    info "Setting up Artifact Registry..."

    if gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" &>/dev/null 2>&1; then
        log "Artifact Registry '$AR_REPO' exists"
    else
        gcloud artifacts repositories create "$AR_REPO" \
            --repository-format=docker \
            --location="$REGION" \
            --description="COMPASS container images" \
            --quiet
        log "Created Artifact Registry '$AR_REPO'"
    fi

    # Configure Docker auth
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet 2>/dev/null
    log "Docker auth configured for ${REGION}-docker.pkg.dev"
    echo ""
}

# ============================================================
# 6. (Optional) Build + Deploy to Cloud Run
# ============================================================
deploy() {
    info "Building and deploying to Cloud Run..."

    IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/compass-backend:latest"
    SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

    # Build with Cloud Build
    info "Submitting build to Cloud Build..."
    gcloud builds submit \
        --tag "$IMAGE" \
        --quiet

    log "Image built: $IMAGE"

    # Deploy to Cloud Run
    info "Deploying to Cloud Run..."
    gcloud run deploy "$CLOUD_RUN_SERVICE" \
        --image="$IMAGE" \
        --region="$REGION" \
        --platform=managed \
        --allow-unauthenticated \
        --port=8080 \
        --cpu=2 \
        --memory=2Gi \
        --min-instances=0 \
        --max-instances=10 \
        --concurrency=80 \
        --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID},ENV=production,FIRESTORE_DATABASE=${FIRESTORE_DB},GCS_BUCKET_OSCAL=${BUCKET_OSCAL}" \
        --service-account="$SA_EMAIL" \
        --quiet

    BACKEND_URL=$(gcloud run services describe "$CLOUD_RUN_SERVICE" \
        --region="$REGION" \
        --format="value(status.url)")

    echo ""
    log "Deployed to: $BACKEND_URL"
    log "Health check: ${BACKEND_URL}/health"
    log "Gemini check: ${BACKEND_URL}/health/gemini"
    echo ""
}

# ============================================================
# Status check
# ============================================================
status_check() {
    echo ""
    echo "=========================================="
    echo " COMPASS — GCP Resource Status"
    echo "=========================================="
    echo ""

    SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

    # Project
    info "Project: $PROJECT_ID"

    # APIs
    info "Enabled APIs:"
    for api in aiplatform firestore storage run cloudbuild artifactregistry generativelanguage; do
        if gcloud services list --enabled --filter="name:${api}" --format="value(name)" 2>/dev/null | grep -q "$api"; then
            log "  $api.googleapis.com"
        else
            warn "  $api.googleapis.com — NOT ENABLED"
        fi
    done

    # Firestore
    echo ""
    info "Firestore databases:"
    gcloud firestore databases list --format="table(name,type,locationId)" 2>/dev/null || warn "Cannot list databases"

    # Buckets
    echo ""
    info "Storage buckets:"
    for BUCKET in "$BUCKET_OSCAL" "$BUCKET_DIAGRAMS"; do
        if gcloud storage buckets describe "gs://$BUCKET" &>/dev/null 2>&1; then
            log "  gs://$BUCKET"
        else
            warn "  gs://$BUCKET — NOT FOUND"
        fi
    done

    # Service account
    echo ""
    info "Service account:"
    if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null 2>&1; then
        log "  $SA_EMAIL"
    else
        warn "  $SA_EMAIL — NOT FOUND"
    fi

    # Artifact Registry
    echo ""
    info "Artifact Registry:"
    if gcloud artifacts repositories describe "$AR_REPO" --location="$REGION" &>/dev/null 2>&1; then
        log "  ${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}"
    else
        warn "  '${AR_REPO}' — NOT FOUND"
    fi

    # Cloud Run
    echo ""
    info "Cloud Run:"
    if gcloud run services describe "$CLOUD_RUN_SERVICE" --region="$REGION" &>/dev/null 2>&1; then
        BACKEND_URL=$(gcloud run services describe "$CLOUD_RUN_SERVICE" --region="$REGION" --format="value(status.url)")
        log "  $CLOUD_RUN_SERVICE → $BACKEND_URL"
    else
        warn "  $CLOUD_RUN_SERVICE — NOT DEPLOYED"
    fi

    echo ""
}

# ============================================================
# Main
# ============================================================
case "${1:-}" in
    --status)
        preflight
        status_check
        ;;
    --deploy)
        preflight
        enable_apis
        setup_firestore
        setup_storage
        setup_iam
        setup_artifact_registry
        deploy
        echo "=========================================="
        echo " Setup + Deploy complete!"
        echo "=========================================="
        ;;
    *)
        preflight
        enable_apis
        setup_firestore
        setup_storage
        setup_iam
        setup_artifact_registry
        echo ""
        echo "=========================================="
        echo " Setup complete!"
        echo "=========================================="
        echo ""
        echo " Next steps:"
        echo "   1. For local dev with service account key:"
        echo "      gcloud iam service-accounts keys create key.json \\"
        echo "        --iam-account=${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
        echo "      export GOOGLE_APPLICATION_CREDENTIALS=\$(pwd)/key.json"
        echo ""
        echo "   2. Or authenticate directly:"
        echo "      gcloud auth application-default login"
        echo ""
        echo "   3. Run locally:"
        echo "      pip install -r requirements.txt"
        echo "      python -m uvicorn backend.app:app --reload --port 8080"
        echo ""
        echo "   4. Deploy when ready:"
        echo "      ./setup-gcp.sh --deploy"
        echo ""
        echo "   5. Check status anytime:"
        echo "      ./setup-gcp.sh --status"
        echo ""
        ;;
esac
