#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Usage: trashy_rm [OPTION].. [FILE]...

Interactive file remover for safe deletion and recycling

Options:
  -f, --force      Ignore nonexistent files and arguments, never prompt
  -r, --recursive  Remove directories and their contents recursively
  -d, --dir        Remove empty directories
  -c, --recycle    Move the files to the trash / recycle bin
      --direct     Standard rm files even if they're in the trash path
  -s, --shred      Shred the files for secure deletion
  -i               Prompt before removal for every file
  -I               Prompt once before removing more than CUTOFF files, or when
                     removing recursively. This is the default mode.
      --interactive[=WHEN] Prompt according to WHEN: never, once (-I), or
                             always (-i). Without WHEN, prompt always.
  -v, --verbose    Explain what is being done
  -h, --help       Display this text and exit
      --version    Output version information and exit
  --               Treats all following arguments as file names
  -                Read file names from stdin

Trashy rm defaults to '--interactive=once' (-I) mode, prompting the user if
more than CUTOFF (defaults to 3) files and directories will be removed. An
attempt is made to provide a useful overview of what files and directories will
be removed before prompting y/n.

Trashy rm also supports different removal modes.
  Recycle mode (-c or --recycle) will move the given files to the best matching
    trash / recycle bin for the device and OS.
  Normal mode will unlink the files via standard rm. If a file resides in the
    configured trash path, the file will instead be moved to the trash.
  Direct mode (--direct) will unlink files via standard rm, ignoring the trash
    path.
  Shred mode (-s, --shred) will use shred / gshred to more securely delete a
    file, bypassing the other removal modes. Shred mode will attempt to
    repeatedly overwrite the file bytes for more secure deletion than rm, which
    leaves the data intact but unlinked. Shred's effectiveness is limited by
    filesystem type (e.g. journaling or Copy On Write) and device behavior; see
    GNU shred's documentation for more information

See man trashy_rm(1) for configuration information
"""

# TODO: Might be useful in a man page / README later
# General purpose file remover wrapping standard rm, mv, and shred commands to
# handle unlinking, recycling, and safe deletion of files and directories. Also
# provides different interactive modes to get a preview of what files will be
# affected.

import configparser
import os
import platform
import sys
from enum import Enum
from subprocess import call

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
    # get version and exit
    version = False
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
    conf = AppConfig()
    for file_name in file_names:
        parser.read(file_name)
    cutoff = parser.getint('prompt', 'cutoff', fallback=None)
    if cutoff is not None:
        conf.cutoff = cutoff
    if parser.has_section('trash_path'):
        conf.trashy_dirs += [os.path.expanduser(os.path.expandvars(path)) for _, path in parser.items('trash_path')]
    return conf


class OptParseError(Exception):
    """Exception indicating an invalid command line argument"""


def parse_opts(opts: List[str]) -> ExecConfig:
    """Parse command line arguments"""
    conf = ExecConfig()
    it = iter(opts)
    while True:
        try:
            opt = next(it)
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
                        raise StopIteration()
                    elif o == '-get-trash':
                        # Stop processing if we see a get-trash flag
                        conf.get_trash = True
                        raise StopIteration()
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


class UnsupportedSystemError(Exception):
    """Exception indicating the system is not supported by trashy rm"""


class LinuxSystemInfo:
    def __int__(self):
        self.uid = os.getuid()
        self.configs = LinuxSystemInfo.get_configs()
        self.user_trash = LinuxSystemInfo.get_user_trash()
        self.shredder = LinuxSystemInfo.get_shredder()

    @classmethod
    def get_user_trash(cls) -> str:
        xdg_data_home = os.path.expanduser(os.path.expandvars(os.getenv('XDG_DATA_HOME', '~/.local/share')))
        user_trash = os.path.join(xdg_data_home, 'Trash')
        return user_trash

    @classmethod
    def get_configs(cls) -> List[str]:
        xdg_config_home = os.path.expanduser(os.path.expandvars(os.getenv('XDG_CONFIG_HOME', '~/.config')))
        user_config = os.path.join(xdg_config_home, 'trashy_rm', 'config')
        return [user_config] if os.path.isfile(user_config) else []

    @classmethod
    def get_shredder(cls) -> str:
        # File shredding
        if call('hash shred 2>/dev/null', shell=True) == 0:
            shredder = 'shred'
        elif call('hash gshred 2>/dev/null', shell=True) == 0:
            shredder = 'gshred'
        else:
            shredder = None
        return shredder

    def get_trash_dir(self, target):
        """Get the best matching trash directory for the target file / dir"""
        raise NotImplementedError()


def get_system_info():
    system_type = platform.system()
    if system_type == 'Linux':
        return LinuxSystemInfo()
    elif system_type == 'Darwin':
        # TODO: get support from someone with an Apple Macintosh
        raise UnsupportedSystemError("Support for Darwin systems not implemented")
    else:
        # TODO: BSD should be usable as well
        raise UnsupportedSystemError("Unsupported system: " + system_type)


def run(sys_info, conf: AppConfig, opts: ExecConfig,
        inp=sys.stdin, out=sys.stdout, err=sys.stderr) -> int:
    """Run trashy rm with the given configurations"""
    if opts.help:
        out.write(__doc__)
        return 0
    else:
        raise NotImplementedError()


def main() -> int:
    """trashy_rm run harness"""
    # TODO: handle and test exceptions
    sys_info = get_system_info()
    opts = parse_opts(sys.argv)
    conf = load_app_config(sys_info.configs)
    return run(sys_info, conf, opts)


if __name__ == '__main__':
    sys.exit(main())
