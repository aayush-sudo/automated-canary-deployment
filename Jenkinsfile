
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

                script {
                    if (isUnix()) {
                        sh 'pwd'
                        sh 'ls -la'
                    } else {
                        powershell '''
                            Write-Host "Jenkins workspace:"
                            Get-Location

                            Write-Host "Repository files:"
                            Get-ChildItem -Force
                        '''
                    }
                }
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
                        throw "Jenkins cannot connect to the Docker engine."
                    }

                    Write-Host "`nKubernetes client:"
                    & $kubectl version --client

                    Write-Host "`nMinikube:"
                    & $minikube version

                    Write-Host "`nHelm:"
                    & $helm version

                    Write-Host "`nKubernetes context:"
                    & $kubectl config current-context

                    Write-Host "`nKubernetes nodes:"
                    & $kubectl get nodes

                    if ($LASTEXITCODE -ne 0) {
                        throw "Jenkins cannot access the Kubernetes cluster."
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

                    Write-Host "Checking existing Flagger canary..."
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
                    $minikube = "C:\\Program Files\\Kubernetes\\Minikube\\minikube.exe"
                    $requestedImage = "$env:CANARY_IMAGE"

                    if ([string]::IsNullOrWhiteSpace($requestedImage)) {
                        throw "CANARY_IMAGE must not be empty."
                    }

                    Write-Host "Requested image: $requestedImage"

                    Write-Host "Reading current Flagger target image..."
                    $currentImage = & $kubectl get deployment canary-demo-flagger `
                        -n default `
                        -o "jsonpath={.spec.template.spec.containers[0].image}"

                    if ($LASTEXITCODE -ne 0) {
                        throw "Could not read the Flagger target deployment."
                    }

                    Write-Host "Current target image: $currentImage"

                    Write-Host "Checking image availability in Minikube..."
                    $images = & $minikube -p devops-canary image ls

                    if ($LASTEXITCODE -ne 0) {
                        throw "Could not list images in Minikube."
                    }

                    $imageAvailable = $false
                    foreach ($image in $images) {
                        if ($image.Trim() -eq $requestedImage -or
                            $image.Trim() -eq "docker.io/library/$requestedImage") {
                            $imageAvailable = $true
                            break
                        }
                    }

                    if (-not $imageAvailable) {
                        throw "Image '$requestedImage' is not available in Minikube."
                    }

                    if ($requestedImage -eq $currentImage) {
                        Write-Host "Requested image is already deployed. No rollout is needed."
                    } else {
                        Write-Host "Image is available and differs from the current target."
                        Write-Host "Ready for the controlled deployment stage."
                    }
                '''
            }
        }

    }

    post {
        success {
            echo 'Initial Jenkins pipeline passed.'
        }

        failure {
            echo 'Initial Jenkins pipeline failed. Check Console Output.'
        }
    }
}
