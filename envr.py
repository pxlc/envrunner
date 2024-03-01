# this will be the utility module for convenience functionality

import os
import sys
import math
import time
import shutil
import getpass
import socket
import datetime
import subprocess

from .os_util import os_info, conform_slash


_THIS_DIR = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
_USER = getpass.getuser()
_MACHINE_NAME = socket.gethostname()
if '.' in _MACHINE_NAME:
    _MACHINE_NAME = _MACHINE_NAME.split('.')[0]


def get_env_key(env_descriptor, wrap=False):

    result = 'ENVR_%s' % env_descriptor.replace(' ', '_').upper()
    if wrap:
        result = '${%s}' % result
    return result


def get_env_value(env_descriptor):

    return os.getenv(get_env_key(env_descriptor))


def get_sw_env_key(sw_name, info_item, wrap=False):

    # info_item is one of: "ver", "install", "vmajor", "vminor"

    result = 'ENVR_SW_%s__%s' % (sw_name.replace(' ', '_').upper(),
                                 info_item.upper())
    if wrap:
        result = '${%s}' % result
    return result


def get_sw_env_value(sw_name, info_item):

    return os.getenv(get_sw_env_key(sw_name, info_item))


def get_envrunner_root():

    return _THIS_DIR


def get_envrunner_bin(bin_subpath=None, force_slash=None):

    if bin_subpath:
        return conform_slash('%s/%s/%s' % (_THIS_DIR, "bin", bin_subpath),
                             force_slash=force_slash)

    return conform_slash('%s/%s' % (_THIS_DIR, "bin"), force_slash=force_slash)


def get_envrunner_cfg_root(force_slash=None):

    return conform_slash(os.getenv('ENVR_CFG_ROOT'), force_slash=force_slash)


def get_session_spec_file():

    return os.getenv('ENVR_SESSION_SPEC_FILE')


def get_user_session_root():

    return os.getenv('ENVR_USER_CURRENT_SESSION_ROOT')


def get_active_sw_list():

    active_sw_str = os.getenv('ENVR_ACTIVE_SW_LIST')
    return active_sw_str.split(';')


def get_all_users_data_root():

    return os.getenv('ENVR_ALL_USERS_DATA_ROOT')


def get_user_data_path(subpath):

    return conform_slash(os.path.join(os.getenv('ENVR_ALL_USERS_DATA_ROOT'),
                                      subpath, get_user()))


def get_os():

    return os_info.os


def get_os_distro():

    return os_info.distro


def get_os_version():

    return os_info.version


def get_user():

    return _USER


def get_machine_name():

    return _MACHINE_NAME


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


def escape_str_for_html(input_str):

    if sys.version_info.major < 3:
        import cgi
        return cgi.escape(input_str).encode('ascii', 'xmlcharrefreplace')

    import html
    return html.escape(input_str)


def get_now_timestamp(display_nice=False):

    dt = datetime.datetime.now()
    dt_str = (dt.strftime('%Y-%m-%d %H:%M:%S')
                    if display_nice else dt.strftime('%Y-%m-%d_%H%M%S'))

    t = time.time()  # time in milliseconds
    millisecs_str = str(int((t - float(math.floor(t))) * 1000.0 + 0.5)).zfill(3)

    return str('%s.%s' % (dt_str, millisecs_str))


def open_html_capture_of_env():

    user_current_session_root = os.getenv('ENVR_USER_CURRENT_SESSION_ROOT')
    active_sw_list = os.getenv('ENVR_ACTIVE_SW_LIST').split(';')

    active_sw_html_arr = []
    for active_sw in active_sw_list:
        entry_str = ''
        if '@' in active_sw:
            bits = active_sw.split('@')
            extra_bits = bits[1].split('|')
            # continue here
            if extra_bits[0] == 'v':  # version override
                entry_str = '%s (@ version %s)' % (bits[0], extra_bits[1])
            elif extra_bits[0] == 'dev':  # dev release
                entry_str = '%s (@ DEV "%s" at %s)' % (
                                    bits[0], extra_bits[1], extra_bits[2])
            else:
                entry_str = '%s (@ ???)' % bits[0]
        else:
            entry_str = active_sw

        active_sw_html_arr.append('<li><code>%s</code></li>' % entry_str)

    env_vars_html_arr = []
    for env_key in sorted(os.environ.keys()):
        if 'PATH' in env_key:
            path_items = os.getenv(env_key).split(os.pathsep)
            evar_html = '''
<div>
<code>%s ...</code><br/>
{PATH_ENTRIES_HTML}
</div>
''' % env_key
            path_html_arr = [('<code>&nbsp;&nbsp;&nbsp;%s</code><br/>' % p)
                                    for p in path_items]
            evar_html = evar_html.format(
                                PATH_ENTRIES_HTML='\n'.join(path_html_arr))
        else:
            evar_html = '''
<div><code>%s = %s</code></div>
''' % (env_key, os.getenv(env_key))

        env_vars_html_arr.append(evar_html)

    template_filepath = os.path.join(_THIS_DIR, 'templates',
                                     'env_capture_TEMPLATE.html')

    with open(template_filepath, 'r') as in_fp:
        template_str = in_fp.read()

    final_html_str = template_str.format(
                TEMPLATES_ROOT='%s/templates' % _THIS_DIR,
                TITLE='ENVRUNNER SESSION INSPECT',
                SESSION_REPORT_TIMESTAMP=get_now_timestamp(display_nice=True),
                USER_CURRENT_SESSION_ROOT=user_current_session_root,
                ACTIVE_SOFTWARE_LIST_ITEMS='\n'.join(active_sw_html_arr),
                ENV_ENTRIES='\n'.join(env_vars_html_arr))

    output_html_filepath = os.path.join(user_current_session_root,
                                        '%s_session_inspect_%s.html' % (
                                                getpass.getuser(),
                                                get_now_timestamp()))

    with open(output_html_filepath, 'w') as out_fp:
        out_fp.write('%s\n' % final_html_str)

    css_output_filepath = ('%s/bootstrap.min.css' %
                                os.path.dirname(output_html_filepath))
    shutil.copy2('%s/templates/bootstrap.min.css' % _THIS_DIR,
                 css_output_filepath)

    if os_info.os == 'windows':
        os.system('START "ENVR SESSION" "%s"' % output_html_filepath)
    elif os_info.os == 'macos':
        os.system('open --new "%s"' % output_html_filepath)
    elif os_info.os == 'linux':
        subprocess.Popen(['firefox', '-new-window', output_html_filepath])

