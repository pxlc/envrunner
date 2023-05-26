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

import sys
import logging


_ENVR_STDOUT_LOGGER = logging.getLogger('env_stdout_logger')
_ENVR_STDERR_LOGGER = logging.getLogger('env_stderr_logger')

_ENVR_STDOUT_HANDLER = logging.StreamHandler(sys.stdout)
_ENVR_STDERR_HANDLER = logging.StreamHandler(sys.stderr)


def _setup_envr_loggers():

    stdout_log_level = logging.INFO

    _ENVR_STDOUT_LOGGER.setLevel(stdout_log_level)
    _ENVR_STDOUT_HANDLER.setLevel(stdout_log_level)
    _ENVR_STDOUT_LOGGER.addHandler(_ENVR_STDOUT_HANDLER)

    stderr_log_level = logging.ERROR
    _ENVR_STDERR_LOGGER.setLevel(stderr_log_level)
    _ENVR_STDERR_HANDLER.setLevel(stderr_log_level)
    _ENVR_STDERR_LOGGER.addHandler(_ENVR_STDERR_HANDLER)


_setup_envr_loggers()


def set_envr_log_level(log_level_str):

    log_level = getattr(logging, log_level_str)
    _ENVR_STDOUT_LOGGER.setLevel(log_level)
    _ENVR_STDOUT_HANDLER.setLevel(log_level)


# ------------------------------------------------------------------------
# Logging levels to STDOUT ... these don't flush stdout automatically;
# use "envr_log_flush()" function to do that where needed.
# ------------------------------------------------------------------------

def envr_debug(msg):

    _ENVR_STDOUT_LOGGER.debug(msg)


def envr_info(msg):

    _ENVR_STDOUT_LOGGER.info(msg)


def envr_warning(msg):

    _ENVR_STDOUT_LOGGER.warning(msg)


def envr_log_flush():

    sys.stdout.flush()


# ------------------------------------------------------------------------
# Logging levels to STDERR ... these DO flush stderr automatically;
# when errors occur we want messages to flush so they show up immediately
# in console output.
# ------------------------------------------------------------------------

def envr_error(msg):

    _ENVR_STDOUT_LOGGER.error(msg)
    sys.stderr.flush()


def envr_critical(msg):

    _ENVR_STDOUT_LOGGER.critical(msg)
    sys.stderr.flush()

