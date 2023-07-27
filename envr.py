# this will be the utility module for convenience functionality

import os


def get_sw_install(software_pkg_name):

    env_var = 'ENVR_SW_%s__INSTALl' % software_pkg_name.upper()
    return os.getenv(env_var)


def get_sw_version(software_pkg_name):

    env_var = 'ENVR_SW_%s__VER' % software_pkg_name.upper()
    return os.getenv(env_var)

