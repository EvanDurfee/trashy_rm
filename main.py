#!/usr/bin/env python
"""tashy_rm, the safe-ish rm wrapper

"""

import sys

## Run harness
def main(argv=None):
    if not argv:
        argv = sys.argv
    sys.argv = None
    if not argv:
        sys.stderr.write('trashy_rm: missing operand\nTry trashy_rm --help for more information.\n')
        return 1

if __name__ == '__main__':
    sys.exit(main())
