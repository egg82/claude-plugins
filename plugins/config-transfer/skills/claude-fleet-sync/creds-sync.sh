#!/usr/bin/env bash
# Fleet sync for systemd-creds secrets so every ONLINE host holds the SAME secrets.
#
# WHY THIS IS SEPARATE FROM sync.py:
#   credstore secrets are encrypted against each host's own
#   /var/lib/systemd/credential.secret (and/or TPM2) — the ciphertext is NOT
#   portable. Making a secret fleet-wide means: decrypt on a host that has it, then
#   re-encrypt with each TARGET host's own key. That needs root on every host.
#
# WHAT IT DOES:
#   - Discovers .cred files in BOTH credstores, by logical identity:
#       system : /etc/credstore.encrypted/<name>.cred         (root-owned)
#       user   : $HOME/.config/*/<name>.cred                  (e.g. ~/.config/<app>/)
#   - For each cred, the SOURCE OF TRUTH is the host whose copy has the newest mtime.
#   - Under --apply, it re-encrypts that secret with every other live host's own key
#     (decrypt-on-source | encrypt-on-target via an ssh pipe; plaintext only streams
#     through fds, never written to disk) so all hosts end up with the same value.
#
# SAFETY:
#   - Default is a DRY RUN: inventory by NAME only, no decryption, prints the plan.
#   - Decryption happens ONLY under --apply.
#   - Run under bash (NOT zsh): zsh won't word-split $SSH. The shebang enforces bash.
#
# Usage:
#   creds-sync.sh                 # dry-run: inventory + plan
#   creds-sync.sh --apply         # make every live host's secrets identical (newest wins)
#   creds-sync.sh --apply host... # restrict to given hosts
set -uo pipefail

# PLACEHOLDERS — replace with your own hostnames, or pass hosts as positional args
# (which is what `sync.py creds` does: it forwards the live host set).
FLEET_DEFAULT=("<host-a>" "<host-b>")
SSH="ssh -o BatchMode=yes -o ConnectTimeout=8 -o LogLevel=ERROR"
SYS_STORE=/etc/credstore.encrypted

APPLY=0; HOSTS=()
for a in "$@"; do
  case "$a" in
    --apply) APPLY=1 ;;
    -*)      echo "unknown flag: $a" >&2; exit 2 ;;
    *)       HOSTS+=("$a") ;;
  esac
