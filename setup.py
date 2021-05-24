# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: Red Hat Inc. 2013-2014
# Author: Lucas Meneghel Rodrigues <lmr@redhat.com>

# pylint: disable=E0611
from setuptools import setup, find_packages

VERSION = open('VERSION', 'r').read().strip()


def pre_post_plugin_type():
    try:
        from avocado.core.plugin_interfaces import JobPreTests as Pre
        return 'avocado.plugins.result_events'
    except ImportError:
        return 'avocado.plugins.job.prepost'


if __name__ == "__main__":
    setup(name='avocado-framework-plugin-vt',
          version=VERSION,
          description='Avocado Plugin for Virtualization Testing',
          author='Avocado Developers',
          author_email='avocado-devel@redhat.com',
          url='http://github.com/avocado-framework/avocado-vt',
          packages=find_packages(exclude=('selftests*',)),
          include_package_data=True,
          entry_points={
              'console_scripts': [
                  'avocado-runner-avocado-vt = avocado_vt.plugins.vt_runner:main',
                  ],
              'avocado.plugins.settings': [
                  'vt-settings = avocado_vt.plugins.vt_settings:VTSettings',
                  ],
              'avocado.plugins.cli': [
                  'vt-list = avocado_vt.plugins.vt_list:VTLister',
                  'vt = avocado_vt.plugins.vt:VTRun',
                  ],
              'avocado.plugins.cli.cmd': [
                  'vt-bootstrap = avocado_vt.plugins.vt_bootstrap:VTBootstrap',
                  'vt-list-guests = avocado_vt.plugins.vt_list_guests:VTListGuests',
                  'vt-list-archs = avocado_vt.plugins.vt_list_archs:VTListArchs',
                  ],
              pre_post_plugin_type(): [
                  'vt-joblock = avocado_vt.plugins.vt_joblock:VTJobLock',
                  ],
              'avocado.plugins.init': [
                  'vt-init = avocado_vt.plugins.vt_init:VtInit',
                  ],
              'avocado.plugins.resolver': [
                  'vt = avocado_vt.plugins.vt_resolver:VTResolver'
                  ],
              'avocado.plugins.discoverer': [
                  'vt = avocado_vt.plugins.vt_resolver:VTDiscoverer'
                  ],
              'avocado.plugins.runnable.runner': [
                  'vt = avocado_vt.plugins.vt_runner:VTRunner',
                  ],
              },
          install_requires=["netifaces", "simplejson", "six", "netaddr",
                            "aexpect", "avocado-framework>=68.0"]
          )
