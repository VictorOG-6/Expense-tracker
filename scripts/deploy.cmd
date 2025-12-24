@echo off
setlocal enabledelayedexpansion

:: Configuration
set IMAGE_NAME=%1
set TAG=%2
if "%TAG%"=="" set TAG=latest
if "%REGISTRY%"=="" set REGISTRY=myregistry
set MAX_RETRIES=3

:: Color codes (limited in CMD, using echo for visual separation)
set "LINE========================================================================"

:: Functions implemented via GOTO

:main
echo %LINE%
echo [INFO] Starting deployment for %IMAGE_NAME%:%TAG%
echo %LINE%

call :check_requirements
if errorlevel 1 exit /b 1

call :check_image_exists
if errorlevel 1 exit /b 1

call :tag_image
if errorlevel 1 exit /b 1

call :push_image
if errorlevel 1 exit /b 1

call :verify_push

echo %LINE%
echo [SUCCESS] Deployment completed successfully!
echo [INFO] Image: %REGISTRY%/%IMAGE_NAME%:%TAG%
echo %LINE%
exit /b 0

:check_requirements
echo [INFO] Checking requirements...

where docker >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

if "%IMAGE_NAME%"=="" (
    echo [ERROR] Image name not provided
    echo Usage: deploy.cmd ^<image_name^> [tag]
    exit /b 1
)

echo [SUCCESS] Requirements check passed
exit /b 0

:check_image_exists
echo [INFO] Checking if image %IMAGE_NAME%:%TAG% exists...

docker image inspect %IMAGE_NAME%:%TAG% >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Image %IMAGE_NAME%:%TAG% not found
    echo [INFO] Please build the image first: make build
    exit /b 1
)

echo [SUCCESS] Image found
exit /b 0

:tag_image
set FULL_TAG=%REGISTRY%/%IMAGE_NAME%:%TAG%
echo [INFO] Tagging image as %FULL_TAG%...

docker tag %IMAGE_NAME%:%TAG% %FULL_TAG%
if errorlevel 1 (
    echo [ERROR] Failed to tag image
    exit /b 1
)

echo [SUCCESS] Image tagged successfully
exit /b 0

:push_image
set FULL_TAG=%REGISTRY%/%IMAGE_NAME%:%TAG%
echo [INFO] Pushing %FULL_TAG% to registry...

set attempt=1
:push_loop
docker push %FULL_TAG%
if not errorlevel 1 (
    echo [SUCCESS] Image pushed successfully
    exit /b 0
)

echo [WARNING] Push attempt %attempt%/%MAX_RETRIES% failed

set /a attempt+=1
if %attempt% leq %MAX_RETRIES% (
    echo [INFO] Retrying in 5 seconds...
    timeout /t 5 /nobreak >nul
    goto :push_loop
)

echo [ERROR] Failed to push image after %MAX_RETRIES% attempts
exit /b 1

:verify_push
set FULL_TAG=%REGISTRY%/%IMAGE_NAME%:%TAG%
echo [INFO] Verifying pushed image...

docker manifest inspect %FULL_TAG% >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Could not verify image in registry
) else (
    echo [SUCCESS] Image verified in registry
)
exit /b 0

:cleanup
echo [INFO] Cleaning up local tagged images...
set FULL_TAG=%REGISTRY%/%IMAGE_NAME%:%TAG%
docker rmi %FULL_TAG% 2>nul
exit /b 0