done
[ ${#HOSTS[@]} -eq 0 ] && HOSTS=("${FLEET_DEFAULT[@]}")
# Refuse the placeholder roster rather than "succeeding" with an empty plan: ssh to <host-a>
# fails, rhome() swallows the error, and the dry run then looks identical to "no creds anywhere".
case "${HOSTS[*]}" in
  *"<"*) echo "refusing to run: FLEET_DEFAULT is still the placeholder roster — pass hosts as arguments or edit it" >&2; exit 1 ;;
esac
log(){ echo "[creds-sync] $*" >&2; }

# remote home dir (ask the host rather than assuming: $HOME may be a symlinked mount)
rhome(){ $SSH "$1" 'echo $HOME' 2>/dev/null; }

# List "relpath|abspath|mtime" for every cred on a host (system + user), names only.
list_creds(){
  local h home; h=$1; home=$(rhome "$h"); [ -z "$home" ] && return 0
  # system store (sudo to stat; names are not secret)
  $SSH "$h" "sudo -n sh -c 'for f in $SYS_STORE/*.cred; do [ -e \"\$f\" ] || continue; printf \"sys:%s|%s|%s\\n\" \"\$(basename \"\$f\")\" \"\$f\" \"\$(stat -c%Y \"\$f\")\"; done'" 2>/dev/null
  # user store: $HOME/.config/*/*.cred
  $SSH "$h" "for f in $home/.config/*/*.cred; do [ -e \"\$f\" ] || continue; printf 'usr:%s|%s|%s\n' \"\${f#$home/}\" \"\$f\" \"\$(stat -c%Y \"\$f\")\"; done" 2>/dev/null
}

# cred NAME (for systemd-creds --name) = filename without .cred
credname(){ local b; b=$(basename "$1"); echo "${b%.cred}"; }

# --- reachability ---
LIVE=()
for h in "${HOSTS[@]}"; do
  if $SSH "$h" true 2>/dev/null; then LIVE+=("$h"); else log "WARNING unreachable, skipping: $h"; fi
done
[ ${#LIVE[@]} -ge 2 ] || { log "need >=2 reachable hosts"; exit 1; }
log "live hosts: ${LIVE[*]}"

# --- inventory: identity -> "host:abspath:mtime ..." ---
declare -A WHERE   # identity -> space-list of host\tabspath\tmtime
for h in "${LIVE[@]}"; do
  while IFS='|' read -r ident abspath mtime; do
    [ -n "$ident" ] || continue
    WHERE["$ident"]+="$h	$abspath	$mtime "
  done < <(list_creds "$h")
done
[ ${#WHERE[@]} -gt 0 ] || { log "no creds discovered"; exit 0; }

echo "[creds-sync] inventory:"
for ident in "${!WHERE[@]}"; do
  printf "  %s\n" "$ident"
  echo "${WHERE[$ident]}" | tr ' ' '\n' | awk -F'\t' 'NF>=2{printf "      %s  %s\n",$1,$2}'
done

# --- plan + apply: source = newest mtime; push to every other live host ---
ACTIONS=0
for ident in "${!WHERE[@]}"; do
  scope=${ident%%:*}            # sys|usr
  # pick source-of-truth = newest mtime. WHERE[$ident] is a flat whitespace list of
  # (host path mtime) triplets, so positional parsing in steps of 3 is reliable.
  src_host=""; src_path=""; src_mtime=-1
  set -- ${WHERE[$ident]}
  while [ $# -ge 3 ]; do
    h=$1; p=$2; m=$3; shift 3
    if [ "${m:-0}" -gt "$src_mtime" ]; then src_mtime=$m; src_host=$h; src_path=$p; fi
  done
  name=$(credname "$src_path")
  for h in "${LIVE[@]}"; do
    have=""; set -- ${WHERE[$ident]}
    while [ $# -ge 3 ]; do [ "$1" = "$h" ] && have=$2; shift 3; done
    if [ "$h" = "$src_host" ]; then continue; fi
    if [ -n "$have" ]; then action="refresh(identical-or-overwrite)"; else action="create"; fi
    [ "$APPLY" = 1 ] || { echo "  PLAN $ident: $src_host -> $h  [$action] name=$name"; ACTIONS=$((ACTIONS+1)); continue; }
    # idempotency: if target already decrypts to the same secret, leave it (avoids
    # needless re-encryption and mtime churn that would bounce the source each run).
    # Decrypt with --name= (empty) so the embedded-name check never blocks the compare:
    # a legacy cred whose embedded name != its filename must still be readable here. The
    # AEAD still authenticates the plaintext; only the cosmetic name label is skipped.
    if [ -n "$have" ]; then
      empty_sha=$(printf '' | sha256sum | cut -d' ' -f1)
      sh_src=$($SSH "$src_host" "sudo -n systemd-creds decrypt --name= $src_path - 2>/dev/null | sha256sum | cut -d' ' -f1")
      sh_tgt=$($SSH "$h" "sudo -n systemd-creds decrypt --name= $have - 2>/dev/null | sha256sum | cut -d' ' -f1")
      if [ -n "$sh_src" ] && [ "$sh_src" != "$empty_sha" ] && [ "$sh_src" = "$sh_tgt" ]; then log "  identical, skip: $ident -> $h"; continue; fi
    fi
    echo "  APPLY $ident: $src_host -> $h  [$action] name=$name"
    ACTIONS=$((ACTIONS+1))
    # determine target path + owner
    if [ "$scope" = sys ]; then tgt_path="$SYS_STORE/$name.cred"; owner=root; ginst="root"; else
      thome=$(rhome "$h"); tgt_path="$thome/${ident#usr:}"; owner=$($SSH "$h" 'id -un'); ginst=$($SSH "$h" 'id -gn'); fi
    # decrypt on source -> re-encrypt with the TARGET host's own key (plaintext only in
    # the pipe). Source decrypt uses --name= (empty) to bypass the embedded-name check so
    # a legacy cred whose embedded name != filename still decrypts; the target is always
    # (re-)written with --name=$name, normalizing every host's copy to the filename
    # convention. BOTH pipe stages are checked: a refused decrypt yields an empty pipe
    # that `encrypt` would otherwise wrap into a bogus cred and exit 0 (the original bug).
    $SSH "$src_host" "sudo -n systemd-creds decrypt --name= $src_path -" \
      | $SSH "$h" "sudo -n systemd-creds encrypt --name=$name - /run/cs.$$.cred"
    cs_ps=("${PIPESTATUS[@]}")
    if [ "${cs_ps[0]:-1}" -ne 0 ] || [ "${cs_ps[1]:-1}" -ne 0 ]; then
      log "  FAILED $ident -> $h (decrypt rc=${cs_ps[0]:-?}, encrypt rc=${cs_ps[1]:-?}) — not installing"
      $SSH "$h" "sudo -n rm -f /run/cs.$$.cred" 2>/dev/null
      continue
    fi
    $SSH "$h" "sudo -n mkdir -p \"\$(dirname $tgt_path)\"; sudo -n install -o $owner -g $ginst -m 600 /run/cs.$$.cred $tgt_path && sudo -n rm -f /run/cs.$$.cred"
    # verify the INSTALLED cred decrypts back to the same secret before declaring success
    empty_sha=$(printf '' | sha256sum | cut -d' ' -f1)
    v_src=$($SSH "$src_host" "sudo -n systemd-creds decrypt --name= $src_path - 2>/dev/null | sha256sum | cut -d' ' -f1")
    v_tgt=$($SSH "$h" "sudo -n systemd-creds decrypt --name=$name $tgt_path - 2>/dev/null | sha256sum | cut -d' ' -f1")
    if [ -n "$v_src" ] && [ "$v_src" != "$empty_sha" ] && [ "$v_src" = "$v_tgt" ]; then
      log "  done $ident -> $h ($tgt_path)"
    else
      log "  ERROR verify FAILED $ident -> $h — installed cred does NOT match source (src=$v_src tgt=$v_tgt)"
    fi
  done
done

if [ "$APPLY" != 1 ]; then
  log "DRY RUN ($ACTIONS action(s) planned) — re-run with --apply to make secrets identical."
else
  log "DONE ($ACTIONS action(s))."
fi
