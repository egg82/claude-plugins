# k8up under `restricted` PodSecurity fails silently

k8up's backup/prune/restore runner pods are rejected at admission by PodSecurity `restricted`, because
they don't set container-level `allowPrivilegeEscalation: false` or `capabilities.drop: [ALL]`. The
operator exposes only a **pod**-level security context, so it **cannot** be made restricted-compliant
through configuration.

**The effect is invisible:** every schedule fires, the Job fails `BackoffLimitExceeded`, and no pod is
ever created. Existing repos freeze at whenever `restricted` began being enforced, and anything added
afterwards gets an empty repo — the classic "the latest backup doesn't work" with nothing obviously
broken. (Talos defaults to `baseline`, so a cluster-wide `restricted` means somebody hardened it
deliberately.)

**Fix:** run the k8up namespace at `baseline` enforce and keep `restricted` as warn/audit — via the
namespace label, or on Talos by patching the admission default back with `talosctl patch mc
--mode=no-reboot`.

**Two diagnostic traps.** Once `restricted` is only *warn*, the operator's `would violate PodSecurity`
log line is a **false positive** — it is emitted for backups that then succeed, so never judge breakage
from it. And runner pods are garbage-collected immediately, so read the Backup objects instead:
`kubectl get backups.k8up.io -A` — note the `.k8up.io` suffix, since a bare `backup` collides with the
MariaDB CRD. To check posture directly, use a server-side dry-run (`kubectl run pss --image=busybox
--dry-run=server …`; "pod created" means baseline admits it).
