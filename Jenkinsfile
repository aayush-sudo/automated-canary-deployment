
pipeline {
    agent any

    parameters {
        string(
            name: 'CANARY_IMAGE',
            defaultValue: 'canary-demo:v2',
            description: 'Container image to deploy through the Flagger-managed canary'
        )
    }

    options {
        timestamps()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Repository') {
            steps {
                echo 'Repository checkout completed.'

                powershell '''
                    Write-Host "Jenkins workspace:"
                    Get-Location

                    Write-Host "Repository files:"
                    Get-ChildItem -Force
                '''
            }
        }

        stage('Check Build Environment') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    $env:KUBECONFIG = "C:\\Users\\hp\\.kube\\config"

                    $docker = "C:\\Users\\hp\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe"
                    $kubectl = "C:\\Windows\\System32\\kubectl\\kubectl.exe"
                    $minikube = "C:\\Program Files\\Kubernetes\\Minikube\\minikube.exe"
                    $helm = "C:\\Users\\hp\\AppData\\Local\\Microsoft\\WinGet\\Links\\helm.exe"

                    Write-Host "Agent identity:"
                    whoami

                    Write-Host "`nGit:"
                    git --version

                    Write-Host "`nDocker client and server:"
                    & $docker version
                    if ($LASTEXITCODE -ne 0) {
                        throw "Jenkins cannot connect to Docker."
                    }

                    Write-Host "`nKubernetes client:"
                    & $kubectl version --client
                    if ($LASTEXITCODE -ne 0) {
                        throw "kubectl is unavailable."
                    }

                    Write-Host "`nMinikube:"
                    & $minikube version
                    if ($LASTEXITCODE -ne 0) {
                        throw "Minikube executable is unavailable."
                    }

                    Write-Host "`nHelm:"
                    & $helm version
                    if ($LASTEXITCODE -ne 0) {
                        throw "Helm is unavailable."
                    }

                    Write-Host "`nKubernetes context:"
                    & $kubectl config current-context
                    if ($LASTEXITCODE -ne 0) {
                        throw "Could not read Kubernetes context."
                    }

                    Write-Host "`nKubernetes nodes:"
                    & $kubectl get nodes
                    if ($LASTEXITCODE -ne 0) {
                        throw "Jenkins cannot access Kubernetes."
                    }
                '''
            }
        }

        stage('Deployment Preflight') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    $env:KUBECONFIG = "C:\\Users\\hp\\.kube\\config"
                    $kubectl = "C:\\Windows\\System32\\kubectl\\kubectl.exe"

                    Write-Host "Checking Flagger canary..."
                    & $kubectl get canary canary-demo-flagger -n default
                    if ($LASTEXITCODE -ne 0) {
                        throw "Required Flagger canary was not found."
                    }

                    Write-Host "Checking Flagger controller..."
                    & $kubectl get deployment flagger -n istio-system
                    if ($LASTEXITCODE -ne 0) {
                        throw "Flagger controller is unavailable."
                    }

                    Write-Host "Checking Flagger-managed services..."
                    & $kubectl get services canary-demo-flagger canary-demo-flagger-primary canary-demo-flagger-canary -n default
                    if ($LASTEXITCODE -ne 0) {
                        throw "One or more required Flagger services are missing."
                    }

                    Write-Host "Deployment preflight passed. No resources were changed."
                '''
            }
        }

        stage('Validate Canary Image') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    $env:KUBECONFIG = "C:\\Users\\hp\\.kube\\config"

                    $kubectl = "C:\\Windows\\System32\\kubectl\\kubectl.exe"
                    $requestedImage = "$env:CANARY_IMAGE"

                    if ([string]::IsNullOrWhiteSpace($requestedImage)) {
                        throw "CANARY_IMAGE must not be empty."
                    }

                    Write-Host "Requested image: $requestedImage"

                    Write-Host "Reading current Flagger target image..."
                    $currentImage = & $kubectl get deployment canary-demo-flagger `
                        -n default `
                        -o "jsonpath={.spec.template.spec.containers[0].image}"

                    if ($LASTEXITCODE -ne 0 -or
                        [string]::IsNullOrWhiteSpace(($currentImage -join ""))) {
                        throw "Could not read the Flagger target image."
                    }

                    $currentImage = ($currentImage -join "").Trim()
                    Write-Host "Current target image: $currentImage"

                    Write-Host "Validating against existing application deployments..."

                    $knownImage = $false

                    foreach ($deployment in @("canary-demo-v1", "canary-demo-v2")) {
                        $image = & $kubectl get deployment $deployment `
                            -n default `
                            -o "jsonpath={.spec.template.spec.containers[0].image}"

                        if ($LASTEXITCODE -ne 0) {
                            throw "Could not inspect deployment $deployment."
                        }

                        $image = ($image -join "").Trim()

                        if ($image -ne $requestedImage) {
                            continue
                        }

                        $ready = & $kubectl get deployment $deployment `
                            -n default `
                            -o "jsonpath={.status.readyReplicas}"

                        if ($LASTEXITCODE -ne 0) {
                            throw "Could not check readiness for $deployment."
                        }

                        $replicas = & $kubectl get deployment $deployment `
                            -n default `
                            -o "jsonpath={.spec.replicas}"

                        if ($LASTEXITCODE -ne 0) {
                            throw "Could not read replica count for $deployment."
                        }

                        if ([int]($ready -join "0") -lt 1 -or
                            [int]($replicas -join "0") -lt 1) {
                            throw "Image '$requestedImage' matches $deployment, but it has no ready replica."
                        }

                        Write-Host "Image matches deployment: $deployment"
                        Write-Host "Ready replicas: $ready / $replicas"
                        $knownImage = $true
                        break
                    }

                    if (-not $knownImage) {
                        throw "Image '$requestedImage' does not match a validated v1 or v2 application deployment."
                    }

                    if ($requestedImage -eq $currentImage) {
                        Write-Host "Requested image already matches the Flagger target."
                        Write-Host "No rollout is needed."
                    } else {
                        Write-Host "Image matches a ready application deployment."
                        Write-Host "Ready for a separate controlled deployment stage."
                    }

                    Write-Host "Image validation passed. No resources were changed."
                '''
            }
        }
    }

    post {
        success {
            echo 'Jenkins validation pipeline passed.'
        }

        failure {
            echo 'Jenkins pipeline failed. Check Console Output.'
        }
    }
}
