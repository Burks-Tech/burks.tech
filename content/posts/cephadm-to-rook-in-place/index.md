---
title: "cephadm to Rook, in place"
subtitle: "Seven hosts, 97 TiB and zero data movement."
date: 2026-10-24T09:00:00-05:00
summary: "How we moved a seven-host, 44-OSD production Ceph cluster from cephadm to Rook on Talos Linux one host at a time, without building a second cluster or moving any data."
tags: [ceph, rook, talos, kubernetes]
toc: true
source:
  url: "https://github.com/Burks-Tech/cephadm-to-rook-in-place"
  rev: "v1.0.1"
  title: "cephadm-to-rook-in-place"
  summary: "The full guide, the per-host runbook, all 23 pitfalls, the lessons, and the sanitized manifests and gate scripts. Docs CC BY 4.0, scripts MIT."
stats:
  - { value: "7 / 7", label: "hosts converted" }
  - { value: "44", label: "OSDs adopted" }
  - { value: "97 TiB", label: "stayed on disk" }
  - { value: "0", label: "PGs remapped" }
phases:
  - label: "phase 0 · lab"
    title: "Prove it in a lab"
    detail: "Four VMs rehearsed the whole conversion eight times. Baselines taken, the cluster cleaned up."
    impact: "none"
  - label: "phase 1 · rook beside cephadm"
    title: "Rook arrives, nothing moves"
    detail: "Rook operator in with CSI off, cephadm scheduling frozen, mons renamed to Rook's letters at the same IPs, Rook's identity seeded by hand, a `CephCluster` with no storage nodes, cephadm paused."
    impact: "one mgr module restart"
  - label: "phase 2 · per host"
    title: "One host at a time"
    detail: "Stop the host's cephadm daemons, swap only the boot disk, install Talos, prove a cold boot, add one line to the `CephCluster`. Rook adopts the same OSDs and the same mon."
    impact: "one host degraded per window"
  - label: "phase 3 · services"
    title: "MDS, RGW and SMB"
    detail: "CephFS handed to Rook MDS daemons, S3 rebuilt as a new object store and copied over, SMB replaced by a single Samba pod."
    impact: "6–8 s MDS stall, S3 down for one evening"
  - label: "phase 4 · decommission"
    title: "Last host, then cephadm goes"
    detail: "The host with the awkward services went last. Then the cephadm mgr module was switched off and its state removed: `HEALTH_OK`."
    impact: "none"
---

In October 2026 we moved our production Ceph cluster from cephadm to Rook. We didn't build a second cluster and we didn't copy any data. Seven hosts went from Ubuntu, with Ceph in cephadm-managed containers, to Talos Linux, with Ceph in Rook-managed pods, one host at a time. Every OSD came back under Rook from the same LVM volumes, with the same id and the same key it had before.

Rook doesn't support this, and we found no public report of anyone else completing it. So we wrote all of it down: the guide, the per-host runbook, every pitfall and the scripts that proved nothing moved are in [cephadm-to-rook-in-place](https://github.com/Burks-Tech/cephadm-to-rook-in-place) on GitHub. This post is the short version.

## The cluster

- Seven bare-metal hosts with 44 OSDs across HDD, SATA and SAS SSD, and NVMe. All of them `ceph-volume lvm` OSDs, many with DB volumes on a shared NVMe.
- An erasure-coded 5+2 CephFS data pool on exactly seven hosts, so no spare failure domain. About 243 TiB raw, 97 TiB used.
- Seven mons, two CephFS filesystems, an S3 object store and an SMB service.
- Before: Ceph 20.2.4 Tentacle under cephadm on Ubuntu 24.04. After: the same Ceph, run by Rook v1.21.0 on Talos Linux v1.14.2 and Kubernetes v1.36.

The supported route is a second cluster and a data copy, which needs a second full set of disks. Rebuilding the OSDs host by host is the other common answer, but with EC 5+2 on exactly seven hosts, every rebuilt host would leave the pool a shard short until recovery finished: days, on HDDs. Keeping the data on disk and replacing only the boot disk made each host's window the same exposure as an ordinary reboot.

## What "in place" means

Ceph cares about a handful of identities. Keep all of them, and the only thing that changes is who starts the processes.

| Identity | How we kept it |
|---|---|
| fsid, `mon.` and `client.admin` keys | Rook's identity Secret, created by hand from the live values before any `CephCluster` existed |
| Mon names and addresses | Mons renamed to Rook's letters, `a` to `g`, while still under cephadm, at the same IPs |
| OSD ids, keys and data | Only the boot disk is replaced. Rook's prepare job finds `ceph-volume` LVM OSDs by their `ceph.cluster_fsid` tag and starts the same ids |
| CRUSH host buckets | Kubernetes node name equals the existing CRUSH host name, no topology labels, `osd_crush_update_on_start=false` |
| Pools and rules | No pool CRs at all during the migration |

Get the first row wrong and Rook bootstraps a brand-new cluster next to your old one. Get the CRUSH bucket wrong and the OSDs re-place themselves and the cluster remaps.

## The shape of it

{{< phases >}}

Between phases the cluster is healthy and can sit for days. A mix of cephadm and Rook hosts is a normal, stable state, which is what made it possible to stop, look and decide at every step.

## How we knew nothing moved

"Zero data movement" has a precise meaning here: every placement group keeps the same up and acting set, CRUSH doesn't change, and no pool starts using a new rule. Writes that land while a host is down still have to recover when it comes back, as after any reboot. That took 4 to 10 minutes per window, and it isn't movement.

To prove it, we hashed the cluster's placement before and after every step: the raw, up and acting set of every PG, the CRUSH map, the rules, the pool settings and the OSD tree. Each host's adoption gate compared those hashes with the baseline taken before its window, and they were identical at every gate on all seven hosts. On top of that, every adopted OSD had to match its old key hash, metadata and memory target.

