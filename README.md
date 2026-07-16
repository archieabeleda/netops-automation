# netops-automation

Network automation for multi-vendor labs and internal networks. Four tools on one inventory and a single Netmiko connection layer: config backup with drift detection, pre and post change validation, STIG-style compliance auditing, and IPAM sync against NetBox.

Live writeup → https://archieabeleda.github.io/netops-automation/

## Why it exists

Four things go wrong on a network when no one is watching. Config drifts off the standard. A change drops an adjacency and nobody notices until traffic does. A device quietly falls out of compliance. The documentation stops matching reality. Each tool here closes one of those gaps, runs unattended, and never trusts me to remember.

## What it does

Config backup and drift detection logs into each device, pulls the running config, strips the volatile lines, and commits it to git. Anything that changed since the last run shows up as a line-level diff with the device named in the commit message.

Pre and post change validation snapshots interface, BGP, and routing state before a change and again after, then compares the two and flags dropped neighbors or interfaces that went down.

STIG-style compliance auditing checks each device against a declarative rule set, forbidden services, missing banners, NTP, SSH version, and reports every violation with the device and the rule it broke.

IPAM sync reads live IP and MAC allocations from device ARP tables and reconciles them into NetBox, so the source of truth matches the network instead of last quarter's guess.

## Read-only until told otherwise

The three tools that only read run freely. The two that can change a device or a record, remediation and NetBox sync, are dry runs by default. They print the exact config block or record they would push and touch nothing until I add an explicit `--apply`. Captured configs go to a separate private repository, because the code is public and the network layout is not.

Worst case on a read is a misread stanza. There is no write path to get wrong unless I open one on purpose.

## How it's built

A src-layout Python package with a Typer CLI, one command group per tool, every device session routed through a single Netmiko context manager. Inventory and rules are declarative YAML, validated on load. Credentials come from the environment, never the repo. SSH sessions can verify host keys against `known_hosts`. Built and validated in an EVE-NG lab, with a setup guide that takes someone from a bare Ubuntu box to a working run.

## Architecture

```
src/netops/
  settings.py          config from environment, credentials never in the repo
  inventory.py         one YAML file, validated on load
  connections.py       single Netmiko context manager used by every tool
  cli.py               Typer entry point, one command group per tool
  backup/              pull config, strip volatile lines, difflib drift, git push
  compliance/          declarative rules, read-only audit, gated remediation
  prepost/             snapshot state, compare before and after
  ipam/                ARP discovery, NetBox sync
```

## Quickstart

```
git clone https://github.com/archieabeleda/netops-automation
cd netops-automation
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env                                       # set credentials
cp inventory/devices.example.yaml inventory/devices.yaml   # list devices

netops backup run --no-push     # safe local run, reads devices, changes nothing
netops compliance audit         # report violations, changes nothing
```

## Commands

```
netops backup run [--push/--no-push]     # capture configs, detect drift
netops backup schedule --at 02:00        # run it daily
netops prepost snapshot pre              # capture state before a change
netops prepost snapshot post             # capture state after
netops prepost compare pre post          # report what broke
netops compliance audit                  # report violations, read-only
netops compliance remediate [--apply]    # dry run, or push the fixes
netops ipam sync [--apply]               # preview, or write to NetBox
```

## Example: drift detection

[![audit output](docs/img/audit.png)](docs/img/audit.png)

## Safety

The tools that change a device or a record are read-only until you opt in. `compliance remediate` and `ipam sync` are dry runs by default and print what they would do. Add `--apply` to act. Run remediation against a lab first, and read the diff before production.

## Setup

Full setup, from enabling SSH on the lab devices to scheduling backups, is in the [writeup](https://archieabeleda.github.io/netops-automation/).

## License

MIT. See [LICENSE](LICENSE).

---

Built by Archie Abeleda · CISSP · CCSP · CCNP Security
[archieabeleda.dev](https://archieabeleda.dev) · [GitHub](https://github.com/archieabeleda) · [LinkedIn](https://linkedin.com/in/ajrabeleda)
