#!/bin/sh
set -e

IMAGE_NAME="$1"
TAG="$2"

echo "Deploying $IMAGE_NAME:$TAG on Unix..."

docker tag "$IMAGE_NAME:$TAG" "myregistry/$IMAGE_NAME:$TAG"
docker push "myregistry/$IMAGE_NAME:$TAG"

echo "Deployment successful"