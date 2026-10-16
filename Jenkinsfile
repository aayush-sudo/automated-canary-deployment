
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

        stage('Check Build Environment') {      git status
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"

                    Write-Host "Agent identity:"
                    whoami

                    Write-Host "Git:"
                    git --version

                    Write-Host "Docker:"
                    docker --version

                    Write-Host "Kubernetes client:"
                    kubectl version --client
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
