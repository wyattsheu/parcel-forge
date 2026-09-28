#!/usr/bin/env bash
set -euo pipefail

STUDENT_USER="${STUDENT_USER:-studentdev}"
STUDENT_UID="${STUDENT_UID:-20001}"
STUDENT_GID="${STUDENT_GID:-20001}"

# --- 1. Ensure SSH host keys exist (persisted via /etc/ssh volume) ---
ssh-keygen -A

# --- 2. Ensure the student's home (persisted volume) has correct ownership/perms ---
mkdir -p "/home/${STUDENT_USER}/.ssh"
chown -R "${STUDENT_UID}:${STUDENT_GID}" "/home/${STUDENT_USER}"
chmod 700 "/home/${STUDENT_USER}/.ssh"
if [ -f "/home/${STUDENT_USER}/.ssh/authorized_keys" ]; then
  chmod 600 "/home/${STUDENT_USER}/.ssh/authorized_keys"
  chown "${STUDENT_UID}:${STUDENT_GID}" "/home/${STUDENT_USER}/.ssh/authorized_keys"
fi

mkdir -p /workspace
chown "${STUDENT_UID}:${STUDENT_GID}" /workspace

CHILD_PIDS=()

term_handler() {
  echo "Received SIGTERM/SIGINT, shutting down..." >&2
  for pid in "${CHILD_PIDS[@]}"; do
    kill -TERM "$pid" 2>/dev/null || true
  done
  for pid in "${CHILD_PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  exit 0
}
trap term_handler SIGTERM SIGINT

# --- 3. Start sshd (foreground-capable daemon, backgrounded here so we can also run code-server) ---
/usr/sbin/sshd -D -e &
CHILD_PIDS+=("$!")

# --- 4. Start code-server as the student user, if it is installed ---
if command -v code-server >/dev/null 2>&1; then
  # No --auth none: code-server auto-generates a random password on first run
  # and persists it (in the studentdev home volume) at
  # ~/.config/code-server/config.yaml. Only someone with container SSH access
  # (the container key, not the gateway key) can read it. This keeps the
  # gateway key from being equivalent to a shell via the web IDE's terminal.
  su -s /bin/bash "${STUDENT_USER}" -c \
    "code-server --bind-addr 0.0.0.0:8080 /workspace" &
  CHILD_PIDS+=("$!")
else
  echo "code-server not installed; skipping." >&2
fi

# --- 5. Wait on all children; exit when any dies, forward signals correctly ---
wait -n "${CHILD_PIDS[@]}"
term_handler
