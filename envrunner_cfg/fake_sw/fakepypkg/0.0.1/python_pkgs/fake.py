
import os

def get_pkg_version():

    return '0.0.1'

def show_env(evar_list=None):

    if not evar_list:
        evar_list = sorted(os.environ.keys())

    print('')
    print('')

    for evar in evar_list:

        if 'PATH' in evar:
            print(':: %s ...' % evar)
            for p in os.getenv(evar).split(os.pathsep):
                print('    %s' % p)
        else:
            print(':: %s = %s' % (evar, os.getenv(evar)))

    print('')
    print('')

