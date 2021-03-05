#!/usr/bin/env python
"""tashy_rm, the safe-ish rm wrapper

"""

import sys
from enum import Enum


class InteractiveMode(Enum):
    NEVER = 1
    NORMAL = 2
    ALWAYS = 3


class AppConfig:
    """Defines the configuration of trashy_rm itself"""
    # number of files / dirs to remove before a prompt is given
    prompt_cutoff = 3
    # directories in which to default to trash instead of rm
    trashy_dirs = []


class ExecutionConfig:
    """Defines the configuration for this trashy_rm execution"""
    # Never prompt, ignore non-existent files and arguments
    force = False
    # Prompt mode (never, once / normal, or always
    interactive_mode = InteractiveMode.NORMAL
    # handle empty directories
    handle_dirs = False
    # Recurse though directories
    recursive = False
    # Root preservation (off, /, all) not supported at this time
    # preservation = None
    # Verbosity
    verbose = False
    # Trash / recycle instead of normal rm
    trash = False
    # Shred (overrides recycle)
    shred = False
    # Dry run, do not modify the file system
    dry_run = False

def run(app_config, exec_config):
    """Run trashy rm with the given configurations"""
    return 0

def main(argv=None):
    """trashy_rm run harness"""
    if not argv:
        argv = sys.argv
    sys.argv = None
    if not argv:
        sys.stderr.write('trashy_rm: missing operand\nTry trashy_rm --help for more information.\n')
        return 1


if __name__ == '__main__':
    sys.exit(main())
