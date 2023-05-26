# -----------------------------------------------------------------------------
# MIT License
#
# Copyright (c) 2023 pxlc
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------

import os
import platform


OPPOSITE_PATH_SLASH_D = {'\\': '/', '/': '\\'}

def fslash(path):

    return path.replace('\\', '/')


def conform_path_slash(path_str, force_slash=None):

    path_slash = os.sep
    if force_slash:
        if force_slash not in ('\\', '/'):
            raise Exception(
                'Expecting "force_slash" value to either be a back-slash or '
                'a forward slash, instead got "%s"' % force_slash)

        path_slash = force_slash

    return path_str.replace(OPPOSITE_PATH_SLASH_D[path_slash], path_slash)


class InfoObj:
    def __init__(self, d):
        self.__dict__.update(d)


def _get_linux_os_release_obj():

    info_d = {}
    with open('/etc/os-release', 'r') as fp:
        for line in fp:
            line = line.strip().replace('"', '')
            if not line:
                continue
            k, v = line.split('=')
            info_d[k.lower()] = v

    return InfoObj(info_d)


def _build_os_info():

    platform_bits = platform.platform().split('-')
    _os = platform_bits[0].lower()
    _os_info = {'os': _os}

    if _os == 'windows':
        _os_info.update({
            'distro': 'windows%s' % platform_bits[1],
            'version': platform_bits[2],
        })
        if len(platform_bits) > 3:
            _os_info['service_pack'] = platform_bits[3]
    elif _os == 'linux':
        os_release_obj = _get_linux_os_release_obj()
        _os_info.update({
            'distro': os_release_obj.id.lower(),
            'version': os_release_obj.version_id,
        })
    elif _os == 'macos':
        _os_info.update({
            'distro': '%s-%s' % (_os, platform_bits[2]),
            'version': platform_bits[1],
        })
    else:
        raise Exception('"%s" is not a supported operating system.' % _os)

    _os_info.update({
        'specificity_list': [
            '%s/%s/%s' % (
                    _os_info['os'], _os_info['distro'], _os_info['version']),
            '%s/%s' % (_os_info['os'], _os_info['distro']),
            _os_info['os'],
        ]
    })

    return InfoObj(_os_info)


# generate and store OS information
os_info = _build_os_info()


# bootstrap the base env vars
_THIS_DIR = fslash(os.path.dirname(os.path.abspath(__file__)))

ENVR_CFG_ROOT = (
    os.getenv('ENVR_CFG_ROOT')
            if os.getenv('ENVR_CFG_ROOT')
            else '%s/envrunner_cfg' % _THIS_DIR)
ENVR_CFG_SITE_ROOT = (
    os.getenv('ENVR_CFG_SITE_ROOT')
            if os.getenv('ENVR_CFG_SITE_ROOT')
            else '%s/site' % ENVR_CFG_ROOT)
ENVR_CFG_PROJECTS_ROOT = (
    os.getenv('ENVR_CFG_PROJECTS_ROOT')
            if os.getenv('ENVR_CFG_PROJECTS_ROOT')
            else '%s/projects' % ENVR_CFG_ROOT)
ENVR_CFG_SW_ENVS_ROOT = (
    os.getenv('ENVR_CFG_SW_ENVS_ROOT')
            if os.getenv('ENVR_CFG_SW_ENVS_ROOT')
            else '%s/sw_envs' % ENVR_CFG_ROOT)


def reset_bootstrap_env():

    os.environ['ENVR_OS'] = os_info.os
    os.environ['ENVR_OS_DISTRO'] = os_info.distro
    os.environ['ENVR_OS_VER'] = os_info.version

    os.environ['ENVR_CFG_ROOT'] = ENVR_CFG_ROOT
    os.environ['ENVR_CFG_SITE_ROOT'] = ENVR_CFG_SITE_ROOT
    os.environ['ENVR_CFG_PROJECTS_ROOT'] = ENVR_CFG_PROJECTS_ROOT
    os.environ['ENVR_CFG_SW_ENVS_ROOT'] = ENVR_CFG_SW_ENVS_ROOT


reset_bootstrap_env()


