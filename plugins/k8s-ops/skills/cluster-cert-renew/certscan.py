#!/usr/bin/env python3
"""Report how long the cluster admin certs have left, and alert on anything near expiry.

Two sources, both scanned on the host this runs on:
  kubeconfig    $KUBECONFIG_PATH  (default ~/.kube/config)   client certs kubectl presents
  talosconfig   $TALOS_GLOB       (default ~/.talos/*/talosconfig)
                                                             os:admin certs talosctl presents

  check   print a table of every cert found (always exits 0 unless the scan itself broke)
  notify  same scan, but POST to a chat webhook when something needs attention

A source that cannot be read is reported as UNKNOWN and *does* trigger a notification.
A silent scan and a healthy fleet must never look the same.
"""
import argparse
import base64
import datetime
import glob
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.request

WARN_DAYS = 30
KUBECONFIG = os.path.expanduser(os.environ.get("KUBECONFIG_PATH", "~/.kube/config"))
# One directory per cluster, each holding that cluster's talosconfig. Point $TALOS_GLOB
# at wherever you keep them.
TALOS_GLOB = os.path.expanduser(os.environ.get("TALOS_GLOB", "~/.talos/*/talosconfig"))


class Row:
    """One cert, or one thing we could not read. status is OK / WARN / EXPIRED / UNKNOWN."""

    def __init__(self, source, name, expiry=None, note=""):
        self.source, self.name, self.expiry, self.note = source, name, expiry, note

    @property
    def days(self):
        if self.expiry is None:
            return None
        return (self.expiry - datetime.datetime.now(datetime.timezone.utc)).days

    def status(self, warn_days):
        days = self.days
        if days is None:
            return "UNKNOWN"
        if days < 0:
            return "EXPIRED"
        return "WARN" if days <= warn_days else "OK"

    def line(self, warn_days):
        when = self.expiry.strftime("%Y-%m-%d") if self.expiry else "?"
        days = f"{self.days:>5}d" if self.expiry is not None else "     ?"
        tail = f"  {self.note}" if self.note else ""
        return f"{self.source:<12} {self.name:<16} {when}  {days}  {self.status(warn_days):<7}{tail}"


