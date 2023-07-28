# this will be the utility module for convenience functionality

import os

from .os_util import os_info


def get_sw_install(software_pkg_name):

    env_var = 'ENVR_SW_%s__INSTALL' % software_pkg_name.upper()
    return os.getenv(env_var)


def get_sw_version(software_pkg_name):

    env_var = 'ENVR_SW_%s__VER' % software_pkg_name.upper()
    return os.getenv(env_var)


def print_env(compact=False, exclude_env_keys=None):

    if exclude_env_keys is not None:
        exclude_env_keys = []

    env_keys = [ek for ek in sorted(os.environ.keys())
                                if ek not in exclude_env_keys]
    print('')

    for ek in env_keys:
        if 'PATH' in ek:
            if not compact:
                print('')
            print('%s ...' % ek)
            for p in os.getenv(ek).split(os.pathsep):
                print('    %s' % p)
        else:
            if not compact:
                print('')
            print('%s = %s' % (ek, os.getenv(ek)))

    print('')
    print('')

