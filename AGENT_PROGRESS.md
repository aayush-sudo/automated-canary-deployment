# Automated Canary Deployment Integration Checklist

This file records inspection findings only. No deployment, Chaos Mesh experiment,
merge, commit, or push was performed.

## Verified repository state

- Current branch: `feature/person2-deployment`.
- Current branch tracks `origin/feature/person2-deployment`.
- The tracked worktree was clean at inspection start.
- An untracked `evidence/` directory already exists locally.
- Existing Person 2 rollout baseline is the Jenkins `ROLLOUT_V3` path; Build #27
  was supplied as the known successful baseline and was not rerun.

## Verified available branches

- Local Person 1 branch: `feature/Aayush-app-ci`.
- Local Person 2 branch: `feature/person2-deployment`.
- Remote Person 3 branch: `origin/feature/person3-chaos` is advertised by the
  remote and was read through a temporary fetch result without checkout.
- Person 3's branch commit contains Chaos Mesh manifests and evidence but does
  not contain the Person 2 Jenkinsfile.

## Verified existing work

- Application and tests: `app/app.py`, `app/test_app.py`, and
  `app/requirements.txt`.
- Image build definition: `app/Dockerfile`.
- GitHub Actions CI: `.github/workflows/ci.yml` runs Python tests and builds
  `canary-demo:v1` and `canary-demo:v2` locally without publishing them.
- Kubernetes and Flagger resources: `k8s/`.
- Istio traffic resources: `istio/`.
- Person 2 rollout evidence: `evidence/person2/`.
- Person 3 Chaos Mesh resources on the remote branch:
  `experiments/canary-delay.yaml`, `experiments/flagger-canary-chaos.yaml`,
  and `experiments/latency-metric.yaml`, plus `evidence/person3/`.

## Proposed integration checklist (approval required before implementation)

- [ ] Decide whether Jenkins should build/tag/load images itself or consume
      images produced and published by CI; the current GitHub Actions workflow
      does not publish images.
- [ ] Define the source of the image version passed to Jenkins and preserve the
      existing safety contract for `CANARY_IMAGE` and `DEPLOY_MODE`.
- [ ] Add an approved Jenkins stage for application tests and image build/load,
      without weakening the existing Kubernetes and Flagger preflight checks.
- [ ] Apply or verify the Kubernetes, Flagger, and Istio resources in an
      approved order, keeping Flagger as the owner of canary traffic shifting.
- [ ] Add an opt-in Chaos Mesh stage that runs only after explicit approval and
      captures experiment status and cleanup evidence.
- [ ] Define promotion evidence: Flagger `Succeeded`, canary weight `0`,
      primary traffic `100`, expected application version, and rollout logs.
- [ ] Define rollback evidence: failed analysis, traffic returned to primary,
      affected resources/events, and clean experiment removal.
- [ ] Resolve branch integration strategy for Person 1 and Person 3 before any
      merge or Jenkinsfile modification.
- [ ] Run targeted tests and pipeline validation only after approval; no
      deployment or Chaos Mesh execution is part of this inspection.

## Open integration gaps

- GitHub Actions builds images but does not publish them or load them into the
  Jenkins agent's Minikube profile.
- Person 3's Chaos Mesh work is remote-only in this worktree and is not wired
  into Jenkins.
- No single approved pipeline currently coordinates application CI, image
  availability, Flagger rollout, traffic verification, and optional chaos
  verification.
- The current Jenkinsfile is Windows-agent-specific through configured paths
  for Docker, kubectl, Minikube, Helm, and kubeconfig.

## Evidence screenshots to capture after approval

1. Jenkins Build #27 parameters and successful overall result.
2. Jenkins console stages showing repository/environment checks and rollout
   completion.
3. Flagger Canary status showing `Succeeded`, `failedChecks: 0`, and a new
   `lastPromotedSpec`.
4. Istio/Flagger VirtualService showing primary `100` and canary `0` after
   promotion.
5. Workloads showing the promoted primary pod ready and the expected image.
6. The primary application's `/version` response showing the expected version.
7. For future rollback testing only: Chaos Mesh experiment status, Flagger
   failure/rollback status, traffic restoration, and cleanup confirmation.
