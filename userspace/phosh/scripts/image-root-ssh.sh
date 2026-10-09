#!/usr/bin/env bash
# Sourced by the builder. These functions affect only its derived image tree.
load_image_root_ssh_key() {
    m1_ssh_public_key=''
    local key_file=${1:-} key_type key_blob key_comment
    [[ -n $key_file ]] || return 0
    [[ -f $key_file && $(stat -c %s -- "$key_file") -le 16384 ]] || {
        echo 'SSH key input must be a regular public-key file of at most 16 KiB' >&2
        return 1
    }
    m1_ssh_public_key=$(cat -- "$key_file") || return 1
    # Windows OpenSSH public keys commonly end in CRLF. Normalize only the
    # terminal CR; embedded CR/newlines and multiple keys remain invalid.
    m1_ssh_public_key=${m1_ssh_public_key%$'\r'}
    [[ -n $m1_ssh_public_key && $m1_ssh_public_key != *$'\n'* && $m1_ssh_public_key != *$'\r'* ]] || {
        echo 'SSH key input must contain one OpenSSH public-key line' >&2
        return 1
    }
    read -r key_type key_blob key_comment <<<"$m1_ssh_public_key"
    case "$key_type" in
        ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521|sk-ssh-ed25519@openssh.com|sk-ecdsa-sha2-nistp256@openssh.com) ;;
        *) echo 'SSH key input must be a public key, without authorized_keys options' >&2; return 1 ;;
    esac
    ssh-keygen -l -f "$key_file" >/dev/null 2>&1 || {
        echo 'Invalid OpenSSH public key' >&2
        return 1
    }
}

configure_image_root_ssh() {
    local tree=$1
    [[ -d $tree/root && ! -L $tree/root && ! -L $tree/root/.ssh ]] || return 1
    install -d -o root -g root -m 0700 "$tree/root/.ssh" || return 1
    [[ ! -L $tree/root/.ssh/authorized_keys ]] || return 1
    [[ ! -e $tree/root/.ssh/authorized_keys || -f $tree/root/.ssh/authorized_keys ]] || return 1
    # Replace inherited authorizations only in the newly copied image tree.
    # Unlink first so an inherited hard link cannot modify another file.
    rm -f -- "$tree/root/.ssh/authorized_keys" || return 1
    install -o root -g root -m 0600 /dev/null "$tree/root/.ssh/authorized_keys" || return 1
    if [[ -n $m1_ssh_public_key ]]; then
        printf '%s\n' "$m1_ssh_public_key" >"$tree/root/.ssh/authorized_keys" || return 1
    fi
}

verify_image_root_ssh() {
    local tree=$1
    [[ ! -L $tree/root && ! -L $tree/root/.ssh && ! -L $tree/root/.ssh/authorized_keys ]] || return 1
    [[ $(stat -c '%u:%g:%a' "$tree/root/.ssh") == 0:0:700 ]] || return 1
    [[ $(stat -c '%u:%g:%a' "$tree/root/.ssh/authorized_keys") == 0:0:600 ]] || return 1
    if [[ -n $m1_ssh_public_key ]]; then
        cmp -s <(printf '%s\n' "$m1_ssh_public_key") "$tree/root/.ssh/authorized_keys" || return 1
    else
        [[ ! -s $tree/root/.ssh/authorized_keys ]] || return 1
    fi
}
