import os
import shutil
import socket
import subprocess

import requests


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except OSError:
        return ""


def _public_ip():
    for url in ("https://api.ipify.org", "https://ifconfig.me/ip"):
        try:
            response = requests.get(url, timeout=3)
            response.raise_for_status()
            value = response.text.strip()
            if value:
                return value
        except requests.RequestException:
            continue
    return "unavailable"


def _port_status(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(0.2)
        return "LISTEN" if client.connect_ex(("127.0.0.1", port)) == 0 else "DOWN"


def _screen_names():
    try:
        result = subprocess.run(
            ["screen", "-ls"], capture_output=True, text=True, timeout=2, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    names = []
    for line in result.stdout.splitlines():
        value = line.strip().split("\t", 1)[0]
        if "." in value and value.split(".", 1)[0].isdigit():
            names.append(value)
    return ",".join(names) or "none"


def build_status_message():
    uptime_raw = _read_text("/proc/uptime").split()
    uptime_hours = round(float(uptime_raw[0]) / 3600, 1) if uptime_raw else "unavailable"
    load = _read_text("/proc/loadavg").split()[:3]
    disk = shutil.disk_usage(os.path.abspath(os.sep))
    ports = ", ".join(
        f"{port}:{_port_status(port)}"
        for port in (6099, 23333, 23334, 23335, 7776, 7777, 7778, 7779)
    )
    return "\n".join(
        [
            "[tai261 status]",
            f"host: {socket.gethostname()}",
            f"public_ip: {_public_ip()}",
            f"uptime_hours: {uptime_hours}",
            f"loadavg: {' '.join(load) if load else 'unavailable'}",
            f"disk(/): {disk.used // (1024 ** 3)}/{disk.total // (1024 ** 3)} GiB used",
            f"ports: {ports}",
            f"screens: {_screen_names()}",
        ]
    )


def handle_status_command(
    event_data,
    message_text,
    authorized_user_id,
    group_sender,
    private_sender,
    status_builder=build_status_message,
    source_ip="",
    allowed_source_ips=None,
):
    if message_text.strip() != "#status":
        return False
    if allowed_source_ips and source_ip not in allowed_source_ips:
        print(f"Ignored #status from untrusted source {source_ip}")
        return True
    sender_id = int(
        event_data.get("sender", {}).get("user_id")
        or event_data.get("user_id")
        or 0
    )
    if not authorized_user_id or sender_id != int(authorized_user_id):
        print(f"Ignored unauthorized #status from {sender_id}")
        return True
    message = status_builder()
    # Status contains host metadata, so always return it to the configured QQ user
    # instead of trusting a group/user destination supplied by the webhook body.
    private_sender(int(authorized_user_id), message)
    return True
