# The owner's Azure test VM: its state around the 1.6.7 and 1.6.8 work (2026-11-05 and 2026-11-06, UTC)

**Class: OWNER AZURE TEST.** Hamza's own VM (Ubuntu 24.04.5 LTS, kernel 7.0.0-1017-azure, 2 vCPU, 3.9 GB of memory,
PostgreSQL 16). The client's VM was not contacted. Records: [`housekeeping/`](housekeeping/) (the final check, its
script and log, and the host records of the two earlier gates in `housekeeping/earlier/`), and the host records of
this delivery's gate ([`container/logs/`](container/logs/)) and of the walkthrough session
([`evidence/owner-azure-test/1.6.8/walkthrough/logs/`](walkthrough/logs/)), each `host_before.txt` and `host_after.txt`.

## What this work used, and what it left

- **Folders.** `q167` (the 1.6.7 work; it also holds the campaign database dump and the stored live pages that the
  later replays read), `q168` (the gate of the second 1.6.8 candidate, `7a96218`) and `q168d` (this delivery's final
  candidate) in the VM user's home. They are kept: 1.9 GiB, 1.2 GiB and 1.6 GiB at 23:31:58Z (`du -sh`); the disk is
  38% used (11 of 29 GB).
- **PostgreSQL.** One role, `walmart_q167`, made by this work. Its databases (`walmart_q167_*`, `walmart_q168_*`,
  `walmart_q168d_*`: 25 databases, 4.4 GiB in all) were dropped from 23:31:51Z to 23:31:58Z, after the evidence taken
  from them had been fetched and checked; none failed to drop. The role is kept, with no database. The script refuses
  to drop a database of that role outside these names, and the VM's other databases (`walmart_collector`,
  `walmart_oxylabs`, `walmart_pubtest`, `walmart_pubtest_oxylabs`, `walmart_pubtest_scrapedo`, `walmart_scrapedo`)
  were not touched: the log lists them before and after.
- **Docker.** Ubuntu's Docker packages were unpacked into this work's folder, not installed. Each session started
  its own daemon (its own socket under `/run`, its own data root, `bridge: none`, no iptables rules), and its last
  step stopped the daemon and removed the data root.
- **Processes.** None of this work's processes is left running: the housekeeping script checked at 23:31:51Z and
  refuses to run otherwise. A waiting shell from the 1.6.7 session (it polled a log of that session) had been left
  behind; it was stopped at 22:22:41Z.
- **2026-11-06.** After the housekeeping, the probe 1.7.2 package built again before publication was run in a new
  folder, `q168e`, in the VM user's home, from 01:02:36Z to 01:05:06Z ([`probe-1.7.2/`](probe-1.7.2/)): no
  database, no Docker, no request. At 01:06:52Z none of its processes was running, the folder held 117 MiB and is
  kept, and the disk was 39% used ([`probe-1.7.2/host_after_run.txt`](probe-1.7.2/host_after_run.txt)).

## The Docker gate's `after` step (exit 1)

The gate's last step compares the host with its state before the gate. It exited 1 at 22:09:13Z because the gate's
four databases (`walmart_q168d_c_*`) were still present: they had been kept on purpose for the checks that followed.
They were dropped with the others (above). The step's output is [`container/logs/after.log`](container/logs/after.log).

## The bridge `docker0`

The 1.6.7 gate's record of the host before it ran (2026-11-05T10:49Z,
[`housekeeping/earlier/host_before_1.6.7_gate.txt`](housekeeping/earlier/host_before_1.6.7_gate.txt)) lists a bridge
`docker0` (state DOWN, address 172.17.0.1/16, and its two systemd device units), left by an earlier Docker test on
this VM; no Docker of the system is installed. It is absent from every later record: after the 1.6.7 gate (17:03Z),
before and after the `7a96218` gate (17:54Z, 18:38Z), before and after this delivery's gate (21:24Z, 22:09Z), before
and after the walkthrough session (22:58Z, 23:14Z), and now (23:31Z). No script of this work names `docker0`, and
what removed it is not established. Nothing on the VM uses it: there is no Docker daemon of the system, and a Docker
daemon creates its default bridge when it starts. It was not recreated. To recreate it by hand, with its address
and the hardware address its IPv6 link-local address was derived from:
`sudo ip link add docker0 type bridge && sudo ip link set docker0 address 2a:5c:eb:ac:19:fb && sudo ip addr add 172.17.0.1/16 dev docker0 && sudo ip link set docker0 up`
(the record keeps only its state, DOWN, which a bridge without ports shows even when it is up).

## The host now, against its state before the 1.6.7 gate

[`housekeeping/host_now.txt`](housekeeping/host_now.txt) (23:31:58Z), made by the same commands as the gates'
records, against the 1.6.7 gate's record of the host before it (10:49Z). The comparison is in
[`housekeeping/housekeeping.log`](housekeeping/housekeeping.log). It differs in three things only:

- the bridge `docker0`: its link, its address and its two systemd device units, present then and absent now (above);
- four databases of this work's role (`walmart_q167_oxylabs`, `walmart_q167_oxylabs_test`, `walmart_q167_scrapedo`,
  `walmart_q167_scrapedo_test`), made by the 1.6.7 work before that record, and dropped now;
- a heading of the record, which now names `q168` beside `q167`: a change of the script, not of the host.

Everything else recorded is the same: the installed packages (670, by the SHA-256 of their list), the firewall rules
(iptables filter and nat, ip6tables, the nft ruleset), the forwarding settings, the AppArmor profiles, no mount naming
Docker, containerd or this work's folders, `/etc/docker`, `/var/lib/docker` and `/var/lib/containerd` absent, the
entries of `/run` (among them `containerd`, `docker` and `docker.sock`, left by the earlier Docker test), `/opt`, no
unit or process naming Docker or containerd, no `docker` group, the VM's other databases and the listening sockets.

## The VM is left running

Deallocating it needs the owner's Azure credentials, which this work does not hold (acceptance rows A73 and B21:
PENDING_OWNER).
