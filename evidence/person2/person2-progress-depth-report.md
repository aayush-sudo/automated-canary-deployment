# Automated Canary Deployment — Person 2 Progress Depth Report

Date of report: 2026-10-19

## 1. Scope and status at a glance

This report documents the Person 2 work completed for the Jenkins deployment
pipeline, Flagger canary rollout, Istio traffic ownership, Prometheus latency
analysis, Chaos Mesh readiness, and preparation for a controlled rollback
demonstration.

The report separates:

- Commands actually executed.
- Results actually observed.
- Proposed commands or manifests that were not executed.
- Known blockers and required next actions.

The end-to-end Chaos Mesh rollback has **not** been demonstrated yet.

Current verified baseline:

- Branch: `feature/person2-deployment`
- Upstream: `origin/feature/person2-deployment`
- Last committed revision used by Jenkins Build #30:
  `fd68c246128657a930f9422391bbaf760acf3b3b`
- Kubernetes context: `devops-canary`
- Primary image: `canary-demo:v3`
- Primary readiness: `1/1`
- Flagger phase: `Succeeded`
- Flagger canary weight: `0`
- Flagger failed checks: `0`
- Flagger route: primary `100`, canary `0`
- Active NetworkChaos resources: none

## 2. Safety rules followed

The following actions were intentionally not performed:

- No `git clean`, hard reset, force push, or deletion of untracked files.
- No teammate branch merge.
- No static Istio VirtualService reapplication.
- No blind application of the alternate Person 3 Canary manifest.
- No Chaos Mesh experiment application.
- No live NetworkChaos resource creation.
- No Kubernetes resource modification except the explicitly approved additive
  live Canary metric attachment.
- No Jenkins build was triggered by the agent after the HTTP 403 response.
- No service account, Windows permission, environment variable, or service
  configuration was changed.
- No credentials, kubeconfig contents, tokens, or private keys were printed.

## 3. Repository and branch inspection

### Commands executed

```powershell
git status --short --branch
git branch --show-current
git log -1 --oneline --decorate
git remote -v
git --no-pager log -8 --oneline -- Jenkinsfile
```

### Observed results

```text
## feature/person2-deployment...origin/feature/person2-deployment
 M Jenkinsfile
?? AGENT_PROGRESS.md
?? evidence/
?? nly validation mode
```

The current branch remained `feature/person2-deployment`. The modified
Jenkinsfile was never staged, committed, or pushed during this work.

The untracked files and directories were preserved:

- [AGENT_PROGRESS.md](../../AGENT_PROGRESS.md)
- [evidence/](.)
- The oddly named untracked file

### Branch findings

- Person 1 branch: `feature/Aayush-app-ci`, available locally and remotely.
- Person 3 branch: `origin/feature/person3-chaos`, inspected without switching
  branches or merging.
- The application, tests, Dockerfile, and Person 1 CI work were already
  integrated into the Person 2 branch.
- Person 3's experiment files were remote-only during the earlier inspection.

## 4. Application and CI integration

Inspected files included:

- `app/app.py`
- `app/test_app.py`
- `app/requirements.txt`
- `app/Dockerfile`
- `.github/workflows/ci.yml`
- `docs/application-and-ci.md`

Verified findings:

- The application exposes health and version endpoints.
- The application version is controlled by `APP_VERSION`.
- GitHub Actions runs the Python tests.
- GitHub Actions builds v1 and v2 images with `push: false`.
- GitHub Actions does not publish an image registry artifact.
- Jenkins therefore builds and loads `canary-demo:v3` locally for the
  Minikube rollout.

## 5. Jenkins pipeline work

### Existing pipeline modes

The Jenkinsfile defines:

```text
VALIDATE_ONLY
IMAGE_BUILD_ONLY
ROLLOUT_V3
```

The rollout contract is exact:

```text
CANARY_IMAGE=canary-demo:v3
DEPLOY_MODE=ROLLOUT_V3
```

The build/load stage is gated for:

```groovy
params.DEPLOY_MODE in ['IMAGE_BUILD_ONLY', 'ROLLOUT_V3']
```

The image-only validation stage is restricted to:

```groovy
params.DEPLOY_MODE == 'IMAGE_BUILD_ONLY'
```

The Flagger rollout stage is restricted to:

```groovy
params.DEPLOY_MODE == 'ROLLOUT_V3'
```

Therefore `IMAGE_BUILD_ONLY` cannot reach the Flagger rollout stage.

### Approved Jenkinsfile change

The approved change previously reviewed in the `Build and Load Canary Image`
stage was:

