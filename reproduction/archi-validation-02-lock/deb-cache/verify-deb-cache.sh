#!/bin/sh
set -eu

fail() {
	printf 'verify-deb-cache: ERROR: %s\n' "$*" >&2
	exit 1
}

usage() {
	printf 'Usage: %s CACHE_DIRECTORY\n' "$0" >&2
	exit 2
}

[ "$#" -eq 1 ] || usage
MANIFEST_DIR=$(CDPATH= cd -P "$(dirname "$0")" && pwd)
CACHE_DIR=$(CDPATH= cd -P "$1" 2>/dev/null && pwd) || fail "cache directory not found: $1"
LOCK_DIR=$(CDPATH= cd -P "$MANIFEST_DIR/.." && pwd)

[ "$(cat "$CACHE_DIR/STATUS" 2>/dev/null || :)" = COMPLETE ] ||
	fail "cache STATUS is not COMPLETE"

deb_count=$(find "$CACHE_DIR" -type f -name '*.deb' | wc -l | tr -d ' ')
[ "$deb_count" -eq 1086 ] || fail "found $deb_count .deb files; expected 1086"
part_count=$(find "$CACHE_DIR" -type f -name '*.part' | wc -l | tr -d ' ')
[ "$part_count" -eq 0 ] || fail "found $part_count partial files"

for name in PACKAGES.tsv SOURCES.tsv SHA256SUMS DEB-CACHE-PRESENT.tsv \
	DEB-CACHE-MISSING.tsv DEB-DOWNLOAD-PLAN.tsv DEB-UNRESOLVED-PLAN.tsv; do
	[ -f "$MANIFEST_DIR/$name" ] || fail "tracked manifest missing: $name"
done
[ -f "$LOCK_DIR/PACKAGES.tsv" ] || fail "lock package inventory missing"

TAB=$(printf '\t')
tail -n +2 "$MANIFEST_DIR/PACKAGES.tsv" |
	LC_ALL=C sort -c -t "$TAB" -k1,1 -k2,2 -k3,3 2>/dev/null ||
	fail "PACKAGES.tsv is not sorted"
