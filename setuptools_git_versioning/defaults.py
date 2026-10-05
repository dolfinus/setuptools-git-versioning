from __future__ import annotations

DEFAULT_TEMPLATE = "{tag}"
DEFAULT_DEV_TEMPLATE = "{tag}.post{ccount}+git.{sha}"
DEFAULT_DIRTY_TEMPLATE = "{tag}.post{ccount}+git.{sha}.dirty"
DEFAULT_STARTING_VERSION = "0.0.1"
DEFAULT_SORT_BY = "creatordate"
DEFAULT_CONFIG = {
    "template": DEFAULT_TEMPLATE,
    "dev_template": DEFAULT_DEV_TEMPLATE,
    "dirty_template": DEFAULT_DIRTY_TEMPLATE,
    "starting_version": DEFAULT_STARTING_VERSION,
    "version_callback": None,
    "version_file": None,
    "count_commits_from_version_file": False,
    "prefer_tag": False,
    "tag_formatter": None,
    "branch_formatter": None,
    "tag_filter": None,
    "sort_by": DEFAULT_SORT_BY,
}


def set_default_options(config: dict):
    for key, value in DEFAULT_CONFIG.items():
        config.setdefault(key, value)
    return config