```powershell
$dockerOutput = & $env:DOCKER build -f app/Dockerfile -t $image app 2>&1
$dockerExitCode = $LASTEXITCODE
$dockerOutput | ForEach-Object { Write-Host $_ }
if ($dockerExitCode -ne 0) {
    throw "Could not build $image."
}

$minikubeOutput = & $env:MINIKUBE image load --profile $profile $image 2>&1
$minikubeExitCode = $LASTEXITCODE
$minikubeOutput | ForEach-Object { Write-Host $_ }
if ($minikubeExitCode -ne 0) {
    throw "Could not load $image into Minikube profile $profile."
}
```

Preserved values:

```text
image: canary-demo:v3
Dockerfile: app/Dockerfile
build context: app
Minikube profile: devops-canary
```

### Static validation executed

The embedded PowerShell was parsed using the PowerShell parser. Result:

```text
Embedded PowerShell parse errors: 0
```

Also executed:

```powershell
git diff --check
git diff -- Jenkinsfile
git diff --stat -- Jenkinsfile
```

Results:

- No whitespace errors.
- Diff scope was limited to 8 insertions and 4 deletions.
- No other tracked file was changed.
- Jenkins was not triggered after this local edit.

The output-capture change is independently valid, but it does not solve
Minikube profile visibility when Jenkins runs under a different Windows
account.

## 6. Phase 1 — installed component and baseline verification

The complete command log is preserved in
[phase1-prerequisite-checks.txt](phase1-prerequisite-checks.txt).

### Context and repository

Commands:

```powershell
$env:KUBECONFIG = 'C:\Users\hp\.kube\config'
$KUBECTL = 'C:\Windows\System32\kubectl\kubectl.exe'
$HELM = 'C:\Users\hp\AppData\Local\Microsoft\WinGet\Links\helm.exe'
git status --short --branch
git branch --show-current
git log -1 --oneline --decorate
& $KUBECTL config current-context
```

Observed:

```text
Branch: feature/person2-deployment
HEAD: fd68c24 (ci: build canary image before rollout)
Kubernetes context: devops-canary
```

Status: **PASS**

### Helm releases and controllers

Commands:

```powershell
& $HELM list -A
& $KUBECTL get pods -n chaos-mesh -o wide
& $KUBECTL get deployment flagger -n istio-system -o wide
& $KUBECTL get crd networkchaos.chaos-mesh.org -o wide
```

Observed:

```text
chaos-mesh: chart/app 2.8.4, deployed
flagger: chart/app 1.45.0, deployed
prometheus: chart 29.36.1, app v3.15.0, deployed
chaos-controller-manager: 1/1 Running
chaos-daemon: 1/1 Running
flagger: 1/1 available
networkchaos.chaos-mesh.org: present
```

Status: **PASS**

### Chaos Mesh runtime and permissions

Commands:

```powershell
& $KUBECTL get daemonset chaos-daemon -n chaos-mesh -o yaml
& $KUBECTL get clusterrole chaos-mesh-chaos-controller-manager-cluster-level -o yaml
& $KUBECTL get clusterrole chaos-mesh-chaos-controller-manager-target-namespace -o yaml
& $KUBECTL api-resources | Select-String -Pattern 'networkchaos'
```

Observed:

```text
runtime: containerd
socket: /host-run/containerd.sock
hostPath: /run/containerd mounted at /host-run
NetworkChaos API: chaos-mesh.org/v1alpha1
```

Status: **PASS**

### Primary application and load generator

Commands:

```powershell
& $KUBECTL get deployments,pods,svc -n default -o wide
$version = & $KUBECTL exec deployment/canary-demo-flagger-primary `
  -n default -- python -c `
  "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5001/version', timeout=5).read().decode())"
& $KUBECTL logs pod/canary-load-generator -n default --since=5m --tail=80
& $KUBECTL get pods -n default -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,APP:.metadata.labels.app,VERSION:.metadata.labels.version,IMAGE:.spec.containers[0].image'
```

Observed:

```text
primary deployment: 1/1 ready
primary image: canary-demo:v3
/version: {"application":"canary-demo","version":"v3"}
canary-load-generator: Running, 2/2 ready
```

The recent load-generator log output was empty, so active request generation
was not proven by logs alone.

A label inconsistency was observed:

```text
primary running image/version: v3
primary pod label version: v2
```

The workload identity label `app` is the more important selector for the
Flagger-generated services, but this version-label inconsistency must remain a
review item.

Status:

- Application readiness/version: **PASS**
- Active traffic proof from load-generator logs: **BLOCKED**
- Label consistency: **REVIEW REQUIRED**

### Flagger routing

Command:

```powershell
& $KUBECTL get virtualservice,destinationrule -n default -o yaml
```

