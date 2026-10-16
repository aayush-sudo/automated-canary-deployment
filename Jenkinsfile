
pipeline {
    agent any

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
