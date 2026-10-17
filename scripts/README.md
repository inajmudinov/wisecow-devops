# Problem Statement 2

Selected objectives:
1. System Health Monitoring
2. Application Health Checker

Requirements: Python 3 standard library. System monitoring requires Linux.

## System health monitoring

Checks CPU usage over one second, memory usage, disk usage,
total processes and processes in the running state.

Default alert thresholds:
- CPU: greater than 80%
- Memory: greater than 80%
- Disk: greater than 85%
- Total processes: greater than 500

Run:
    python3 scripts/system_health.py

Customize thresholds and save a log:
    python3 scripts/system_health.py --cpu 80 --memory 80 --disk 85 --max-processes 500 --log /tmp/wisecow-health.log

Exit codes: 0 = healthy, 1 = threshold exceeded, 2 = error.

Validated normal output, forced process-count alert, file logging,
and alert exit code 1. Metrics describe the Linux/WSL environment.

## Application health checker

Checks HTTP status, response time and availability across sampled requests.
HTTP 200 is expected by default. Redirects are followed.
Connection failures, timeouts and unexpected statuses are reported DOWN.
HTTPS certificate verification is enabled; --ca-cert accepts a custom CA.

Healthy application:
    python3 scripts/app_health.py http://localhost:4499/ --checks 5 --interval 2

Unavailable endpoint:
    python3 scripts/app_health.py http://127.0.0.1:1/ --timeout 2

Custom expected status:
    python3 scripts/app_health.py https://example.com/ --expected-status 200

Exit codes: 0 = all checks healthy, 1 = at least one failed check,
2 = configuration error.

Validated five successful HTTP 200 checks with exit code 0 and
connection-refused detection with exit code 1.
An earlier run detected a closed connection followed by two successes.
Availability is calculated from observed samples, not historical uptime.
