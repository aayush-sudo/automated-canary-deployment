pipeline {
    agent any

    parameters {
        string(
            name: 'CANARY_IMAGE',
            defaultValue: 'canary-demo:v2',
            description: 'Container image to validate or deploy through the Flagger-managed canary'
        )
        choice(
            name: 'DEPLOY_MODE',
            choices: ['VALIDATE_ONLY', 'IMAGE_BUILD_ONLY', 'ROLLOUT_V3'],
            description: 'Choose validation only or explicitly trigger the v3 canary rollout'
        )
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        MINIKUBE_HOME = 'C:\\Users\\hp\\.minikube'
        KUBECONFIG = 'C:\\Users\\hp\\.kube\\config'
        KUBECTL = 'C:\\Windows\\System32\\kubectl\\kubectl.exe'
        MINIKUBE = 'C:\\Program Files\\Kubernetes\\Minikube\\minikube.exe'
        DOCKER = 'C:\\Users\\hp\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        HELM = 'C:\\Users\\hp\\AppData\\Local\\Microsoft\\WinGet\\Links\\helm.exe'
    }

    stages {
        stage('Checkout') {
            steps { checkout scm }
        }

        stage('Verify Repository') {
            steps {
                echo 'Repository checkout completed.'
                powershell '''
                    $ErrorActionPreference = "Stop"
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
                    Write-Host "Agent identity:"
                    whoami
                    Write-Host "`nGit:"
                    git --version
                    if ($LASTEXITCODE -ne 0) { throw "Git is unavailable." }
                    Write-Host "`nDocker client and server:"
                    & $env:DOCKER version
                    if ($LASTEXITCODE -ne 0) { throw "Jenkins cannot connect to Docker." }
                    Write-Host "`nKubernetes client:"
                    & $env:KUBECTL version --client
                    if ($LASTEXITCODE -ne 0) { throw "kubectl is unavailable." }
                    Write-Host "`nMinikube profile diagnostic:"
                    & $env:MINIKUBE profile list
                    Write-Host "Continuing to the explicit Kubernetes access diagnostic."
                    Write-Host "`nHelm:"
                    & $env:HELM version
                    if ($LASTEXITCODE -ne 0) { throw "Helm is unavailable." }
                    Write-Host "`nKubernetes context:"
                    & $env:KUBECTL config current-context
                    if ($LASTEXITCODE -ne 0) { throw "Could not read Kubernetes context." }
                    Write-Host "`nKubernetes nodes:"
                    & $env:KUBECTL get nodes
                    if ($LASTEXITCODE -ne 0) { throw "Jenkins cannot access Kubernetes." }
                '''
            }
        }

        stage('Diagnose Kubernetes Access') {
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"

                    Write-Host "Jenkins service identity:"
                    whoami

                    Write-Host "Checking kubeconfig:"
                    Test-Path "C:\\Users\\hp\\.kube\\config"

                    Write-Host "Checking Minikube API endpoint:"
                    Test-NetConnection 127.0.0.1 -Port 51191

                    Write-Host "Testing Kubernetes API access:"
                    & $env:KUBECTL --request-timeout=10s get nodes
                    if ($LASTEXITCODE -ne 0) {
                        throw "Kubernetes API access failed under Jenkins."
                    }
                '''
            }
        }

        stage('Deployment Preflight') {
            when { expression { params.DEPLOY_MODE != 'IMAGE_BUILD_ONLY' } }
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    Write-Host "Checking Flagger canary..."
                    & $env:KUBECTL get canary canary-demo-flagger -n default
                    if ($LASTEXITCODE -ne 0) { throw "Required Flagger canary was not found." }
                    Write-Host "Checking Flagger controller..."
                    & $env:KUBECTL get deployment flagger -n istio-system
                    if ($LASTEXITCODE -ne 0) { throw "Flagger controller is unavailable." }
                    Write-Host "Checking Flagger-managed services..."
                    & $env:KUBECTL get services canary-demo-flagger canary-demo-flagger-primary canary-demo-flagger-canary -n default
                    if ($LASTEXITCODE -ne 0) { throw "One or more required Flagger services are missing." }
                    Write-Host "Deployment preflight passed."
                '''
            }
        }

        stage('Build and Load Canary Image') {
            when {
                expression {
                    params.DEPLOY_MODE in ['IMAGE_BUILD_ONLY', 'ROLLOUT_V3']
                }
            }
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    $image = "canary-demo:v3"
                    $profile = "devops-canary"
                    $requestedImage = "$env:CANARY_IMAGE".Trim()

                    if ($requestedImage -ne $image) {
                        throw "IMAGE_BUILD_ONLY requires CANARY_IMAGE to be exactly $image."
                    }

                    Write-Host "Checking active Kubernetes context before building or loading the image."
                    $context = & $env:KUBECTL config current-context
                    if ($LASTEXITCODE -ne 0) {
                        throw "Could not read the active Kubernetes context."
                    }
                    $context = ($context -join "").Trim()
                    Write-Host "Active Kubernetes context: $context"
                    if ($context -ne $profile) {
                        throw "Refusing image build and load because the active Kubernetes context is '$context', not '$profile'."
                    }

                    $env:PATH = "C:/Users/hp/AppData/Local/Programs/DockerDesktop/resources/bin;$env:PATH"

                    Write-Host "Building $image from app/Dockerfile."

                    $stdoutFile = Join-Path $env:TEMP "docker-build-$env:BUILD_NUMBER.out"
                    $stderrFile = Join-Path $env:TEMP "docker-build-$env:BUILD_NUMBER.err"

                    $dockerArgs = @(
                        'build',
                        '-f', 'app/Dockerfile',
                        '-t', $image,
                        'app'
                    )

                    $process = Start-Process `
                        -FilePath $env:DOCKER `
                        -ArgumentList $dockerArgs `
                        -WorkingDirectory (Get-Location).Path `
                        -Wait `
                        -PassThru `
                        -NoNewWindow `
                        -RedirectStandardOutput $stdoutFile `
                        -RedirectStandardError $stderrFile

                    if (Test-Path $stdoutFile) {
                        Get-Content $stdoutFile | ForEach-Object { Write-Host $_ }
                    }

                    if (Test-Path $stderrFile) {
                        Get-Content $stderrFile | ForEach-Object { Write-Host $_ }
                    }

                    $dockerExitCode = $process.ExitCode

                    Remove-Item $stdoutFile, $stderrFile -Force -ErrorAction SilentlyContinue

                    if ($dockerExitCode -ne 0) {
                        throw "Could not build $image. Docker exit code: $dockerExitCode"
                    }

                    Write-Host "Docker image build completed successfully."

                    Write-Host "Loading $image into Minikube profile $profile."
                    $minikubeOutput = & $env:MINIKUBE image load --profile $profile $image 2>&1
                    $minikubeExitCode = $LASTEXITCODE
                    $minikubeOutput | ForEach-Object { Write-Host $_ }
                    if ($minikubeExitCode -ne 0) {
                        throw "Could not load $image into Minikube profile $profile."
                    }

                    Write-Host "Image build and Minikube load passed."
                '''
            }
        }

        stage('Validate Canary Image') {
            when { expression { params.DEPLOY_MODE != 'IMAGE_BUILD_ONLY' } }
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    $requestedImage = "$env:CANARY_IMAGE".Trim()
                    $deployMode = "$env:DEPLOY_MODE".Trim()
                    Write-Host "Deployment mode: $deployMode"
                    Write-Host "Requested image: $requestedImage"

                    if ($deployMode -notin @("VALIDATE_ONLY", "ROLLOUT_V3")) {
                        throw "Unsupported deployment mode: $deployMode"
                    }
                    if ([string]::IsNullOrWhiteSpace($requestedImage)) {
                        throw "CANARY_IMAGE must not be empty."
                    }

                    if ($deployMode -eq "VALIDATE_ONLY") {
                        if ($requestedImage -notin @("canary-demo:v1", "canary-demo:v2")) {
                            throw "VALIDATE_ONLY supports canary-demo:v1 or canary-demo:v2."
                        }
                        $knownImage = $false
                        foreach ($deployment in @("canary-demo-v1", "canary-demo-v2")) {
                            $image = & $env:KUBECTL get deployment $deployment -n default -o "jsonpath={.spec.template.spec.containers[0].image}"
                            if ($LASTEXITCODE -ne 0) { throw "Could not inspect deployment $deployment." }
                            $image = ($image -join "").Trim()
                            if ($image -ne $requestedImage) { continue }
                            $ready = & $env:KUBECTL get deployment $deployment -n default -o "jsonpath={.status.readyReplicas}"
                            if ($LASTEXITCODE -ne 0) { throw "Could not check readiness for $deployment." }
                            $replicas = & $env:KUBECTL get deployment $deployment -n default -o "jsonpath={.spec.replicas}"
                            if ($LASTEXITCODE -ne 0) { throw "Could not read replica count for $deployment." }
                            $readyText = ($ready -join "").Trim()
                            $replicaText = ($replicas -join "").Trim()
                            $readyCount = if ([string]::IsNullOrWhiteSpace($readyText)) { 0 } else { [int]$readyText }
                            $replicaCount = if ([string]::IsNullOrWhiteSpace($replicaText)) { 0 } else { [int]$replicaText }
                            if ($readyCount -lt 1 -or $replicaCount -lt 1) {
                                throw "Image '$requestedImage' matches $deployment, but it has no ready replica."
                            }
                            Write-Host "Validated $requestedImage on $deployment ($readyCount/$replicaCount ready)."
                            $knownImage = $true
                            break
                        }
                        if (-not $knownImage) { throw "Image '$requestedImage' does not match a validated v1 or v2 deployment." }
                        Write-Host "Validation-only mode: no application resources will be changed."
                    }
                    else {
                        if ($requestedImage -ne "canary-demo:v3") {
                            throw "ROLLOUT_V3 requires CANARY_IMAGE to be exactly canary-demo:v3."
                        }
                        $checkPod = "canary-image-check-$env:BUILD_NUMBER"
                        Write-Host "Testing v3 image on Minikube with temporary pod $checkPod."
                        & $env:KUBECTL delete pod $checkPod -n default --ignore-not-found=true --wait=true
                        if ($LASTEXITCODE -ne 0) { throw "Could not clear an old image-check pod." }
                        & $env:KUBECTL run $checkPod -n default --image=$requestedImage --restart=Never --image-pull-policy=Never --command -- python -c "print('v3 image available')"
                        if ($LASTEXITCODE -ne 0) { throw "Could not create the v3 image-check pod." }
                        & $env:KUBECTL wait --for=jsonpath='{.status.phase}'=Succeeded "pod/$checkPod" -n default --timeout=90s
                        if ($LASTEXITCODE -ne 0) {
                            & $env:KUBECTL describe pod $checkPod -n default
                            & $env:KUBECTL logs $checkPod -n default
                            & $env:KUBECTL delete pod $checkPod -n default --ignore-not-found=true --wait=true
                            throw "The v3 image is not runnable on Minikube."
                        }
                        & $env:KUBECTL logs $checkPod -n default
                        if ($LASTEXITCODE -ne 0) { throw "Could not read image-check output." }
                        & $env:KUBECTL delete pod $checkPod -n default --ignore-not-found=true --wait=true
                        if ($LASTEXITCODE -ne 0) { throw "Could not clean up the image-check pod." }
                        Write-Host "v3 image validation passed."
                    }
                '''
            }
        }

        stage('Validate Built Image') {
            when { expression { params.DEPLOY_MODE == 'IMAGE_BUILD_ONLY' } }
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    $image = "canary-demo:v3"
                    $profile = "devops-canary"
                    $checkPod = "canary-image-only-check-$([Guid]::NewGuid().ToString('N').Substring(0, 20))"
                    $failure = $null

                    try {
                        Write-Host "Checking active Kubernetes context."
                        $context = & $env:KUBECTL config current-context
                        if ($LASTEXITCODE -ne 0) {
                            throw "Could not read the active Kubernetes context."
                        }
                        $context = ($context -join "").Trim()
                        Write-Host "Active Kubernetes context: $context"
                        if ($context -ne $profile) {
                            throw "Refusing image validation because the active Kubernetes context is '$context', not '$profile'."
                        }

                        Write-Host "Creating isolated image-check pod $checkPod."
                        & $env:KUBECTL run $checkPod `
                            -n default `
                            --image=$image `
                            --restart=Never `
                            --image-pull-policy=Never `
                            --command -- python -c "print('canary-demo:v3 image available')"
                        if ($LASTEXITCODE -ne 0) {
                            throw "Could not create the image-check pod."
                        }

                        & $env:KUBECTL wait `
                            --for=jsonpath='{.status.phase}'=Succeeded `
                            "pod/$checkPod" `
                            -n default `
                            --timeout=90s
                        if ($LASTEXITCODE -ne 0) {
                            & $env:KUBECTL describe pod $checkPod -n default
                            & $env:KUBECTL logs $checkPod -n default
                            throw "The image-check pod did not reach Succeeded."
                        }

                        & $env:KUBECTL logs $checkPod -n default
                        if ($LASTEXITCODE -ne 0) {
                            throw "Could not read image-check output."
                        }

                        Write-Host "Built image execution validation passed."
                    }
                    catch {
                        $failure = $_
                    }
                    finally {
                        Write-Host "Cleaning up image-check pod $checkPod."
                        & $env:KUBECTL delete pod $checkPod -n default --ignore-not-found=true --wait=true
                        if ($LASTEXITCODE -ne 0) {
                            Write-Warning "Could not clean up image-check pod $checkPod."
                        }
                    }

                    if ($null -ne $failure) {
                        throw $failure
                    }
                '''
            }
        }

        stage('Trigger Flagger Canary Rollout') {
            when { expression { params.DEPLOY_MODE == 'ROLLOUT_V3' } }
            steps {
                powershell '''
                    $ErrorActionPreference = "Stop"
                    if ("$env:CANARY_IMAGE" -ne "canary-demo:v3") {
                        throw "Safety check failed: rollout mode only permits canary-demo:v3."
                    }

                    $oldPromoted = & $env:KUBECTL get canary canary-demo-flagger -n default -o "jsonpath={.status.lastPromotedSpec}"
                    if ($LASTEXITCODE -ne 0) { throw "Could not read current Flagger promotion status." }
                    $oldPromoted = ($oldPromoted -join "").Trim()
                    Write-Host "Previous promoted spec: $oldPromoted"

                    $patchPath = Join-Path $env:TEMP "canary-v3-patch-$env:BUILD_NUMBER.json"
                    $patch = '{"spec":{"template":{"metadata":{"annotations":{"rollout-trigger":"jenkins-' + $env:BUILD_NUMBER + '"}},"spec":{"containers":[{"name":"canary-demo","image":"canary-demo:v3","env":[{"name":"APP_VERSION","value":"v3"}]}]}}}}'
                    Set-Content -Path $patchPath -Value $patch -Encoding ascii
                    try {
                        Write-Host "Updating the Flagger target template. Flagger manages analysis and traffic shifting."
                        & $env:KUBECTL patch deployment canary-demo-flagger -n default --type=strategic --patch-file $patchPath
                        if ($LASTEXITCODE -ne 0) { throw "Could not update the Flagger target deployment." }
                    }
                    finally { Remove-Item $patchPath -Force -ErrorAction SilentlyContinue }

                    $deadline = (Get-Date).AddMinutes(25)
                    $promoted = $false
                    while ((Get-Date) -lt $deadline) {
                        $phase = & $env:KUBECTL get canary canary-demo-flagger -n default -o "jsonpath={.status.phase}"
                        if ($LASTEXITCODE -ne 0) { throw "Could not read Flagger phase." }
                        $phase = ($phase -join "").Trim()
                        $newPromoted = & $env:KUBECTL get canary canary-demo-flagger -n default -o "jsonpath={.status.lastPromotedSpec}"
                        if ($LASTEXITCODE -ne 0) { throw "Could not read Flagger promotion hash." }
                        $newPromoted = ($newPromoted -join "").Trim()
                        Write-Host "Flagger phase=$phase; promoted spec=$newPromoted"
                        if ($phase -eq "Failed") {
                            & $env:KUBECTL describe canary canary-demo-flagger -n default
                            & $env:KUBECTL logs deployment/flagger -n istio-system --tail=80
                            throw "Flagger marked the v3 canary rollout as Failed."
                        }
                        if ($phase -eq "Succeeded" -and -not [string]::IsNullOrWhiteSpace($newPromoted) -and $newPromoted -ne $oldPromoted) {
                            $promoted = $true
                            break
                        }
                        Start-Sleep -Seconds 15
                    }
                    if (-not $promoted) {
                        & $env:KUBECTL describe canary canary-demo-flagger -n default
                        & $env:KUBECTL get pods -n default
                        throw "Timed out waiting for a new successful Flagger promotion. Inspect status before retrying."
                    }

                    Write-Host "Flagger reports a new successful promotion."
                    & $env:KUBECTL get deployment canary-demo-flagger-primary -n default
                    if ($LASTEXITCODE -ne 0) { throw "Could not inspect the promoted primary deployment." }
                    $primaryVersion = & $env:KUBECTL exec deployment/canary-demo-flagger-primary -n default -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5001/version', timeout=5).read().decode())"
                    if ($LASTEXITCODE -ne 0) {
                        throw "Could not verify the primary application version through /version."
                    }
                    $primaryVersion = ($primaryVersion -join "").Trim()
                    Write-Host "Primary version response: $primaryVersion"

                    try {
                        $versionObject = $primaryVersion | ConvertFrom-Json
                    }
                    catch {
                        throw "Primary /version endpoint did not return valid JSON: $primaryVersion"
                    }

                    if ($versionObject.version -ne "v3") {
                        throw "Primary /version response does not confirm v3: $primaryVersion"
                    }

                    Write-Host "Primary application version confirmed: $($versionObject.version)"
                '''
            }
        }
    }

    post {
        success { echo 'Jenkins pipeline completed successfully.' }
        failure { echo 'Jenkins pipeline failed. Check Console Output and Flagger status before retrying.' }
    }
}
