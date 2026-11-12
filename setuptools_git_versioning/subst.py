from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from pprint import pformat

from setuptools_git_versioning.log import DEBUG

ENV_VARS_REGEXP = re.compile(r"\{env:(?P<name>[^:}]+):?(?P<default>[^}]+\}*)?\}", re.IGNORECASE | re.UNICODE)
TIMESTAMP_REGEXP = re.compile(r"\{timestamp:?(?P<fmt>[^:}]+)?\}", re.IGNORECASE | re.UNICODE)

log = logging.getLogger(__name__)


def substitute_env_variables(template: str) -> str:
    log.log(DEBUG, "Substitute environment variables in template %r", template)
    for var, default_value in ENV_VARS_REGEXP.findall(template):
        log.log(DEBUG, "Variable: %r", var)

        default = default_value
        if default_value.upper() == "IGNORE":
            default = ""
        elif not default_value:
            default = "UNKNOWN"
        log.log(DEBUG, "Default: %r", default)

        value = os.environ.get(var, default)
        log.log(DEBUG, "Value: %r", value)

        template, _ = ENV_VARS_REGEXP.subn(value, template, count=1)

    log.log(DEBUG, "Result: %r", template)
    return template


def substitute_timestamp(template: str) -> str:
    log.log(DEBUG, "Substitute timestamps in template %r", template)

    now = datetime.now(tz=timezone.utc).astimezone()
    for fmt in TIMESTAMP_REGEXP.findall(template):
        format_string = fmt or "%s"
        log.log(DEBUG, "Format: %r", format_string)

        # strftime("%s") is platform-specific and fails on Windows
        result = str(int(now.timestamp())) if format_string == "%s" else now.strftime(format_string)
        log.log(DEBUG, "Value: %r", result)

        template, _ = TIMESTAMP_REGEXP.subn(result, template, count=1)

    log.log(DEBUG, "Result: %r", template)
    return template


def resolve_substitutions(template: str, *args, **kwargs) -> str:
    log.log(DEBUG, "Template: %r", template)
    log.log(DEBUG, "Args:%s", pformat(args))

    while True:
        if "{env" in template:
            new_template = substitute_env_variables(template)
            if new_template == template:
                break
            template = new_template
        else:
            break

    if "{timestamp" in template:
        template = substitute_timestamp(template)

    return template.format(*args, **kwargs)
