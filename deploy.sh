#!/bin/bash
set -e

# CareSync EC2 Deployment Script
AWS_REGION=${AWS_REGION:-"us-east-1"}
ECR_REGISTRY=${ECR_REGISTRY:-""}
IMAGE_TAG="latest"
CONTAINER_NAME="caresync-app"
ECR_REPOSITORY="caresync-stroke-app"

echo "=========================================="
echo " CareSync Deployment Started"
echo "=========================================="

if [ -z "$ECR_REGISTRY" ]; then
  echo "Error: ECR_REGISTRY environment variable is not set."
  exit 1
fi

echo "[1/4] Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

echo "[2/4] Pulling latest Docker image from ECR..."
docker pull $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

echo "[3/4] Restarting container..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

echo "[4/4] Launching updated container..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p 5000:5000 \
  -e S3_LOG_BUCKET="${S3_LOG_BUCKET:-caresync-session-logs}" \
  -e AWS_REGION="$AWS_REGION" \
  $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

echo "=========================================="
echo " Deployment Completed Successfully!"
echo "=========================================="
