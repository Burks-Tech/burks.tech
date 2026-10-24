---
title: "About"
subtitle: "David Burks, and the lab these notes come from."
summary: "Who writes burks.tech, and the homelab the posts come from."
---

I'm David Burks. I run a homelab that is built and operated like a small production environment, and I write up the projects worth sharing in detail: what was done, how it was checked and what broke along the way.

## The lab {#the-lab}

The storage half is Ceph 20.2, run by Rook on seven Dell PowerEdge R430 and R730xd servers with Talos Linux. It serves two CephFS filesystems, RBD volumes for Kubernetes, an S3 object store and an SMB share, over a 10 and 25 Gb storage network routed through a Cisco Nexus 92160YC-X.

The compute half is a Talos Linux Kubernetes cluster managed with Flux, with Traefik and the Gateway API in front and an external Prometheus and Alertmanager watching it. Since the [migration to Rook](/posts/cephadm-to-rook-in-place/), the storage servers are nodes in that same cluster.

## Elsewhere

Code and the full write-ups live in the [Burks-Tech organisation on GitHub](https://github.com/Burks-Tech).

## This site

Built with [Hugo](https://gohugo.io/) from a [public repository](https://github.com/Burks-Tech/burks.tech) and served by Cloudflare. There are no cookies and no trackers; Cloudflare Web Analytics counts visits without identifying anyone. The type is Newsreader and JetBrains Mono. Writing is licensed CC BY 4.0, code MIT.
