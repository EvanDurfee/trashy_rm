#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""tashy_rm, the safe-ish rm wrapper

"""

import configparser
import io
import itertools
import os
import sys
from enum import Enum

from typing import List

DEFAULT_CUTOFF = 3


class InteractiveMode(Enum):
    NEVER = 1
    NORMAL = 2
    ALWAYS = 3


class TrashMode(Enum):
    """Mode for trashing / recycling files
    NORMAL will move items to trash if they are in a trash dir specified in the
    config, otherwise normal rm will be used
    """
    NEVER = 1
    NORMAL = 2
    ALWAYS = 3


class AppConfig:
    """Defines the configuration of trashy_rm itself"""
    def __init__(self, cutoff=DEFAULT_CUTOFF, trashy_dirs=None):
        # number of files / dirs to remove before a prompt is given
        if trashy_dirs is None:
            trashy_dirs = list()
        self.cutoff = cutoff
        # directories in which to default to trash instead of rm
        self.trashy_dirs = trashy_dirs


class ExecConfig:
    """Defines the configuration for this trashy_rm execution"""
    # Show help prompt and exit
    help = False
    # Return the current trash dir and exit
    get_trash = False
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
    # Enable trash / recycle mode (default is to recycle items in the configured dirs, rm elsewhere)
    trash_mode = TrashMode.NORMAL
    # Shred (overrides recycle)
    shred = False
    # Dry run, do not modify the file system
    dry_run = False
    # Read targets from the input stream
    read_targets = False
    # target files / dirs
    targets = []


def load_app_config(file_names: List[str]) -> AppConfig:
    parser = configparser.ConfigParser()
    for file_name in file_names:
        parser.read(file_name)
    cutoff = parser.getint('prompt', 'cutoff', fallback=DEFAULT_CUTOFF)
    if parser.has_section('trash_path'):
        trashy_dirs = [os.path.expanduser(os.path.expandvars(path)) for _, path in parser.items('trash_path')]
    else:
        trashy_dirs = []
    return AppConfig(cutoff, trashy_dirs)


class OptParseError(Exception):
    """Exception indicating an invalid command line argument"""


def parse_opts(opts: List[str]) -> ExecConfig:
    """Parse command line arguments"""
    conf = ExecConfig()
    it = iter(opts)
    while True:
        try:
            opt = next(it)
            print('Begin: ' + opt)
            if opt == '--':
                # Everything after this is a file
                conf.targets += it
            elif opt == '-':
                # We should read targets from the input stream as well
                conf.read_targets = True
            elif not opt.startswith('-'):
                conf.targets.append(opt)
            else:
                # Start by removing the leading '-' and splitting short opts into a list of characters
                for o in [opt[1:]] if opt.startswith('--') else list(opt[1:]):
                    # Handle the standard rm args first
                    if o == 'f' or o == '-force':
                        conf.force = True
                    elif o == 'd' or o == '-dir':
                        conf.handle_dirs = True
                    elif o == 'r' or o == '-recursive':
                        conf.recursive = True
                    elif o == 'v' or o == '-verbose':
                        conf.verbose = True
                    elif o == 'i' or o == '-interactive' or o == '-interactive=always' or o == '-interactive=yes':
                        conf.interactive_mode = InteractiveMode.ALWAYS
                    elif o == 'I' or o == '-interactive=once':
                        conf.interactive_mode = InteractiveMode.NORMAL
                    elif o == '-interactive=never' or o == '-interactive=no' or o == '-interactive=none':
                        conf.interactive_mode = InteractiveMode.NEVER
                    # TODO: preserve-root flags?
                    # Handle trashy_rm args
                    elif o == 'h' or o == '-help':
                        # Stop processing if we see a help flag
                        conf.help = True
                        raise StopIteration
                    elif o == '-get-trash':
                        # Stop processing if we see a get-trash flag
                        conf.get_trash = True
                        raise StopIteration
                    elif o == 'c' or o == '-recycle':
                        conf.trash_mode = TrashMode.ALWAYS
                    elif o == '-direct':
                        conf.trash_mode = TrashMode.NEVER
                    elif o == 's' or o == '-shred':
                        conf.shred = True
                    elif o == '-dryrun':
                        conf.dry_run = True
                        # sys.stderr.write('Dry Run. Not actually removing files.\n\n')
                    else:
                        raise OptParseError('careful_rm: invalid option -- \'' + o + '\'')
        except StopIteration:
            break
    return conf


def run(app_config: AppConfig, exec_config: ExecConfig) -> int:
    """Run trashy rm with the given configurations"""
    return 0


def main() -> int:
    """trashy_rm run harness"""
    # TODO: pass IO and config
    return run(None, None)


if __name__ == '__main__':
    sys.exit(main())
