#!/usr/bin/env bash
# The host firewall (ufw): incoming SSH only from the operator's address; everything else incoming refused;
# outgoing allowed (the collector only makes outbound HTTPS calls). The Azure network security group may still
# allow more: restrict its SSH rule to the same address in the portal.
#
#   sudo bash restrict-ssh.sh 203.0.113.7      # enables the rule, with a 10-minute dead-man timer
#   sudo bash restrict-ssh.sh confirm          # from a NEW SSH session: keeps the rule (stops the timer)
#
# Until `confirm`, the timer disables ufw after 10 minutes, so a wrong address cannot lock the operator out.
# To change the address later: `sudo ufw allow from NEW to any port 22 proto tcp` then delete the old rule;
# without SSH, use the Azure portal's Run command or serial console.
set -euo pipefail
[ "$(id -u)" = 0 ] || { echo "run as root (sudo)" >&2; exit 1; }
if [ "${1:-}" = confirm ]; then
  systemctl stop walmart-ufw-deadman.timer
  echo "ufw rule kept; dead-man timer stopped"
  ufw status verbose
  exit 0
fi
addr=${1:?usage: restrict-ssh.sh ADDRESS | confirm}
[[ "$addr" =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}(/[0-9]{1,2})?$ ]] || { echo "an IPv4 address expected" >&2; exit 1; }
systemd-run --quiet --unit=walmart-ufw-deadman --on-active=10min /usr/sbin/ufw disable
ufw default deny incoming
ufw default allow outgoing
ufw allow from "$addr" to any port 22 proto tcp comment 'operator SSH'
ufw --force enable
ufw status verbose
echo "open a NEW SSH session within 10 minutes and run: sudo bash restrict-ssh.sh confirm"