awk -F '\t' '
NR == 1 { if ($0 != "package\tversion\tarchitecture\tfile") exit 2; next }
NF != 4 || $1 == "" || $2 == "" || $3 == "" || $4 == "" { exit 2 }
{
	key = $1 FS $2 FS $3
	if (++keys[key] != 1 || ++files[$4] != 1 || $4 ~ /\// || $4 !~ /\.deb$/) exit 2
	v = $2
	sub(/^[^:]*:/, "", v)
	if ($4 != $1 "_" v "_" $3 ".deb") exit 2
	count++
}
END { if (count != 1086) exit 2 }
' "$MANIFEST_DIR/PACKAGES.tsv" || fail "invalid package manifest"

awk -F '\t' -v lock_packages="$LOCK_DIR/PACKAGES.tsv" '
FILENAME == lock_packages {
	if (FNR > 1) lock[$1 FS $2 FS $3]++
	next
}
FNR == 1 { if ($0 != "package\tversion\tarchitecture\tfile") exit 2; next }
NF != 4 { exit 2 }
{
	key = $1 FS $2 FS $3
	cache[key]++
	if (!(key in lock) || cache[key] != 1) exit 2
}
END {
	for (key in lock) { if (lock[key] != 1 || !(key in cache)) exit 2; lock_count++ }
	for (key in cache) cache_count++
	if (lock_count != 1086 || cache_count != 1086) exit 2
}' "$LOCK_DIR/PACKAGES.tsv" "$MANIFEST_DIR/PACKAGES.tsv" ||
	fail "cache package list is not a bijection with the userspace lock"

awk -F '\t' -v packages="$MANIFEST_DIR/PACKAGES.tsv" '
FILENAME == packages {
	if (FNR > 1) {
		key = $1 FS $2 FS $3
		package_file[key] = $4
		package_count++
	}
	next
}
FNR == 1 { if ($0 != "package\tversion\tarchitecture\torigin\turl\treference_size\treference_sha256\tpublished_sha1\tlocal_sha256\tfile") exit 2; next }
NF != 10 || $1 == "" || $2 == "" || $3 == "" || $5 == "" || $10 == "" { exit 2 }
{
	key = $1 FS $2 FS $3
	if (++keys[key] != 1 || !(key in package_file) || package_file[key] != $10) exit 2
	sources_count++
	if ($4 == "local-cache" || $4 == "Debian:debian-trixie-main") {
		if (length($7) != 64 || $7 ~ /[^0-9a-f]/ || $8 != "not-published" || length($9) != 64) exit 2
		if ($4 == "local-cache") local++
		else debian++
	} else if ($4 == "Debian-Snapshot" || $4 == "Mobian-keyring-Debian-Snapshot") {
		if ($7 != "not-indicated-by-snapshot" || length($8) != 40 || $8 ~ /[^0-9a-f]/ || length($9) != 64) exit 2
		if ($4 == "Debian-Snapshot") snapshot++
		else mobian++
	}
	else exit 2
}
END {
	for (key in package_file) if (!(key in keys)) exit 2
	if (package_count != 1086 || sources_count != 1086 || local != 772 || debian != 301 || snapshot != 12 || mobian != 1) exit 2
}' "$MANIFEST_DIR/PACKAGES.tsv" "$MANIFEST_DIR/SOURCES.tsv" || fail "invalid provenance manifest or source counts"

awk -F '\t' -v sums="$MANIFEST_DIR/SHA256SUMS" '
FILENAME == sums { split($0, fields, /[[:space:]]+/); checksum[fields[2]] = fields[1]; next }
FNR == 1 { next }
NF != 10 || !($10 in checksum) || $9 != checksum[$10] { exit 2 }
{ count++ }
END { if (count != 1086) exit 2 }
' "$MANIFEST_DIR/SHA256SUMS" "$MANIFEST_DIR/SOURCES.tsv" ||
	fail "SOURCES.tsv local hashes do not match SHA256SUMS"

check_plan() {
	file=$1
	expected=$2
	fields=$3
	key=$4
	rows=$(awk -F '\t' -v fields="$fields" 'NR == 1 { next } NF != fields { exit 2 } END { print NR - 1 }' "$MANIFEST_DIR/$file") ||
		fail "invalid columns in $file"
	[ "$rows" -eq "$expected" ] || fail "$file has $rows rows; expected $expected"
	tail -n +2 "$MANIFEST_DIR/$file" | LC_ALL=C sort -c -t "$TAB" $key 2>/dev/null ||
		fail "$file is not sorted"
}
check_plan DEB-CACHE-PRESENT.tsv 772 6 '-k1,1 -k2,2 -k3,3'
check_plan DEB-CACHE-MISSING.tsv 314 4 '-k1,1 -k2,2 -k3,3'
check_plan DEB-DOWNLOAD-PLAN.tsv 301 8 '-k1,1 -k2,2 -k3,3 -k4,4 -k5,5'
check_plan DEB-UNRESOLVED-PLAN.tsv 13 11 '-k1,1 -k2,2 -k3,3'

awk -F '\t' '
NR == 1 { if ($0 != "package\tversion\tarchitecture\tstatus") exit 2; next }
NF != 4 { exit 2 }
{ status[$4]++; total++ }
END { if (total != 314 || status["index-only"] != 301 || status["unresolved"] != 13) exit 2 }
' "$MANIFEST_DIR/DEB-CACHE-MISSING.tsv" || fail "invalid missing-package status counts"

awk -F '\t' '
NR == 1 { if ($0 != "package\tversion\tarchitecture\trepository\tfilename\turl\tsize_bytes\tsha256") exit 2; next }
NF != 8 || $4 == "" || $5 == "" || $6 !~ /^https:\/\// || $7 !~ /^[0-9]+$/ || length($8) != 64 { exit 2 }
{ count++ }
END { if (count != 301) exit 2 }
' "$MANIFEST_DIR/DEB-DOWNLOAD-PLAN.tsv" || fail "invalid Debian download plan"

awk -F '\t' '
NR == 1 { if ($0 != "package\tversion\tarchitecture\tstatus\tsource\tfilename\turl\tsize_bytes\tsha256\tsnapshot_sha1\tnote") exit 2; next }
NF != 11 || $4 != "snapshot-sha1-only" || $5 != "debian-snapshot" || $7 !~ /^https:\/\/snapshot\.debian\.org\// || $8 !~ /^[0-9]+$/ || length($10) != 40 { exit 2 }
{ count++ }
END { if (count != 13) exit 2 }
' "$MANIFEST_DIR/DEB-UNRESOLVED-PLAN.tsv" || fail "invalid Snapshot candidate plan"

awk '
NF != 2 || length($1) != 64 || $1 ~ /[^0-9a-f]/ || $2 !~ /\.deb$/ { exit 2 }
{ if (++files[$2] != 1) exit 2; count++ }
END { if (count != 1086) exit 2 }
' "$MANIFEST_DIR/SHA256SUMS" || fail "invalid SHA256SUMS"
awk -v checksums="$MANIFEST_DIR/SHA256SUMS" '
FILENAME == ARGV[1] { if (FNR > 1) package[$4]++; next }
FILENAME == checksums { checksum[$2]++; next }
END {
	for (file in package) { if (package[file] != 1 || checksum[file] != 1) exit 2; package_count++ }
	for (file in checksum) { if (checksum[file] != 1 || !(file in package)) exit 2; checksum_count++ }
	if (package_count != 1086 || checksum_count != 1086) exit 2
}' "$MANIFEST_DIR/PACKAGES.tsv" "$MANIFEST_DIR/SHA256SUMS" ||
	fail "SHA256SUMS file set differs from PACKAGES.tsv"

while IFS="$TAB" read -r package version architecture file; do
	[ "$package" = package ] && continue
	[ -f "$CACHE_DIR/$file" ] || fail "missing archive: $file"
	[ "$(dpkg-deb -f "$CACHE_DIR/$file" Package)" = "$package" ] || fail "Package mismatch: $file"
	[ "$(dpkg-deb -f "$CACHE_DIR/$file" Version)" = "$version" ] || fail "Version mismatch: $file"
	[ "$(dpkg-deb -f "$CACHE_DIR/$file" Architecture)" = "$architecture" ] || fail "Architecture mismatch: $file"
done < "$MANIFEST_DIR/PACKAGES.tsv"

(CDPATH= cd "$CACHE_DIR" && sha256sum -c "$MANIFEST_DIR/SHA256SUMS" --quiet) ||
	fail "SHA-256 verification failed"

printf 'OK: verified 1086 packages against %s\n' "$CACHE_DIR"