Two habits made the hashes trustworthy. We checked each baseline's own stability first (two baselines taken 15 minutes apart must compare clean), and we chained them, so every window started from the previous window's final state and any drift between windows would have shown. The gate script is in the repository's [examples](https://github.com/Burks-Tech/cephadm-to-rook-in-place/tree/v1.0.1/examples).

## One host window

A typical window took 30 to 45 minutes from stopping cephadm on a host to all of its OSDs up under Rook:

1. Set `noout` and stop the host's cephadm daemons.
2. Swap only the boot disk. The old one went in a bag as the rollback.
3. Install Talos to the new disk, selected by WWN rather than by device letter.
4. Prove a cold boot. The first boot after an install is a kexec and says nothing about the disk's boot path; a real power cycle caught two different "no boot device" problems before Rook was involved.
5. Check the network, including jumbo frames on the routed path.
6. Add one name-only entry to the `CephCluster`'s `storage.nodes`. Rook's prepare job adopts the host's OSDs, and its mon comes back with the same letter and address.
7. Run the hash gate, let the window's writes recover, unset `noout`, soak.

The first host took three and a half hours, and the overrun was all firmware: getting Dell 13th-generation servers to boot Talos from the new disk. The recipe we ended up with is in [the Dell boot notes](https://github.com/Burks-Tech/cephadm-to-rook-in-place/blob/v1.0.1/docs/dell-13g-talos-boot.md).

## What broke

[Every problem is written up](https://github.com/Burks-Tech/cephadm-to-rook-in-place/blob/v1.0.1/docs/pitfalls.md) with its symptom, cause, fix and prevention: 23 of them. The ones worth knowing before you start:

- **Mon renames stalled on join drift.** Our idle lab never showed it; the busy production cluster did, on the first rename. Raise `paxos_max_join_drift` before you begin.
- **ARP flux black-holed routed jumbo traffic.** After the fifth host, Ceph looked perfect, but kernel RBD writes sat stuck for half an hour. The host's onboard 1 Gb port, kept up because the BMC shares it, answered ARP for the Ceph address, so routed traffic arrived through a 1500-byte port and anything larger vanished. A same-VLAN jumbo ping passed. `arp_ignore=1` and `arp_announce=2` fixed it, and the jumbo check moved to the routed path.
- **An MDS `startupProbe` override broke the filesystem handover.** Rook uses a user-supplied `startupProbe` verbatim, so ours, with timings but no handler, produced an invalid Deployment. The one block we hadn't tested in the lab was the one that failed. Cost: an 11-minute hold.
- **Our GitOps controller undid our freeze.** We suspended the writers' Flux Kustomizations, and their parent re-applied them with `suspend: false`. Velero's kopia maintenance turned out to be a writer nobody had listed. Together that cost two hours in the S3 window.
- **We lost the Samba machine SID** when the old SMB service went away, and had to drop Windows ACLs. Capture any identity you might need before the hosts that hold it are gone.

Two services didn't come across at all, by design. Rook can't serve a realm-less RGW zone, so S3 was rebuilt as a new object store and copied over in one evening. Rook has no SMB support, so the share moved to a single Samba pod.

## How we ran it

The technique matters less than the discipline around it. What we'd keep:

- **Hold-first.** Any unexpected result stops the run, the evidence goes to the person who decides, and nothing reverts on its own.
- **Plan the whole runbook, then run each step in one motion.** No fixes improvised mid-step.
- **Declare the expected warnings** and accept nothing else, and write down what may never go on that list.
- **Diff against baselines** with hashes, not eyeballs.
- **One change at a time.** No other Ceph changes, GitOps merges or dependency updates during a window.
- **Separate deciding from doing.** Whoever holds the go/no-go at the irreversible gates shouldn't be the one typing at that moment. It made stopping cheap: holding was the default, not a failure.

The lab taught one more: the harness can cost more than the migration. Six of our eight lab runs failed on tooling and false alarms, never on the migration itself. Short, real checks with a person deciding beat a strict auto-abort harness by a factor of three.

## Afterwards

The morning after the last host and the decommission: `HEALTH_OK`, 44 of 44 OSDs up and in, 1,561 PGs active+clean, and the hosts within two percentage points of each other on utilisation.

Performance came through the migration unchanged: no measurable increase or decrease.

A few cluster-wide items are still open, such as turning Rook's mon health checks, the balancer and the autoscaler back on. The [changelog](https://github.com/Burks-Tech/cephadm-to-rook-in-place/blob/main/CHANGELOG.md) tracks them.

## Should you do this?

If you can afford a second cluster and a data copy, do that: it's the supported path. This one is for people who can't, and who will first check that:

- every OSD is a `ceph-volume lvm` OSD with complete LV tags;
- the new OS can activate the existing LVM volume groups at boot;
- each storage node's Kubernetes name can equal its CRUSH host bucket;
- the mon IP addresses can stay the same throughout;
- `ceph osd ok-to-stop` holds for one host at a time, and they know their failure margin while it's down;
- they'll build a lab that copies their cluster's oddities on purpose.

Read the rollback sections before you start, not after. Every step before the final decommission was reversible host by host, and that is the only reason the risk was acceptable to us.

The [guide](https://github.com/Burks-Tech/cephadm-to-rook-in-place/blob/v1.0.1/docs/guide.md) has Phase 1 in full, the gates and the rollbacks. The [host conversion runbook](https://github.com/Burks-Tech/cephadm-to-rook-in-place/blob/v1.0.1/docs/host-conversion.md) has every step of a window, with measured timings. Links in this post point at the `v1.0.1` release so they stay stable; the repository will keep changing as the remaining steps are done.