def cert_expiry(pem):
    """Return the notAfter of a cert, or None if openssl can't read it.

    The base64 blob in a kube/talos config decodes to PEM text, not DER.
    """
    p = subprocess.run(["openssl", "x509", "-noout", "-enddate"],
                       input=pem, capture_output=True)
    if p.returncode != 0:
        return None
    m = re.search(r"notAfter=(.+)", p.stdout.decode())
    if not m:
        return None
    try:
        return datetime.datetime.strptime(m.group(1).strip(), "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def load_yaml(path):
    """Parse a kube/talos config. yaml isn't in the stdlib, so shell out if it's missing."""
    try:
        import yaml
        with open(path) as fh:
            return yaml.safe_load(fh)
    except ImportError:
        p = subprocess.run(["python3", "-c",
                            "import yaml,json,sys;json.dump(yaml.safe_load(open(sys.argv[1])),sys.stdout)",
                            path], capture_output=True)
        if p.returncode != 0:
            raise RuntimeError("no yaml module available")
        return json.loads(p.stdout)


def scan_kubeconfig(path):
    if not os.path.exists(path):
        return [Row("kubeconfig", "-", note=f"not found: {path}")]
    try:
        doc = load_yaml(path)
    except Exception as exc:
        return [Row("kubeconfig", "-", note=f"unreadable: {exc}")]
    rows = []
    for user in sorted(doc.get("users") or [], key=lambda u: u.get("name", "")):
        name = user.get("name", "?")
        blob = (user.get("user") or {}).get("client-certificate-data")
        if not blob:
            # exec/token/plugin auth, or a context with no client cert at all — not a cert to track
            continue
        exp = cert_expiry(base64.b64decode(blob))
        rows.append(Row("kubeconfig", name, exp, "" if exp else "cert did not parse"))
    if not rows:
        rows.append(Row("kubeconfig", "-", note="no client certs found"))
    return rows


def scan_talosconfigs(pattern):
    paths = sorted(glob.glob(pattern))
    if not paths:
        # Absence is a coverage gap, not a clean bill of health — say so out loud.
        return [Row("talosconfig", "-", note=f"not checked on this host (no {pattern})")]
    rows = []
    for path in paths:
        cluster = os.path.basename(os.path.dirname(path))
        try:
            doc = load_yaml(path)
        except Exception as exc:
            rows.append(Row("talosconfig", cluster, note=f"unreadable: {exc}"))
            continue
        for ctx_name, ctx in (doc.get("contexts") or {}).items():
            blob = (ctx or {}).get("crt")
            label = cluster if ctx_name == cluster else f"{cluster}/{ctx_name}"
            if not blob:
                rows.append(Row("talosconfig", label, note="no client cert in context"))
                continue
            exp = cert_expiry(base64.b64decode(blob))
            rows.append(Row("talosconfig", label, exp, "" if exp else "cert did not parse"))
    return rows


def scan():
    rows = scan_kubeconfig(KUBECONFIG) + scan_talosconfigs(TALOS_GLOB)
    rows.sort(key=lambda r: (r.expiry is None, r.expiry or datetime.datetime.max.replace(
        tzinfo=datetime.timezone.utc)))
    return rows


def webhook():
    """The chat webhook to POST to: straight from the env, or printed by a helper command.

    $CERT_ALERT_WEBHOOK      the URL itself
    $CERT_ALERT_WEBHOOK_CMD  a command that prints the URL on stdout, for reading it out of a
                             secret store such as Vault/OpenBao, `pass`, or sops. e.g.
                               /usr/local/bin/vault kv get -mount=<mount> -field=<field> <path>
                             Give it an ABSOLUTE path: a non-interactive SSH session (which is
                             what a scheduler gets) has none of the login profile's PATH.
    """
    url = os.environ.get("CERT_ALERT_WEBHOOK")
    if url:
        return url
    cmd = os.environ.get("CERT_ALERT_WEBHOOK_CMD")
    if not cmd:
        return ""
    argv = shlex.split(cmd)
    if not os.path.exists(argv[0]):
        print(f"[notify] webhook helper not found at {argv[0]}", file=sys.stderr)
        return ""
    p = subprocess.run(argv, text=True, capture_output=True)
    if p.returncode != 0:
        print(f"[notify] webhook helper failed: {p.stderr.strip()}", file=sys.stderr)
        return ""
    return p.stdout.strip()


def push(message):
    url = webhook()
    if not url:
        print("[notify] no webhook (set $CERT_ALERT_WEBHOOK or $CERT_ALERT_WEBHOOK_CMD)"
              " — NOT sent:\n" + message, file=sys.stderr)
        return 3
    # `content` is the field most chat webhooks take; adjust if yours differs.
    data = json.dumps({"content": message[:1900]}).encode()
    # Set a User-Agent explicitly. A chat service fronted by a CDN/WAF commonly 403s the
    # default urllib one, which reads as "the webhook URL is wrong" when it is not.
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json", "User-Agent": "cluster-cert-renew/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        print(f"[notify] webhook {resp.status}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["check", "notify"])
    ap.add_argument("--warn-days", type=int, default=WARN_DAYS,
                    help=f"flag certs expiring within this many days (default {WARN_DAYS})")
    ap.add_argument("--force", action="store_true",
                    help="notify even when everything is healthy (for testing the pipe)")
    args = ap.parse_args()

    rows = scan()
    print(f"{'SOURCE':<12} {'NAME':<16} {'EXPIRES':<10}  {'LEFT':>6}  STATUS")
    for r in rows:
        print(r.line(args.warn_days))

    bad = [r for r in rows if r.status(args.warn_days) != "OK"]
    healthy = len(rows) - len(bad)
    print(f"\n{healthy} ok, {len(bad)} needing attention (warn threshold {args.warn_days}d)")

    if args.cmd == "check":
        return 0
    if not bad and not args.force:
        print("[notify] all clear — nothing sent")
        return 0

    host = os.uname().nodename
    if bad:
        head = f"**Cluster admin certs need attention** (checked on `{host}`)"
        body = "\n".join(
            f"`{r.source:<11} {r.name:<15}` {r.status(args.warn_days)}"
            + (f" — expires {r.expiry:%Y-%m-%d} ({r.days}d)" if r.expiry else f" — {r.note}")
            for r in bad)
        tail = "\nRenew with the `cluster-cert-renew` skill *before* expiry — once the talosctl " \
               "`os:admin` cert lapses, renewal needs the CA keys from `controlplane.yaml`."
    else:
        head = f"**Cluster admin certs all healthy** (checked on `{host}`)"
        body = "\n".join(f"`{r.source:<11} {r.name:<15}` expires {r.expiry:%Y-%m-%d} ({r.days}d)"
                         for r in rows if r.expiry)
        tail = ""
    return push(f"{head}\n{body}{tail}")


if __name__ == "__main__":
    sys.exit(main())
