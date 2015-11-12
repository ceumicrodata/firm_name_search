from . import name_to_taxid
from . import build_index

import sys


def main_and_argv(argv):
    '''
    Determine the function to execute and the parameters.
    '''
    if argv and argv[0] == 'index':
        return build_index.main, argv[1:]
    else:
        return name_to_taxid.main, argv


def main(version='test version'):
    main, argv = main_and_argv(sys.argv[1:])
    sys.exit(main(argv, version))


if __name__ == '__main__':
    main()
