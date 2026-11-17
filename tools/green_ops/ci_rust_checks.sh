# SPDX-FileCopyrightText: 2026 Parth Shailesh Thite
# SPDX-License-Identifier: MIT OR Apache-2.0

# Invoke with bash from repository root. Compilation/tests only; no flash or radio.
set -euo pipefail

toolchain=${GREEN_OPS_RUST_TOOLCHAIN:-1.99.1}
version=$(rustup run "$toolchain" rustc --version)
if [[ "$version" != 'rustc 1.99.1 '* ]]; then
    echo 'Expected pinned rustc1.99.1; select an installed matching toolchain.' >&2
    exit 1
fi

# Same host-compatible exclusions as test/05_cargotest.sh, with lock enforced.
rustup run "$toolchain" cargo test --locked --workspace --exclude hophop --exclude nrfxlib-sys-pretty
rustup run "$toolchain" cargo test --locked --workspace --all-features --exclude hophop --exclude nrfxlib-sys-pretty

# Documented standalone telemetry checks; this is not a full firmware build/link.
mkdir -p build/green-ops-ci
rustup run "$toolchain" rustc --edition=2024 -D warnings --test examples/src/green_ops_telemetry.rs -o build/green-ops-ci/telemetry-tests
build/green-ops-ci/telemetry-tests
printf '%s\n' '#![no_std]' '#[path = "../../examples/src/green_ops_telemetry.rs"]' 'pub mod telemetry;' > build/green-ops-ci/no_std_check.rs
rustup run "$toolchain" rustc --edition=2024 --crate-type lib --target thumbv8m.main-none-eabihf -D warnings build/green-ops-ci/no_std_check.rs -o build/green-ops-ci/libtelemetry_check.rlib
