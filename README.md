# netops-automation

Network automation for multi-vendor labs and internal networks. Four tools on one inventory and connection layer: config backup and drift detection, pre and post change validation, STIG compliance auditing, and IPAM source-of-truth sync.


## What this is

A working toolkit that logs into network devices over SSH and does four jobs. It backs up running configs to git and flags drift, snapshots network state before and after a change to catch dropped adjacencies, audits devices against a rule set and pushes fixes when told to, and syncs live IP and MAC allocations into NetBox. Connections go through Netmiko, so any platform Netmiko supports works with the same code. The examples target Cisco IOS and NX-OS, built and validated in an EVE-NG lab.


## What this isn't

A turnkey product. It is a lab and portfolio project that shows a way to build read-only-first network automation with human gates on anything that changes a device. The tools that write are dry runs by default and act only when you add `--apply`. Point it at production only behind a service account and a change process.


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

```bash
git clone https://github.com/ctrlf4rchie/netops-automation
cd netops-automation
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env                                       # set credentials
cp inventory/devices.example.yaml inventory/devices.yaml   # list devices

netops backup run --no-push     # safe local run, reads devices, changes nothing
netops compliance audit         # report violations, changes nothing
```


## Example: drift detection

![audit output](docs/img/audit.png)



## Safety

The tools that change device or record state are read-only until you opt in. `compliance remediate` and `ipam sync` are dry runs by default and print what they would do. Add `--apply` to act. Run remediation against a lab first and read the diff before production.


## License

MIT. See LICENSE.

---

Built by Archie Abeleda · CISSP · CCSP · CCNP Security · PCNSE
[archieabeleda.dev](https://archieabeleda.dev) · [GitHub](https://github.com/ctrlf4rchie) · [LinkedIn](https://linkedin.com/in/ajrabeleda)
