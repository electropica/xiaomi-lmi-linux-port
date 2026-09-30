# Bash helpers for tracking only loop devices backed by the current working image.
# The caller provides WORK_RAW, SECTOR_SIZE, LOOP_DEV and fail().

loop_path_is_valid() {
    [[ ${1-} =~ ^/dev/loop[0-9]+$ ]]
}

loop_list_for_work_image() {
    local listing name backing extra
    local -a matches=()
    [[ -n ${WORK_RAW:-} && -f $WORK_RAW ]] || return 1
    listing=$(losetup --list --noheadings --raw --output NAME,BACK-FILE) || return 2
    while IFS=$' \t' read -r name backing extra; do
        [[ -n $name && -n $backing && -z ${extra:-} ]] || continue
        loop_path_is_valid "$name" || continue
        [[ $backing == "$WORK_RAW" ]] && matches+=("$name")
    done <<< "$listing"
    ((${#matches[@]} == 1)) || return $((${#matches[@]} == 0 ? 1 : 2))
    printf '%s\n' "${matches[0]}"
}

loop_device_is_owned() {
    local wanted=$1 listing name backing extra
    loop_path_is_valid "$wanted" || return 1
    [[ -n ${WORK_RAW:-} && -f $WORK_RAW ]] || return 1
    listing=$(losetup --list --noheadings --raw --output NAME,BACK-FILE) || return 2
    while IFS=$' \t' read -r name backing extra; do
        [[ -n $name && -n $backing && -z ${extra:-} ]] || continue
        [[ $name == "$wanted" && $backing == "$WORK_RAW" ]] && return 0
    done <<< "$listing"
    return 1
}

attach_work_loop() {
    local output
    LOOP_DEV=
    output=$(losetup --find --show --partscan --sector-size "$SECTOR_SIZE" "$WORK_RAW") || return 1
    loop_path_is_valid "$output" || return 1
    if loop_device_is_owned "$output"; then
        LOOP_DEV=$output
        return 0
    fi
    return 1
}

detach_owned_loop() {
    local candidate=${LOOP_DEV:-} rc

    if loop_path_is_valid "$candidate"; then
        if loop_device_is_owned "$candidate"; then
            :
        else
            rc=$?
            # A stale device, or a device now backed by another image, is never detached.
            if ((rc > 1)); then
                printf 'ERROR: cannot verify loop ownership; leaving device untouched\n' >&2
                return 1
            fi
            candidate=
        fi
    elif [[ -n $candidate ]]; then
        printf 'NOTICE: ignoring invalid loop path: %s\n' "$candidate" >&2
        candidate=
    fi

    if [[ -z $candidate ]]; then
        if candidate=$(loop_list_for_work_image); then
            :
        else
            rc=$?
            LOOP_DEV=
            if ((rc == 1)); then return 0; fi
            printf 'ERROR: cannot uniquely identify this attempt loop; leaving devices untouched\n' >&2
            return 1
        fi
    fi

    loop_path_is_valid "$candidate" || {
        LOOP_DEV=
        printf 'ERROR: refused non-device loop value\n' >&2
        return 1
    }
    if loop_device_is_owned "$candidate"; then
        :
    else
        rc=$?
        if ((rc == 1)); then LOOP_DEV=; return 0; fi
        printf 'ERROR: cannot verify loop ownership; leaving device untouched\n' >&2
        return 1
    fi

    if losetup --detach "$candidate"; then
        LOOP_DEV=
        return 0
    fi

    # A failed command may still have detached the device. Recheck ownership
    # before allowing the EXIT trap to retry; a successful detach is never repeated.
    if loop_device_is_owned "$candidate"; then
        LOOP_DEV=$candidate
        return 1
    else
        rc=$?
        if ((rc == 1)); then LOOP_DEV=; return 0; fi
        LOOP_DEV=$candidate
        return 1
    fi
}
