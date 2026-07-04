"""Command line interface.

    netops backup run [--push/--no-push]
    netops backup schedule --at 02:00
    netops prepost snapshot pre
    netops prepost compare pre post
    netops compliance audit
    netops compliance remediate [--apply]
    netops ipam sync [--apply]
"""

from __future__ import annotations

import typer

from . import backup as backup_mod
from .compliance import auditor as compliance_auditor
from .compliance import remediate as compliance_remediate
from .ipam import ipam as ipam_mod
from .logging_config import configure_logging
from .prepost import prepost as prepost_mod

DEFAULT_RULES = "src/netops/compliance/stig_examples.yaml"

app = typer.Typer(
    help="Network automation: backup, validation, compliance, IPAM sync.",
    no_args_is_help=True,
)

backup_app = typer.Typer(help="Configuration backup and drift detection.", no_args_is_help=True)
prepost_app = typer.Typer(help="Pre-change and post-change validation.", no_args_is_help=True)
compliance_app = typer.Typer(help="Security and compliance auditing.", no_args_is_help=True)
ipam_app = typer.Typer(help="IPAM discovery and source-of-truth sync.", no_args_is_help=True)

app.add_typer(backup_app, name="backup")
app.add_typer(prepost_app, name="prepost")
app.add_typer(compliance_app, name="compliance")
app.add_typer(ipam_app, name="ipam")


@backup_app.command("run")
def backup_run(
    push: bool = typer.Option(True, help="Commit and push changes to the configured remote."),
) -> None:
    configure_logging()
    backup_mod.run_backup(push=push)


@backup_app.command("schedule")
def backup_schedule(
    at: str = typer.Option("02:00", help="Daily run time as HH:MM, 24 hour."),
) -> None:
    configure_logging()
    backup_mod.schedule_backup(at_time=at)


@prepost_app.command("snapshot")
def prepost_snapshot(
    label: str = typer.Argument(..., help="Label for this snapshot, e.g. pre or post."),
) -> None:
    configure_logging()
    prepost_mod.take_snapshot(label=label)


@prepost_app.command("compare")
def prepost_compare(
    before: str = typer.Argument(..., help="Label of the earlier snapshot."),
    after: str = typer.Argument(..., help="Label of the later snapshot."),
) -> None:
    configure_logging()
    prepost_mod.compare_snapshots(before=before, after=after)


@compliance_app.command("audit")
def compliance_audit(
    rules: str = typer.Option(DEFAULT_RULES, help="Path to the rule set."),
) -> None:
    configure_logging()
    compliance_auditor.run_audit(rules_path=rules)


@compliance_app.command("remediate")
def compliance_remediate_cmd(
    rules: str = typer.Option(DEFAULT_RULES, help="Path to the rule set."),
    apply: bool = typer.Option(
        False, "--apply", help="Push fixes. Without this flag the run is a dry run."
    ),
) -> None:
    configure_logging()
    compliance_remediate.run_remediation(rules_path=rules, apply=apply)


@ipam_app.command("sync")
def ipam_sync(
    apply: bool = typer.Option(
        False, "--apply", help="Write to NetBox. Without this flag the run is a preview."
    ),
) -> None:
    configure_logging()
    ipam_mod.sync(apply=apply)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
