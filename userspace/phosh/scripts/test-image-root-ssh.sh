#!/usr/bin/env bash
# Run as root; all writes are confined to a disposable temporary directory.
set -euo pipefail
[[ $(id -u) == 0 ]] || { echo 'Run this isolated ownership test as root' >&2; exit 2; }
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
source "$script_dir/image-root-ssh.sh"
tmp=$(mktemp -d)
trap 'rm -rf -- "$tmp"' EXIT
mkdir -p "$tmp/image/root/.ssh"
printf 'inherited authorization\n' >"$tmp/original"
ln "$tmp/original" "$tmp/image/root/.ssh/authorized_keys"
load_image_root_ssh_key ''
configure_image_root_ssh "$tmp/image"
verify_image_root_ssh "$tmp/image"
grep -qx 'inherited authorization' "$tmp/original"
[[ ! -s $tmp/image/root/.ssh/authorized_keys ]]

ssh-keygen -q -t ed25519 -N '' -C synthetic-build-test -f "$tmp/test-key"
load_image_root_ssh_key "$tmp/test-key.pub"
configure_image_root_ssh "$tmp/image"
verify_image_root_ssh "$tmp/image"
cmp "$tmp/test-key.pub" "$tmp/image/root/.ssh/authorized_keys"
expect_rejected_key() {
    if load_image_root_ssh_key "$1" 2>/dev/null; then
        echo 'Invalid key input unexpectedly accepted' >&2; exit 1
    fi
}
expect_rejected_key "$tmp/test-key"
expect_rejected_key "$tmp/missing"
cat "$tmp/test-key.pub" "$tmp/test-key.pub" >"$tmp/two-keys"
expect_rejected_key "$tmp/two-keys"
printf 'ssh-ed25519 invalid test\n' >"$tmp/invalid"
expect_rejected_key "$tmp/invalid"
printf 'command="true" ' >"$tmp/options"
cat "$tmp/test-key.pub" >>"$tmp/options"
expect_rejected_key "$tmp/options"
head -c 16385 /dev/zero >"$tmp/oversized"
expect_rejected_key "$tmp/oversized"

load_image_root_ssh_key ''
rm "$tmp/image/root/.ssh/authorized_keys"
ln -s "$tmp/original" "$tmp/image/root/.ssh/authorized_keys"
if configure_image_root_ssh "$tmp/image"; then
    echo 'Symlink authorization unexpectedly accepted' >&2; exit 1
fi
grep -qx 'inherited authorization' "$tmp/original"
rm "$tmp/image/root/.ssh/authorized_keys"
mv "$tmp/image/root/.ssh" "$tmp/ssh-outside"
ln -s "$tmp/ssh-outside" "$tmp/image/root/.ssh"
if configure_image_root_ssh "$tmp/image"; then
    echo 'Symlink SSH directory unexpectedly accepted' >&2; exit 1
fi
echo 'PASS: default empty authorizations, explicit public key, invalid inputs, hard-link isolation and symlink refusal'