Observed:

```text
Flagger-owned VirtualService: canary-demo-flagger
primary weight: 100
canary weight: 0
```

The static repository VirtualService for the separate `canary-demo` service
was identified as distinct and must not be reapplied while Flagger owns the
generated route.

Status: **PASS**

## 7. Phase 2 — Prometheus latency metric

The complete command and result log is preserved in
[phase2-latency-metric-validation.txt](phase2-latency-metric-validation.txt).

### Provider and service

Commands:

```powershell
& $KUBECTL get metrictemplate latency-source -n default -o yaml
& $KUBECTL get svc prometheus-server -n istio-system -o yaml
```

Observed:

```text
MetricTemplate: latency-source
provider: prometheus
address: http://prometheus-server.istio-system:80
Prometheus Service port: 80/TCP
targetPort: 9090
```

Status: **PASS**

### PromQL validation

The query used the Istio duration histogram:

```promql
histogram_quantile(
  0.99,
  sum(
    rate(
      istio_request_duration_milliseconds_bucket{
        reporter="source",
        destination_workload_namespace="default",
        destination_workload=~"canary-demo-flagger.*"
      }[2m]
    )
  ) by (le)
)
```

The Prometheus API was queried through the Kubernetes service proxy:

```powershell
$encoded = [System.Uri]::EscapeDataString($query)
$path = "/api/v1/namespaces/istio-system/services/http:prometheus-server:80/proxy/api/v1/query?query=$encoded"
& $KUBECTL get --raw $path
```

Observed results:

```text
baseline: 9.776923076923078
primary: 9.776923076923078
canary: empty vector
```

The empty candidate vector was expected because no candidate workload existed.
The metric unit is milliseconds, so `max: 500` means 500 ms.

Status:

- Provider/service/query/unit: **PASS**
- Candidate-specific live data: **BLOCKED until candidate traffic exists**

### Approved live Canary metric attachment

The live Canary initially contained:

```text
request-success-rate: minimum 99, interval 2m
request-duration: maximum 500, interval 2m
```

After explicit approval, a JSON patch added only:

```yaml
- name: latency-seen-by-caller
  templateRef:
    name: latency-source
    namespace: default
  thresholdRange:
    max: 500
  interval: 2m
```

Before patching, the live Canary was backed up to:

[canary-demo-flagger-before-latency-metric.yaml](canary-demo-flagger-before-latency-metric.yaml)

The first inline patch attempt failed due to PowerShell argument quoting
before Kubernetes processed it. A patch file was then used successfully.

Observed after patch:

```text
request-success-rate|2m|99
request-duration|2m|max 500
latency-seen-by-caller|2m|max 500|latency-source|default
phase=Succeeded
weight=0
failedChecks=0
```

Status: **PASS for additive metric attachment**

No teammate Canary manifest was applied wholesale.

## 8. Phase 3 — Chaos Mesh experiment review

The complete review is preserved in
[phase3-chaos-review.txt](phase3-chaos-review.txt).

### Live selector findings

Commands:

```powershell
& $KUBECTL get pods -n default -l app=canary-demo-flagger --show-labels -o wide
& $KUBECTL get deploy -n default -o wide --show-labels
& $KUBECTL get pods -n default -l `
  'app in (canary-demo-flagger-primary,canary-demo-flagger-canary)' `
  --show-labels -o wide
```

Observed:

```text
target deployment canary-demo-flagger: 0 replicas
primary deployment canary-demo-flagger-primary: 1/1 ready
primary app label: canary-demo-flagger-primary
candidate deployment/pod: absent
```

The selector `app=canary-demo-flagger` did not match a current running pod.
It was therefore rejected for the proposed candidate experiment.

### Remote Person 3 files

Inspected without branch switching:

```powershell
git show origin/feature/person3-chaos:experiments/canary-delay.yaml
git show origin/feature/person3-chaos:experiments/flagger-canary-chaos.yaml
git show origin/feature/person3-chaos:experiments/latency-metric.yaml
```

Findings:

- `canary-delay.yaml` selected `app=canary-demo-flagger`, which was not the
  active candidate label.
- `flagger-canary-chaos.yaml` was an alternate full Canary definition and
  unsafe to apply wholesale.
- `latency-metric.yaml` used
  `http://prometheus.istio-system:9090`, which did not match the verified
  live service address.

### Proposed bounded experiment

The proposal was recorded in:

[phase3-networkchaos-proposed.yaml](phase3-networkchaos-proposed.yaml)

Its intended specification was:

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: canary-request-delay
  namespace: default
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      app: canary-demo-flagger-canary
  delay:
    latency: "800ms"
    correlation: "100"
    jitter: "0ms"
  direction: to
  duration: "5m"
