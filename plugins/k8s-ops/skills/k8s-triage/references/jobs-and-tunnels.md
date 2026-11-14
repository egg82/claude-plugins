# Jobs, CronJobs and port-forward tunnels

## CronJobs: the status field that answers a question you did not ask

**`lastSuccessfulTime` is populated by manual jobs too, so it is set even when the schedule has never
fired.** `lastScheduleTime` is the only field that says the schedule ran. A nightly job exercised three
times by hand shows `lastScheduleTime` empty and `lastSuccessfulTime` populated.
`kubectl create job --from=cronjob/x` proves the job works and says nothing about the schedule. Until
`lastScheduleTime` is non-empty, treat an unattended loop as unobserved.

- **A job can report `Failed` while its work completed.** A non-zero exit from a late step (a
  post-render validation, a regression check) burns the backoff limit after the real output landed. Read
  the volume before reading the exit code. A backoff-exhausted job takes its pod with it, so capture logs
  before retrying.
- **`concurrencyPolicy: Forbid` only counts jobs the CronJob controller created.** A manual job is
  invisible to it both ways: the schedule fires on top of your manual run, and your manual run is blocked
  by nothing. Check for a running job yourself before firing one.
- **A backoff retry runs the Job's ORIGINAL pod template**, image included. A Job created before an
  image bump retries on the old image after the bump, so "the first run after the release" can be that
  retry. Wait for a Job whose `creationTimestamp` is after the release (or whose pod spec carries the new
  image), never for "a run that started after it".

## A `port-forward` that outlived its pod returns EMPTY BODIES, not an error

It reads as "the API is broken" rather than "your tunnel is dead". `kubectl port-forward deploy/x`
resolves to one pod at start and does not follow a rollout, so a fast-merging repo loses the tunnel every
few minutes unannounced.

```bash
# Rebind to whatever pod is CURRENT, then wait on a condition the DEAD tunnel
# cannot satisfy: a 200 with a real body, never just "port open".
POD=$(kubectl -n "$NS" get pod -l app=x --field-selector=status.phase=Running \
        -o jsonpath='{.items[0].metadata.name}')
kubectl -n "$NS" port-forward "pod/$POD" 8080:8080 &
for i in $(seq 1 20); do
  case "$(curl -s --max-time 3 http://127.0.0.1:8080/api/thing | head -c 1)" in '[') break;; esac
done
```

When the read exists to confirm a deploy, make the check prove it is the new build: grep the served asset
for a token only the change introduces. A rebound tunnel pointing at a not-yet-rolled pod is the same
false-clean one layer along.
