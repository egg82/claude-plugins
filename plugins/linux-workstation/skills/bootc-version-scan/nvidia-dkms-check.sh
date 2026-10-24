#!/usr/bin/env bash
# Builds the NVIDIA dkms module a GPU-enabled image builds, against
# kernel-ml-devel for each kernel given, inside a throwaway EL9-family container
# (AlmaLinux 9 in the example; any EL9 rebuild works).
# Pass the CURRENT pin first as a control: if it fails too, the harness is
# broken, not the candidate kernel.
#
#   podman run --rm -e ELREPO_ARCHIVE=<archive base URL> -v "$PWD/nvidia-dkms-check.sh:/t.sh:ro,Z" \
#     docker.io/library/almalinux:9 bash /t.sh <current-pin> <candidate-pin>
#
# ELREPO_ARCHIVE (required): base URL of an ELRepo kernel archive that holds the older kernel-ml
# builds, laid out as <base>/archive/kernel/el9/<arch>/ (use your preferred ELRepo mirror).
#
# ~15 min, a few GB of container storage; remove the almalinux image afterwards.
set -euo pipefail
: "${ELREPO_ARCHIVE:?set ELREPO_ARCHIVE to an ELRepo mirror base URL (see header)}"
echo "retries=10" >> /etc/dnf/dnf.conf
dnf -y -q install epel-release dnf-plugins-core >/dev/null
rpm --import https://www.elrepo.org/RPM-GPG-KEY-v2-elrepo.org
dnf -y -q install https://www.elrepo.org/elrepo-release-9.el9.elrepo.noarch.rpm >/dev/null
dnf -y -q config-manager --set-enabled elrepo-kernel
# the live elrepo repo carries only the newest kernels; older pins live here
cat > /etc/yum.repos.d/elrepo-archive.repo <<EOF
[elrepo-kernel-archive]
name=elrepo archive
baseurl=${ELREPO_ARCHIVE%/}/archive/kernel/el9/\$basearch/
gpgcheck=1
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-v2-elrepo.org
EOF
for kv in "$@"; do dnf -y -q install "kernel-ml-devel-${kv}" >/dev/null; done
dnf -y -q install gcc make elfutils-libelf-devel dkms >/dev/null
dnf -y -q config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo
dnf -y -q module reset nvidia-driver >/dev/null
dnf -y -q module enable nvidia-driver:latest-dkms >/dev/null
dnf -y -q install nvidia-kmod-common kmod-nvidia-latest-dkms >/dev/null
nver="$(find /usr/src -maxdepth 1 -name 'nvidia-*' -printf '%f\n' | sort -V | tail -n1 | sed 's/^nvidia-//')"
for kv in "$@"; do
  kver="${kv}.x86_64"
  # NVIDIA's Makefile hard-codes /lib/modules/<kver>/build, which kernel-ml-core
  # would provide; -devel alone does not
  mkdir -p "/lib/modules/${kver}"
  ln -sfn "/usr/src/kernels/${kver}" "/lib/modules/${kver}/build"
  echo "--- nvidia=${nver} kernel=${kver}"
  if dkms build -m nvidia -v "${nver}" -k "${kver}" \
       --kernelsourcedir "/usr/src/kernels/${kver}" > "/tmp/dkms-${kv}.log" 2>&1; then
    echo "DKMS_BUILD_OK ${kver}"
  else
    echo "DKMS_BUILD_FAILED ${kver}"
    tail -25 "/var/lib/dkms/nvidia/${nver}/build/make.log" 2>/dev/null || tail -25 "/tmp/dkms-${kv}.log"
  fi
done