```

The proposal was validated with:

```powershell
& $KUBECTL apply --dry-run=client --validate=strict `
  -f evidence/person2/phase3-networkchaos-proposed.yaml
```

Observed:

```text
networkchaos.chaos-mesh.org/canary-request-delay created (dry run)
```

This did not create a live resource.

## 9. Tagged `canary-delay-demo.yaml` assessment

The tagged file currently contains:

```yaml
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: canary-delay-demo
  namespace: default
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - default
    labelSelectors:
      app: canary-demo-flagger
  delay:
    latency: "800ms"
    correlation: "0"
    jitter: "100ms"
  duration: "10m"
  direction: to
```

It must not be applied as-is.

Reasons:

1. `app=canary-demo-flagger` targets the original Flagger target identity,
   which was scaled to zero, not the generated candidate identity.
2. Ten minutes is longer than the bounded five-minute proposal.
3. It uses different delay parameters from the reviewed proposal.
4. The candidate pod must exist and be verified before any selector is
   accepted.
5. The experiment must never target the primary workload.

Status: **NOT APPROVED FOR APPLICATION**

## 10. Phase 4 — candidate rollout preparation and Build #30

The rollout preparation log is preserved in
[phase4-rollout-preparation.txt](phase4-rollout-preparation.txt).

### Safe supported rollout path

The only supported candidate trigger is Jenkins Build with Parameters:

```text
CANARY_IMAGE=canary-demo:v3
DEPLOY_MODE=ROLLOUT_V3
```

The Jenkins rollout stage:

1. Builds `canary-demo:v3`.
2. Loads it into Minikube profile `devops-canary`.
3. Patches only the Flagger target deployment template.
4. Adds a unique rollout annotation.
5. Lets Flagger create the candidate and control traffic.
6. Waits for a new successful promotion.
7. Verifies the promoted primary `/version` response.

No direct static Istio route change is part of this workflow.

### Build #30 result

Build #30 was manually triggered by the user with the correct parameters.
The agent did not trigger a second build.

Jenkins checked out:

```text
fd68c246128657a930f9422391bbaf760acf3b3b
```

The console output showed:

```text
Active Kubernetes context: devops-canary
Building canary-demo:v3 from app/Dockerfile
```

The build then failed during the Minikube load step with:

```text
cluster "devops-canary" does not exist
Finished: FAILURE
```

The earlier diagnostic also captured Docker's legacy-builder stderr warning
as a PowerShell `NativeCommandError`. The approved Jenkinsfile output-capture
change addresses warning/error-stream handling, but it does not make a
Minikube profile visible across Windows accounts.

No candidate rollout was created by Build #30.

## 11. Jenkins account and Minikube profile blocker

### Commands executed

```powershell
Get-CimInstance Win32_Service |
  Where-Object { $_.Name -match 'jenkins' -or $_.DisplayName -match 'jenkins' } |
  Select-Object Name,DisplayName,State,StartName,PathName

[System.Security.Principal.WindowsIdentity]::GetCurrent().Name

Get-Item 'C:\Users\hp\.minikube\profiles\devops-canary'
Get-Item 'C:\Windows\System32\config\systemprofile\.minikube\profiles\devops-canary' `
  -ErrorAction SilentlyContinue
