#!/usr/bin/env python3.8

"""
Author -    Liew Cher Don
Contact -   c.liew@salesforce.com (deprecated)
            cherdon.liew@salesforce.com
            liewcherdon@gmail.com
"""

import unittest
import os
import sys

try:
    import mock
except ImportError:
    from unittest import mock

curr_path = os.path.abspath(os.path.dirname(__file__))
rma_path = '{}/../guspy/'.format(curr_path)
if rma_path not in sys.path:
    sys.path.append(rma_path)
    sys.path.append(curr_path)


from guspy import *

from deploy_host import HostDeployer, Main, get_command_line
from rest_client import RestClient
from constants import SkipHost, SFDC_SUFFIX, SFDC_FFX_SUFFIX, \
    RR_DEPLOY_CMD_SUCCESS_STR, IDB_UPD_SUCCESS_STR
import katzmeow

from test_constants import mock_hammer_get, mock_gre_roles_get, mock_active_host_get, mock_get, \
    mock_get_versions, mock_get_user_details, mock_ffx_get, MockSpawn, mock_km


class DeployHost(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        self.host_deployer = HostDeployer('abc-app1-1-dc', 'user', 'pswd', False, False, False, None)
        self.host_deployer.pod['super_pod'] = 'sp-1'
        self.host_deployer.pod['name'] = 'abc'
        self.host_deployer.pod['op_status'] = 'Active'
        self.host_deployer.host_status = 'Active'
        self.host_deployer.versions = {'sfdc-base': '226.1.2'}
        self.host_deployer.role = 'app'
        self.host_deployer.managed_type = True
        self.host_deployer.pod['dr'] = False
        self.host_deployer.services = ['sfdc-base', 'caas']

    def assertDictEqual(self, dict1, dict2, msg='Dicts are not equal'):
        self.assertEqual(len(dict1), len(dict2), msg)
        for k, v in dict1.items():
            self.assertEqual(v, dict2[k], msg)

    @mock.patch('os.uname')
    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    def test_validate_hosts(self, mock_uname):
        mock_uname.return_value = ('', 'd')
        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'a-b-c-d,c-d-e,b-c-d-d,c-d-f-e']
        main = Main()
        main.parse_args()
        main.parse_hosts()
        invalid_hosts, other_dc_hosts = main.validate_hosts()
        sys.argv = cur_sys_argv
        self.assertEqual(invalid_hosts, ['c-d-e'])
        self.assertEqual(other_dc_hosts, ['c-d-f-e'])

    @mock.patch('os.uname')
    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    def test_active_host_as_input(self, mock_uname):
        mock_uname.return_value = ('', 'ltm')
        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'a-b-c-d', '-ah', 'a-b-c-ltm']
        main = Main()
        main.parse_args()
        main.parse_hosts()
        invalid_hosts, other_dc_hosts = main.validate_hosts()
        sys.argv = cur_sys_argv
        self.assertEqual(other_dc_hosts, ['a-b-c-d'])

    @mock.patch('os.uname')
    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(katzmeow, 'get_password_from_km_pipe', mock_km)
    def test_get_user_details(self, mock_uname):
        mock_uname.return_value = ('', 'ltm')
        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'a-b-c-ltm', '-e', 'na', '-d', 'na', '-u', 'user']
        main = Main()
        main.parse_args()
        main.get_user_details()
        sys.argv = cur_sys_argv
        self.assertEqual(main.pswd, 'dummy')

    @mock.patch.object(RestClient, 'get', mock_hammer_get)
    def test_hammer_host(self):
        try:
            self.host_deployer.get_host_details()
        except SkipHost as e:
            self.assertTrue('Its a Hammer Host. Cannot deploy.' == str(e))
            return

        self.assertTrue(False, 'Failed to reject Hammer host')

    @mock.patch.object(RestClient, 'get', mock_gre_roles_get)
    def test_invalid_gre_role(self):
        try:
            self.host_deployer.get_host_details()
        except SkipHost as e:
            self.assertTrue('deviceRole "dummy" is not supported by GRE' == str(e))
            return

        self.assertTrue(False, 'Failed to reject host of role not supported by GRE')

    def test_rr_cmds(self):
        base_cmd = 'release_runner.pl -versions sfdc-base@226.1.2 -c deploy -invdb_mode -superpod sp-1 -cluster abc ' \
                   '-cluster_status Active -auto2  -host_status Active -no_lb -host abc-app1-1-dc'

        sfdc_cmd = base_cmd + SFDC_SUFFIX
        self.host_deployer.gen_rr_commands()
        self.assertEqual(self.host_deployer.rr_cmds[0], sfdc_cmd, 'Failed to generate RR command')

        self.host_deployer.pod['dr'] = True
        self.host_deployer.rr_cmds = []
        exp_dr_cmd = sfdc_cmd + ' -drnostart'
        self.host_deployer.gen_rr_commands()
        self.assertEqual(self.host_deployer.rr_cmds[0], exp_dr_cmd + ' -core_dr_start -stopall',
                         'Failed to generate RR command for DR Host')

        self.host_deployer.role = 'ffx'
        self.host_deployer.rr_cmds = []
        exp_ffx_cmd = base_cmd + SFDC_FFX_SUFFIX + ' -drnostart'
        self.host_deployer.gen_rr_commands()
        self.assertEqual(self.host_deployer.rr_cmds[0], exp_ffx_cmd,
                         'Failed to generate RR command for DR Host')

    @mock.patch.object(RestClient, 'get', mock_active_host_get)
    def test_active_host_details(self):
        try:
            self.host_deployer.get_active_host_details()
        except SkipHost as e:
            self.assertTrue('Could not find ACTIVE host' == str(e))
            return

        self.assertTrue(False, 'Active host should not be available')

    @mock.patch('pexpect.spawn')
    def test_get_versions_negative(self, mock_spawn):
        mock_spawn.return_value = MockSpawn(['dummy', 'dummy'])
        self.host_deployer.active_host = 'active-host-1-dc'
        try:
            self.host_deployer.get_versions()
        except SkipHost as e:
            version_failed_cmd = 'Failed to get version with cmd - release_runner.pl -c versioncheck -invdb_mode ' \
                                 '-superpod sp-1 -cluster abc -cluster_status Active -auto2 -threads -host_status ' \
                                 'ACTIVE -product sfdc-base -host active-host-1-dc'
            self.assertTrue(version_failed_cmd in str(e), 'Version command on active host should fail')
            return
        self.assertFalse(True, 'SkipHost exception is expected for active host version check')

    @mock.patch('pexpect.spawn')
    def test_get_versions(self, mock_spawn):
        self.host_deployer.active_host = 'active-host-1-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = ['dummy', data.format(self.host_deployer.active_host, '126.1.2'),
                       data.format(self.host_deployer.host, '4.5'),
                       data.format(self.host_deployer.active_host, '5.2')]
        mock_spawn.return_value = MockSpawn(return_data)

        self.host_deployer.get_versions()
        exp_versions = {'caas': '5.2',
                        'sfdc-base': '126.1.2'}
        self.assertDictEqual(exp_versions, self.host_deployer.versions, 'Failed to get the versions')

    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(Main, 'get_user_details', mock_get_user_details)
    @mock.patch('deploy_host.Main.validate_hosts')
    @mock.patch.object(RestClient, 'get', mock_get)
    @mock.patch('pexpect.spawn')
    def test_deploy(self, mock_spawn, mock_validate_hosts):
        self.host_deployer.active_host = 'active-host-1-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = [data.format(self.host_deployer.host, '4.5'),
                       data.format(self.host_deployer.active_host, '5.2'),
                       'dummy', data.format(self.host_deployer.active_host, '236.1.2'),
                       RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       RR_DEPLOY_CMD_SUCCESS_STR, IDB_UPD_SUCCESS_STR]
        mock_spawn.return_value = MockSpawn(return_data)
        mock_validate_hosts.return_value = ([], [])

        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'abc-app1-1-dc']
        host_deployer = Main().main()
        sys.argv = cur_sys_argv

        exp_services = ['caas', 'sfdc-base']
        exp_versions = {'sfdc-base': '236.1.2',
                        'caas': '5.2'}
        exp_cmds = ['release_runner.pl -versions sfdc-base@236.1.2 -c deploy -invdb_mode -superpod sp-1 -cluster abc '
                    '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-app1-1-dc -softly '
                    '-no_db_data_init -property "pingcheck_max_tries=800" -property "override_newcfg_file=1" -drnostart -core_dr_start -stopall',
                    'release_runner.pl -versions caas@5.2 -c deploy -invdb_mode -superpod sp-1 -cluster abc '
                    '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-app1-1-dc'
                    ' -drnostart']

        host_deployer.services.sort()
        self.assertListEqual(host_deployer.services, exp_services)
        self.assertDictEqual(host_deployer.versions, exp_versions)
        host_deployer.rr_cmds.sort()
        exp_cmds.sort()
        self.assertListEqual(host_deployer.rr_cmds, exp_cmds)

    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(Main, 'get_user_details', mock_get_user_details)
    @mock.patch('deploy_host.Main.validate_hosts')
    @mock.patch.object(RestClient, 'get', mock_get)
    @mock.patch('pexpect.spawn')
    def test_force_deploy(self, mock_spawn, mock_validate_hosts):
        self.host_deployer.active_host = 'active-host-1-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = [data.format(self.host_deployer.host, '5.2'),
                       data.format(self.host_deployer.active_host, '5.2'),
                       'dummy', data.format(self.host_deployer.active_host, '238'),
                       RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       RR_DEPLOY_CMD_SUCCESS_STR, IDB_UPD_SUCCESS_STR]
        mock_spawn.return_value = MockSpawn(return_data)
        mock_validate_hosts.return_value = ([], [])

        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'abc-app1-1-dc', '--force_deploy']
        host_deployer = Main().main()
        sys.argv = cur_sys_argv
        exp_services = ['caas', 'sfdc-base']
        exp_versions = {'sfdc-base': '238',
                        'caas': '5.2'}
        exp_cmds = ['release_runner.pl -versions sfdc-base@238 -c deploy -invdb_mode -superpod sp-1 -cluster abc '
                    '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-app1-1-dc -softly '
                    '-no_db_data_init -property "pingcheck_max_tries=800" -property "override_newcfg_file=1" -drnostart -core_dr_start -stopall',
                    'release_runner.pl -versions caas@5.2 -c deploy -invdb_mode -superpod sp-1 -cluster abc '
                    '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-app1-1-dc'
                    ' -drnostart']

        host_deployer.services.sort()
        self.assertListEqual(host_deployer.services, exp_services)
        self.assertDictEqual(host_deployer.force_deploy_versions, exp_versions)
        host_deployer.rr_cmds.sort()
        exp_cmds.sort()
        self.assertListEqual(host_deployer.rr_cmds, exp_cmds)

    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(Main, 'get_user_details', mock_get_user_details)
    @mock.patch('deploy_host.Main.validate_hosts')
    @mock.patch.object(RestClient, 'get', mock_ffx_get)
    @mock.patch('pexpect.spawn')
    def test_ffx_host_deploy(self, mock_spawn, mock_validate_hosts):
        self.host_deployer.host = 'abc-ffx1-1-dc'
        self.host_deployer.active_host = 'active-ffx1-2-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = ['dummy', data.format(self.host_deployer.active_host, '236.1.2'),
                       RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR]
        mock_spawn.return_value = MockSpawn(return_data)
        mock_validate_hosts.return_value = ([], [])

        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'abc-ffx1-1-dc', '--skip_ffx_buddy']

        host_deployer = Main().main()
        sys.argv = cur_sys_argv
        exp_services = ['sfdc-base']
        exp_versions = {'sfdc-base': '236.1.2'}

        exp_cmds = ['release_runner.pl -versions sfdc-base@236.1.2 -c deploy -invdb_mode -superpod sp-2 -cluster abc '
                    '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-ffx1-1-dc '
                    '-softly -no_db_data_init']

        host_deployer.services.sort()
        self.assertListEqual(host_deployer.services, exp_services)
        self.assertDictEqual(host_deployer.versions, exp_versions)
        host_deployer.rr_cmds.sort()
        exp_cmds.sort()
        self.assertListEqual(host_deployer.rr_cmds, exp_cmds)

    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(Main, 'get_user_details', mock_get_user_details)
    @mock.patch('deploy_host.Main.validate_hosts')
    @mock.patch.object(RestClient, 'get', mock_ffx_get)
    @mock.patch('pexpect.spawn')
    def test_force_deploy_ffx_host_with_buddy_deploy(self, mock_spawn, mock_validate_hosts):
        self.host_deployer.host = 'abc-ffx1-1-dc'
        self.host_deployer.active_host = 'active-ffx1-2-dc'
        self.host_deployer.buddy_host = 'abc-ffx2-1-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = ['dummy', data.format(self.host_deployer.active_host, '126.1.2'), 'dummy',
                       RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR]
        mock_spawn.return_value = MockSpawn(return_data)
        mock_validate_hosts.return_value = ([], [])

        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'abc-ffx1-1-dc', '--force_deploy']

        host_deployer = Main().main()
        sys.argv = cur_sys_argv

        exp_services = ['sfdc-base']
        exp_versions = {'sfdc-base': '126.1.2'}
        exp_buddy_versions = {'sfdc-base': '126.1.2'}

        exp_cmds = [
            'release_runner.pl -versions sfdc-base@126.1.2 -c deploy -invdb_mode -superpod sp-2 -cluster abc '
            '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-ffx1-1-dc '
            '-softly -no_db_data_init']

        exp_buddy_cmds = ['release_runner.pl -versions sfdc-base@126.1.2 -c deploy -invdb_mode -superpod sp-2 '
                          '-cluster abc -cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host '
                          'abc-ffx2-1-dc -softly -no_db_data_init']

        host_deployer.services.sort()
        self.assertListEqual(host_deployer.services, exp_services)
        self.assertDictEqual(host_deployer.force_deploy_versions, exp_versions)
        host_deployer.rr_cmds.sort()
        exp_cmds.sort()
        self.assertListEqual(host_deployer.rr_cmds, exp_cmds)

        self.assertDictEqual(host_deployer.buddy_versions, exp_buddy_versions)
        host_deployer.buddy_rr_cmds.sort()
        exp_buddy_cmds.sort()
        self.assertListEqual(host_deployer.buddy_rr_cmds, exp_buddy_cmds)

    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(Main, 'get_user_details', mock_get_user_details)
    @mock.patch('deploy_host.Main.validate_hosts')
    @mock.patch.object(RestClient, 'get', mock_ffx_get)
    @mock.patch('pexpect.spawn')
    def test_force_update_bootstrap_ffx(self, mock_spawn, mock_validate_hosts):
        self.host_deployer.host = 'abc-ffx1-1-dc'
        self.host_deployer.active_host = 'active-ffx1-2-dc'
        self.host_deployer.buddy_host = 'abc-ffx2-1-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = ['dummy', data.format(self.host_deployer.active_host, '126.1.3'), 'dummy',
                       RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR]
        mock_spawn.return_value = MockSpawn(return_data)
        mock_validate_hosts.return_value = ([], [])

        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'abc-ffx1-1-dc', '--force_deploy', "--force_update_bootstrap"]

        host_deployer = Main().main()
        sys.argv = cur_sys_argv

        exp_services = ['sfdc-base']
        exp_versions = {'sfdc-base': '126.1.3'}
        exp_buddy_versions = {'sfdc-base': '126.1.3'}

        exp_cmds = [
            'release_runner.pl -versions sfdc-base@126.1.3 -c deploy -invdb_mode -superpod sp-2 -cluster abc '
            '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-ffx1-1-dc '
            '-softly -no_db_data_init -force_update_bootstrap']

        exp_buddy_cmds = ['release_runner.pl -versions sfdc-base@126.1.3 -c deploy -invdb_mode -superpod sp-2 '
                          '-cluster abc -cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host '
                          'abc-ffx2-1-dc -softly -no_db_data_init -force_update_bootstrap']

        host_deployer.services.sort()
        self.assertListEqual(host_deployer.services, exp_services)
        self.assertDictEqual(host_deployer.force_deploy_versions, exp_versions)
        host_deployer.rr_cmds.sort()
        exp_cmds.sort()
        self.assertListEqual(host_deployer.rr_cmds, exp_cmds)

        self.assertDictEqual(host_deployer.buddy_versions, exp_buddy_versions)
        host_deployer.buddy_rr_cmds.sort()
        exp_buddy_cmds.sort()
        self.assertListEqual(host_deployer.buddy_rr_cmds, exp_buddy_cmds)

    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(Main, 'get_user_details', mock_get_user_details)
    @mock.patch('deploy_host.Main.validate_hosts')
    @mock.patch.object(RestClient, 'get', mock_ffx_get)
    @mock.patch('pexpect.spawn')
    def test_ffx_host_with_apprise_flag(self, mock_spawn, mock_validate_hosts):
        self.host_deployer.host = 'abc-ffx1-1-dc'
        self.host_deployer.active_host = 'active-ffx1-2-dc'
        self.host_deployer.buddy_host = 'abc-ffx2-1-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = ['dummy', data.format(self.host_deployer.active_host, '126.1.2'), 'dummy',
                       RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR]
        mock_spawn.return_value = MockSpawn(return_data)
        mock_validate_hosts.return_value = ([], [])

        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'abc-ffx1-1-dc', '--apprise_case=0123456']

        host_deployer = Main().main()
        sys.argv = cur_sys_argv

        exp_services = ['sfdc-base']
        exp_versions = {'sfdc-base': '126.1.2'}
        exp_buddy_versions = {'sfdc-base': '126.1.2'}

        exp_cmds = ['release_runner.pl -versions sfdc-base@126.1.2 -c deploy -invdb_mode -superpod sp-2 -cluster abc '
                    '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-ffx1-1-dc '
                    '-softly -no_db_data_init -apprise -case_number 0123456']

        exp_buddy_cmds = ['release_runner.pl -versions sfdc-base@126.1.2 -c deploy -invdb_mode -superpod sp-2 '
                          '-cluster abc -cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host '
                          'abc-ffx2-1-dc -softly -no_db_data_init -apprise -case_number 0123456']

        host_deployer.services.sort()
        self.assertListEqual(host_deployer.services, exp_services)
        self.assertDictEqual(host_deployer.versions, exp_versions)
        host_deployer.rr_cmds.sort()
        exp_cmds.sort()
        self.assertListEqual(host_deployer.rr_cmds, exp_cmds)

        self.assertDictEqual(host_deployer.buddy_versions, exp_buddy_versions)
        host_deployer.buddy_rr_cmds.sort()
        exp_buddy_cmds.sort()
        self.assertListEqual(host_deployer.buddy_rr_cmds, exp_buddy_cmds)

    @mock.patch.object(os, 'getlogin', lambda: 'dummy')
    @mock.patch.object(Main, 'get_user_details', mock_get_user_details)
    @mock.patch('deploy_host.Main.validate_hosts')
    @mock.patch.object(RestClient, 'get', mock_ffx_get)
    @mock.patch('pexpect.spawn')
    def test_ffx_host_with_buddy_deploy(self, mock_spawn, mock_validate_hosts):
        self.host_deployer.host = 'abc-ffx1-1-dc'
        self.host_deployer.active_host = 'active-ffx1-2-dc'
        self.host_deployer.buddy_host = 'abc-ffx2-1-dc'
        data = 'Current version on {} ({}): manifest'
        return_data = ['dummy', data.format(self.host_deployer.active_host, '126.1.2'), 'dummy',
                       RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR, RR_DEPLOY_CMD_SUCCESS_STR,
                       IDB_UPD_SUCCESS_STR]
        mock_spawn.return_value = MockSpawn(return_data)
        mock_validate_hosts.return_value = ([], [])

        cur_sys_argv = sys.argv
        sys.argv = ['deploy_host.py', '--hosts', 'abc-ffx1-1-dc']

        host_deployer = Main().main()
        sys.argv = cur_sys_argv

        exp_services = ['sfdc-base']
        exp_versions = {'sfdc-base': '126.1.2'}
        exp_buddy_versions = {'sfdc-base': '126.1.2'}

        exp_cmds = ['release_runner.pl -versions sfdc-base@126.1.2 -c deploy -invdb_mode -superpod sp-2 -cluster abc '
                    '-cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host abc-ffx1-1-dc '
                    '-softly -no_db_data_init']

        exp_buddy_cmds = ['release_runner.pl -versions sfdc-base@126.1.2 -c deploy -invdb_mode -superpod sp-2 '
                          '-cluster abc -cluster_status IN_MAINTAINANCE -auto2  -host_status IN_MAINTAINANCE -no_lb -host '
                          'abc-ffx2-1-dc -softly -no_db_data_init']

        host_deployer.services.sort()
        self.assertListEqual(host_deployer.services, exp_services)
        self.assertDictEqual(host_deployer.versions, exp_versions)
        host_deployer.rr_cmds.sort()
        exp_cmds.sort()
        self.assertListEqual(host_deployer.rr_cmds, exp_cmds)

        self.assertDictEqual(host_deployer.buddy_versions, exp_buddy_versions)
        host_deployer.buddy_rr_cmds.sort()
        exp_buddy_cmds.sort()
        self.assertListEqual(host_deployer.buddy_rr_cmds, exp_buddy_cmds)

    def test_get_command_line(self):
        sys.argv = ['deploy_host.py', '--hosts', 'abc-ffx1-1-dc']
        cmd_str = get_command_line()
        expected_cmd_str = 'deploy_host.py --hosts abc-ffx1-1-dc '
        self.assertEqual(cmd_str, expected_cmd_str, "get_cmd_line did not return correct command line")


if __name__ == '__main__':
    unittest.main()
