# Wisecow: Docker, Kubernetes, CI/CD and TLS

## Assignment and scope
This project demonstrates containerization, Kubernetes deployment, automated CI/CD, and TLS-secured access for the Wisecow application. This solution includes application source, Dockerfile, Deployment, Service, TLS Ingress and GitHub Actions build/push/deploy workflow.
The screenshots say both private and public repository; the upstream README also requests private access for nyrahul. Confirm the final visibility and reviewer with the recruiter. Do not publish credentials.

Based on the [Wisecow application](https://github.com/nyrahul/wisecow), this project adds containerization, Kubernetes deployment, TLS, and CI/CD automation.

## 1. Prerequisites
Use a Linux/macOS computer or Windows WSL2 with Docker running. Install git, kubectl, k3d, curl and OpenSSL. Check their official installation pages:
- https://docs.docker.com/engine/install/
- https://kubernetes.io/docs/tasks/tools/
- https://k3d.io/

## 2. Build and test locally
Run from the extracted project directory:
```bash
docker build -t wisecow:local .
docker run -d --name wisecow -p 4499:4499 wisecow:local
curl --fail http://localhost:4499/
docker logs wisecow
docker rm -f wisecow
```
Expected: an HTML `<pre>` block with a cow and a random saying.
The image runs as UID 10001; dependencies include netcat-openbsd and /usr/games in PATH.

## 3. Create local Kubernetes and deploy
This concrete example uses k3d's bundled Traefik ingress controller. Port 8443 on your computer maps to HTTPS port 443 on its load balancer.
```bash
k3d cluster create wisecow -p '8443:443@loadbalancer' --agents 1
kubectl create namespace wisecow
k3d image import wisecow:local -c wisecow
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl -n wisecow rollout status deployment/wisecow --timeout=180s
kubectl -n wisecow get pods,svc
```
ClusterIP exposes the app inside Kubernetes; Ingress supplies external HTTPS access. If using another cluster, install an ingress controller and change ingressClassName accordingly.
The probes check process/FIFO presence only: they are lightweight and do not establish end-to-end health. TCP connect-only probes can interfere with this single-request netcat server; use the curl checks below to verify actual serving.

## 4. Enable TLS for the local demonstration
Generate a certificate with a Subject Alternative Name matching the ingress hostname. Keep its private key out of git.
```bash
openssl req -x509 -nodes -days 30 -newkey rsa:2048 \
  -keyout wisecow.key -out wisecow.crt \
  -subj '/CN=wisecow.local' -addext 'subjectAltName=DNS:wisecow.local'
kubectl -n wisecow create secret tls wisecow-tls --cert=wisecow.crt --key=wisecow.key
kubectl apply -f k8s/ingress.yaml
curl --fail --cacert wisecow.crt \
  --resolve wisecow.local:8443:127.0.0.1 https://wisecow.local:8443/
```
This verifies the certificate using the supplied CA certificate; do not use `curl -k` as proof of certificate verification. TLS terminates at Traefik; Traefik-to-Service traffic is HTTP. End-to-end encrypted pod traffic would need an additional TLS proxy or service mesh.
For public access, use a domain you control, point DNS at your ingress endpoint, update both hostname fields, expose port 443 and provision a trusted certificate (for example with cert-manager/ACME). The local certificate is not publicly trusted. This demonstration does not create a public site.

## 5. Push to your own GitHub repository
Create an empty repository in GitHub with the visibility confirmed by the recruiter. Extracted ZIPs do not contain upstream git history.
```bash
git init -b main
git add .
git commit -m 'Containerize Wisecow with Kubernetes TLS and CI/CD'
git remote add origin https://github.com/YOUR_USERNAME/wisecow-devops.git
git push -u origin main
```
For a cloned working copy with an existing origin, rename that remote first or change its URL. Never push this solution into the upstream author's repository.

## 6. CI: automatic build and push
On pushes to every branch the workflow builds, starts the container, checks a real HTTP response, then publishes to `ghcr.io/OWNER/REPOSITORY:COMMIT_SHA`. Pull requests build and test without publishing. GITHUB_TOKEN is supplied automatically; the job requests packages:write.
Check Actions for successful logs. GHCR packages can remain private even when a repository is public. For the simplest demo, explicitly make the image package public in GitHub package settings. If you retain a private package, create a Kubernetes imagePullSecret using a read:packages token, and add imagePullSecrets to the Deployment's pod spec before deployment. Never store that token in source files.

## 7. CD challenge: deploy after a successful build
Enable only once the namespace, TLS secret, image pull access and ingress controller exist.
1. Configure a dedicated self-hosted Linux GitHub Actions runner with labels `self-hosted`, `linux`, `wisecow`, kubectl installed and network access to the Kubernetes API. Do not enable this runner for untrusted contributions. Use a dedicated demo cluster, not a production host.
2. Create GitHub environment `production`. Add its secret `KUBE_CONFIG`: the complete raw kubeconfig YAML (not base64). Use a dedicated namespace-scoped deployment identity. Its role needs get/list/watch/create/update/patch on deployments, services and ingresses, plus get/list/watch on pods and replicasets in namespace wisecow. Do not use an administrator kubeconfig. For k3d, a runner on the same host can reach the local API; a containerized/remote runner may require a different reachable API endpoint and valid certificate settings.
3. Set repository Actions variable `ENABLE_CD` to `true`.
4. Push to main. After build/test/push succeeds, CD applies Service/Ingress and Deployment using the exact published image digest, then waits for rollout. Automatic deployment is disabled until this variable is enabled. Environment protection rules may require approval if you configure them.

The workflow never creates or prints TLS private keys or kubeconfig contents. Use branch protection on main. For stronger supply-chain controls, pin actions and the base image to reviewed immutable digests.

## 8. Validate and collect submission evidence
```bash
kubectl -n wisecow get deployments,pods,svc,ingress
kubectl -n wisecow describe deployment wisecow
kubectl -n wisecow logs deployment/wisecow --tail=20
curl --fail --cacert wisecow.crt --resolve wisecow.local:8443:127.0.0.1 https://wisecow.local:8443/
```
Submit your repository URL, successful Actions screenshot, running pods/services/ingress screenshot and HTTPS output. Explain Docker image -> GHCR -> Deployment -> Service -> TLS Ingress. CI means Continuous Integration; CD means Continuous Deployment; TLS means Transport Layer Security.
Troubleshooting: ImagePullBackOff usually means image name/tag or registry credentials; Pending pods can mean insufficient resources; a 404 often means the request hostname/controller does not match; a 502/503 means check pod readiness, Service selectors and port 4499.
Rollback: `kubectl -n wisecow rollout undo deployment/wisecow` followed by rollout status. Local cleanup: `k3d cluster delete wisecow` (deletes this demo cluster).

## Validation status

Successfully validated on Windows with Ubuntu WSL2 and Docker:

- Docker image built and application tested in terminal and browser.
- Two-node k3d Kubernetes cluster created.
- Two application replicas running with a ClusterIP Service.
- HTTPS tested through Traefik using a self-signed certificate,
  with certificate verification enabled through curl --cacert.
- GitHub Actions built, tested and published the image to GHCR.
- The deployment job successfully deployed the published image by digest.
- HTTPS was tested successfully again after automated deployment.

Successful workflow:
https://github.com/inajmudinov/wisecow-devops/actions/runs/39073308137

Deployment requires the laptop, Docker and self-hosted runner to be running.
KUBE_CONFIG uses a temporary service-account token requested for 24 hours;
renew it after expiry. Renew the registry pull token before its expiry.
TLS terminates at Traefik; traffic from Traefik to the application is HTTP.
The application is available locally, not hosted on a public internet endpoint.
