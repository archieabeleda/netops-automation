# netops-automation

A network automation toolkit for multi-vendor environments. Four operational tools sit on a shared inventory and connection layer:

- **Config backup and drift detection** pulls running configs on a schedule, stores them in git, and flags line-level drift between runs.
- **Pre-change and post-change validation** snapshots interface, BGP, and routing state before a change and re-checks after to catch dropped adjacencies or interfaces that went down.
- **STIG compliance auditing** checks devices against a rule set for forbidden services, missing banners, NTP, SSH version, and can push fixes behind an explicit apply flag.
- **IPAM discovery and source-of-truth sync** maps live IP and MAC allocations from device ARP tables and updates NetBox.

Connections go through Netmiko, so any platform Netmiko supports works with the same code. The shipped examples target Cisco IOS and NX-OS.

## Why this exists

Config state drifts, changes cause silent outages, appliances fall out of compliance, and the source of truth goes stale. Each tool closes one of those gaps and runs unattended.

## Architecture

```
src/netops/
  settings.py          environment-driven config, credentials from env only
  inventory.py         one YAML file, validated on load
  connections.py       single Netmiko context manager used by every tool
  cli.py               Typer entry point, one command group per tool
  backup/
    collector.py       pull running config, strip volatile lines
    differ.py          difflib drift detection
    repo.py            GitPython commit and push
    runner.py          parallel collection, scheduler
  compliance/
    rules.py           declarative rule model
    auditor.py         read-only evaluation
    remediate.py       gated auto-fix, dry run by default
    stig_examples.yaml starter rule set
  prepost/
    prepost.py         snapshot state, compare before and after
  ipam/
    ipam.py            ARP discovery, NetBox sync
```

Credentials never live in the inventory or the repo. They are read from the environment with the `NETOPS_` prefix by `pydantic-settings`. The inventory is a single YAML file validated by pydantic on load.

## Quickstart

```bash
git clone https://github.com/ctrlf4rchie/netops-automation
cd netops-automation
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env                                       # set credentials
cp inventory/devices.example.yaml inventory/devices.yaml   # define devices

netops backup run --no-push     # local run, writes and commits, no push
netops compliance audit         # report violations, changes nothing
pytest -q                       # run the offline unit tests
```

## Commands

```
netops backup run [--push/--no-push]
netops backup schedule --at 02:00
netops prepost snapshot pre
netops prepost snapshot post
netops prepost compare pre post
netops compliance audit --rules src/netops/compliance/stig_examples.yaml
netops compliance remediate            # dry run, prints the config it would push
netops compliance remediate --apply    # pushes fixes and saves config
netops ipam sync                        # preview discovered allocations
netops ipam sync --apply                # write to NetBox
```

## Safety

The tools that change device or record state are read-only until you opt in.

- `compliance remediate` is a dry run by default. It prints the exact config it would send. Add `--apply` to push, at which point it writes the fix and saves the config.
- `ipam sync` previews discovered allocations by default. Add `--apply` to write to NetBox.
- `backup run` writes config files locally and commits them. It only pushes when a remote is set and `--push` is on.

Run remediation against a lab first. Read the diff before you apply anything to production.

## Config backup and drift detection

Configs are stored under `NETOPS_CONFIG_STORE` (default `data/configs`), which is its own git repository with a dedicated remote. That keeps captured configs separate from the toolkit code. Point `NETOPS_GIT_REMOTE` at a private repo. Volatile lines such as timestamps, NVRAM checksums, and clock period are stripped before diffing so a drift report shows real changes only.

## Compliance rules

Rules are declarative and live in YAML. A rule is a regex checked against the running config, a match mode, and the config lines that fix a violation:

```yaml
- id: STIG-TELNET-DISABLED
  title: Telnet must not be an allowed VTY input transport
  severity: high
  match: must_not_contain
  pattern: "transport input telnet"
  platforms: [cisco_ios, cisco_xe, cisco_nxos]
  remediation:
    - line vty 0 15
    - transport input ssh
```

`must_not_contain` flags a violation when the pattern is present. `must_contain` flags one when it is absent. Add rules without touching code.

## Roadmap

- Per-vendor STIG rule packs mapped to DISA benchmark ids
- Slack and email alerting on drift and failed validation
- Per-group credential sets and vault integration
- NetBox interface and MAC modeling for full source-of-truth depth
- pyATS or Genie parsers as an alternative to TextFSM for richer state diffs

## License

MIT