```

Observed:

```text
Jenkins service: Running
StartName: LocalSystem
Executable: C:\Program Files\Jenkins\jenkins.exe
Current interactive user: DESKTOP-77MHU0U\hp
User profile: C:\Users\hp\.minikube\profiles\devops-canary
SYSTEM profile: devops-canary profile unavailable
```

The Jenkinsfile explicitly sets:

```text
KUBECONFIG=C:\Users\hp\.kube\config
```

That is why Jenkins can read the Kubernetes context. Minikube profile
resolution is separate and normally uses the effective account's
`%USERPROFILE%\.minikube` location.

Confirmed root cause:

- Jenkins runs as `NT AUTHORITY\SYSTEM`.
- The existing Minikube profile belongs to `DESKTOP-77MHU0U\hp`.
- SYSTEM cannot see the user's `devops-canary` profile.
- `kubectl` context visibility and Minikube profile visibility are not the
  same thing.

### Option A selected by the project

Run the Jenkins Windows service as `DESKTOP-77MHU0U\hp`.

Trade-off:

- This is the simplest path for the local project because it reuses the
  verified profile and Docker Desktop access.
- It gives Jenkins builds access to the user's files and credentials.
- It depends on the user account's password and logon rights.
- A dedicated Jenkins service account is safer for a shared or production
  machine, but requires separate Minikube and Kubernetes provisioning.

The service account has not yet been changed by this work.

## 12. Current files and evidence

Created or updated evidence:

- [phase1-prerequisite-checks.txt](phase1-prerequisite-checks.txt)
- [phase2-latency-metric-validation.txt](phase2-latency-metric-validation.txt)
- [phase3-chaos-review.txt](phase3-chaos-review.txt)
- [phase3-networkchaos-proposed.yaml](phase3-networkchaos-proposed.yaml)
- [phase4-rollout-preparation.txt](phase4-rollout-preparation.txt)
- [person2-progress-depth-report.md](person2-progress-depth-report.md)

Backups:

- [canary-demo-flagger-before-latency-metric.yaml](canary-demo-flagger-before-latency-metric.yaml)

The current final status check showed no tracked diff. Evidence, progress,
the tagged experiment, and the oddly named file remain untracked. Nothing was
staged, committed, or pushed during the reporting step.

## 13. Final status checklist

| Area | Status | Evidence |
|---|---|---|
| Application and Person 1 CI integrated | PASS | Repository inspection and CI workflow |
| Jenkins v3 build/load logic present | PASS | Jenkinsfile static review |
| Docker warning handling improved | PASS | Embedded PowerShell parse and diff checks |
| Jenkins can access user's Minikube profile | BLOCKED | Jenkins still runs as LocalSystem |
| Kubernetes context `devops-canary` | PASS | `kubectl config current-context` |
| Flagger installed and ready | PASS | Phase 1 Helm/controller checks |
| Prometheus service/provider valid | PASS | Phase 2 service and MetricTemplate checks |
| Latency query returns numeric milliseconds | PASS | Values approximately 9.78 ms and 16.3 ms |
| Custom metric attached to live Canary | PASS | Approved additive patch and status verification |
| Candidate pod created | BLOCKED | Build #30 failed before rollout |
| Candidate selector verified live | BLOCKED | No candidate pod exists |
| NetworkChaos manifest schema valid | PASS | Client-side strict dry run |
| NetworkChaos experiment applied | NOT DONE | No active NetworkChaos resources |
| Chaos-driven rollback demonstrated | NOT DONE | No candidate/experiment/failed analysis |
| Cluster restored after chaos | NOT APPLICABLE | Chaos was never started |
| Jenkinsfile committed and pushed | UNVERIFIED FROM CURRENT WORKTREE | No current tracked diff; commit/push history was not changed by this report |

## 14. Safest next steps

1. Obtain explicit approval to change the Jenkins Windows service from
   `LocalSystem` to `DESKTOP-77MHU0U\hp`.
2. Change the service account manually or through an approved administrative
   procedure, preserving the password securely.
3. Restart Jenkins and verify the service starts.
4. Run read-only Jenkins access checks:

   ```powershell
   whoami
   minikube profile list
   minikube status --profile devops-canary
   kubectl config current-context
   kubectl get nodes
   ```

5. Do not trigger a rollout until Jenkins can see the profile.
6. Run the approved Jenkins rollout with:

   ```text
   CANARY_IMAGE=canary-demo:v3
   DEPLOY_MODE=ROLLOUT_V3
   ```

7. While Flagger is analyzing, verify:

   ```powershell
   kubectl get pods -n default `
     -l app=canary-demo-flagger-canary --show-labels -o wide
   kubectl get deployment canary-demo-flagger-canary -n default
   kubectl get virtualservice canary-demo-flagger -n default -o yaml
   kubectl get canary canary-demo-flagger -n default -o yaml
   ```

8. Confirm the candidate is Running, ready, and receiving traffic before
   applying any chaos.
9. Reconfirm the Prometheus candidate-specific query returns data.
10. Request separate explicit approval before applying
    [phase3-networkchaos-proposed.yaml](phase3-networkchaos-proposed.yaml).
11. After an approved experiment, remove only the named NetworkChaos resource
    and verify:

    ```powershell
    kubectl delete networkchaos canary-request-delay -n default
    kubectl get networkchaos -A
    ```

12. Capture actual Flagger failed checks, traffic restoration, application
    version, readiness, and cleanup output. Do not describe rollback as
    successful unless those outputs are observed.

## 15. Bottom-line conclusion

The infrastructure prerequisites are largely healthy and the custom latency
metric is attached to the live Canary. The main blocker is Jenkins account
isolation: the Jenkins SYSTEM account cannot see the user's Minikube profile.
Build #30 therefore never created a candidate. The Chaos Mesh experiment
remains prepared but unapplied, and the required end-to-end unhealthy-canary
rollback remains unverified.
