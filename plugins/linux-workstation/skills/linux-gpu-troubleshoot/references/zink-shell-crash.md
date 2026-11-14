# Getting the core for a shell that dies in zink (Topic 5, Symptom A)

The shell's crash handler catches SIGBUS and exits deliberately (the unit records a bare
`status=1/FAILURE`), and two things block a core; lifting only one gets nothing:

- A policy drop-in setting `Storage=none` **and** `ProcessSizeMax=0` in
  `/etc/systemd/coredump.conf.d/`. Override both in a drop-in that sorts **after** the policy's file; a
  `99-` name loses because digits sort before letters. Confirm with
  `systemd-analyze cat-config systemd/coredump.conf` before reproducing.
- The shell's own crash handler (a debug env var that only suppresses the crash *dialog* still lets the
  handler swallow the signal).

Signature in `coredumpctl info`: `memcpy -> util_copy_box -> zink_image_subdata -> st_TexImage ->
_mesa_TexImage2D -> ...TextureUploader::textureImage`. `zink_*` plus `libgallium` in a shell backtrace is
the whole finding; no debuginfo needed. `rpm -q systemd-coredump` is a false negative on el9 (the binary
ships in `systemd-udev`).
