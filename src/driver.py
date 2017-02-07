import json
import re

import datetime
from cloudshell.shell.core.interfaces.save_restore import OrchestrationSaveResult
from cloudshell.shell.core.interfaces.save_restore import OrchestrationSavedArtifact
from cloudshell.shell.core.interfaces.save_restore import OrchestrationSavedArtifactInfo
from cloudshell.shell.core.interfaces.save_restore import OrchestrationRestoreRules
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext
from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.driver_context import AutoLoadCommandContext
from cloudshell.shell.core.driver_context import AutoLoadResource
from cloudshell.shell.core.driver_context import AutoLoadAttribute
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.driver_context import CancellationContext


import os
from cloudshell.api.cloudshell_api import CloudShellAPISession
from cloudshell.core.logger.qs_logger import get_qs_logger, log_execution_info

import time

# paramiko = None
import paramiko
import traceback
import sys

def myexcepthook(exctype, value, tb):
    x = []
    if issubclass(exctype, Exception):
        x.append("Exception type: " + str(exctype))
        x.append("Value called: " + str(value))
        x.append("Stacktrace: ")
        for trace in traceback.format_tb(tb):
            x.append(trace)
        try:
            logger = get_qs_logger('out-of-reservation', 'GigaVUE-OS', 'no-resource')
            logger.error('\r\n'.join(x))
        except Exception as e:
            try:
                with open(r'c:\programdata\qualisystems\gigamon.log', 'a') as f:
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' qs_logger failed: ' + str(e)+'\r\n')
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' (QS LOGGER NOT WORKING): ' + '\r\n'.join(x)+'\r\n')
            except:
                pass
    sys.__excepthook__(exctype, value, traceback)


sys.excepthook = myexcepthook


class GigamonDriverPortUniqueId (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.fakedata = None
        self._fulladdr2alias = {}
        self._log(None, 'GigamonDriverPortUniqueId __init__ called\r\n')

    def _log(self, context, message):
        # with open(r'c:\programdata\qualisystems\gigamon.log', 'a') as f:
        #     f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' GigamonDriverPortUniqueId _log called\r\n')
        try:
            try:
                resid = context.reservation.reservation_id
            except:
                resid = 'out-of-reservation'
            try:
                resourcename = context.resource.fullname
            except:
                resourcename = 'no-resource'
            logger = get_qs_logger(resid, 'GigaVUE-OS-L2', resourcename)
            logger.info(message)
        except Exception as e:
            try:
                with open(r'c:\programdata\qualisystems\gigamon.log', 'a') as f:
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' qs_logger failed: ' + str(e)+'\r\n')
                    f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ' (QS LOGGER NOT WORKING): ' + message+'\r\n')
            except:
                pass

    def _ssh_disconnect(self, context, ssh, channel):
        self._log(context, 'disconnnect')
        if self.fakedata:
            return
        ssh.close()

    def _ssh_connect(self, context, host, port, username, password, alternate_password, prompt_regex):
        self._log(context, 'connect %s %d %s %s %s %s' % (host, port, username, password, alternate_password, prompt_regex))
        if self.fakedata:
            return
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        tries = 0
        pw = password
        while True:
            try:
                tries += 1
                ssh.connect(host,
                            port=port,
                            username=username,
                            password=pw,
                            look_for_keys=True)
                channel = ssh.invoke_shell()
                rv = ''
                s = self._ssh_read(context, ssh, channel, prompt_regex + '|Admin Password:')  # eat banner and first prompt, or detect new password prompt
                rv += s
                if 'Admin Password:' in s:  # we are being required to enter a new password
                    time.sleep(5)
                    self._ssh_write(context, ssh, channel, password + '\n')  # enter new password
                    s = self._ssh_read(context, ssh, channel, 'Admin Password:|Confirm:')
                    rv += s
                    if 'Admin Password:' in s:
                        self._ssh_write(context, ssh, channel, password + '\n')  # reenter new password
                        s = self._ssh_read(context, ssh, channel, 'Confirm:')
                        rv += s
                    self._ssh_write(context, ssh, channel, password + '\n')  # reenter new password
                    s = self._ssh_read(context, ssh, channel, prompt_regex)  # eat first prompt
                    rv += s
                return ssh, channel, rv
            except Exception as e:
                if tries >= 8:
                    self._log(context, 'SSH connection failed after 4 tries of normal and alternate passwords')
                    raise e
                if pw == password:
                    pw = alternate_password
                else:
                    pw = password
                self._log(context, 'Password rejected or other connectivity error: %s\nsleeping 10 seconds and retrying...' % str(e))
                time.sleep(10)



    def _ssh_write(self, context, ssh, channel, command):
        self._log(context, 'sending: <<<' + command + '>>>')
        if self.fakedata:
            print command
            return
        channel.send(command)
        self._log(context, 'send complete')

    def _ssh_read(self, context, ssh, channel, prompt_regex):
        if self.fakedata:
            return
        rv = ''
        self._log(context, 'read...')
        while True:
            # self.channel.settimeout(30)
            self._log(context, 'recv')
            r = channel.recv(2048)
            self._log(context, 'recv returned: <<<' + str(r) + '>>>')
            if r:
                rv += r
            if rv:
                t = rv
                t = re.sub(r'(\x9b|\x1b)[[?;0-9]*[a-zA-Z]', '', t)
                t = re.sub(r'(\x9b|\x1b)[>=]', '', t)
                t = re.sub('.\b', '', t) # not r''
            else:
                t = ''
            if not r or len(re.findall(prompt_regex, t)) > 0:
                rv = t
                if rv:
                    rv = rv.replace('\r', '\n')
                self._log(context, 'read complete: <<<' + str(rv) + '>>>')
                return rv

    def _ssh_command(self, context, ssh, channel, command, prompt_regex):
        if self.fakedata:
            print command
            if command in self.fakedata:
                print self.fakedata[command]
                return self.fakedata[command]
            else:
                return ''
        else:
            self._ssh_write(context, ssh, channel, command + '\n')
            rv = self._ssh_read(context, ssh, channel, prompt_regex)
            if '\n%' in rv.replace('\r', '\n'):
                es = 'CLI error message: ' + rv
                self._log(context, es)
                raise Exception(es)
            return rv

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        self._log(context, 'GigamonDriverPortUniqueId initialize called\r\n')

    def _connect(self, context):
        self._log(context, 'GigamonDriverPortUniqueId _connect called\r\n')
        if self.fakedata:
            return None, None, None

        try:
            domain = context.reservation.domain
        except:
            domain = 'Global'

        api = CloudShellAPISession(context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   port=context.connectivity.cloudshell_api_port,
                                   domain=domain)

        ssh, channel, o = self._ssh_connect(context, context.resource.address,
                              22,
                              context.resource.attributes['User'],
                              api.DecryptPassword(context.resource.attributes['Password']).Value,
                              api.DecryptPassword(context.resource.attributes['Alternate Password']).Value,
                              '>')

        e = self._ssh_command(context, ssh, channel, 'enable', '[#:]')
        if ':' in e:
            self._ssh_command(context, ssh, channel, api.DecryptPassword(context.resource.attributes['Enable Password']).Value,
                              '[^[#]# ')
        # self._ssh_command(context, ssh, channel, 'cli session terminal type dumb', '[^[#]# ')
        self._ssh_command(context, ssh, channel, 'cli session terminal length 999', '[^[#]# ')
        return ssh, channel, o

    def _disconnect(self, context, ssh, channel):
        if self.fakedata:
            return
        self._ssh_disconnect(context, ssh, channel)

    # <editor-fold desc="Networking Standard Commands">
    def restore(self, context, cancellation_context, path, restore_method, configuration_type, vrf_management_name):
        """
        Restores a configuration file
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str path: The path to the configuration file, including the configuration file name.
        :param str restore_method: Determines whether the restore should append or override the current configuration.
        :param str configuration_type: Specify whether the file should update the startup or running config.
        :param str vrf_management_name: Optional. Virtual routing and Forwarding management name
        """
        self._log(context, 'restore called with inputs path=%s restore_method=%s configuration_type=%s vrf_management_name=%s' % (path, restore_method, configuration_type, vrf_management_name))

        running_saved = 'running' if configuration_type.lower() == 'running' else 'saved'
        if running_saved != 'running':
            raise Exception('Restoring config for "startup" is not implemented. Only "running" is implemented.')

        if restore_method == 'append':
            raise Exception('Restore method "append" is not implemented. Only "override" is implemented.')

        if '://' not in path:
            raise Exception('Path must include URL scheme such as tftp://')

        path = path.replace('.cfg', '.txt')

        api = CloudShellAPISession(context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   port=context.connectivity.cloudshell_api_port,
                                   domain=context.reservation.domain)

        api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Restoring config')

        ssh, channel, _ = self._connect(context)
        m = []
        try:
            m.append(self._ssh_command(context, ssh, channel, 'configure terminal', '[^[#]# '))
            try:
                try:
                    # delete existing file if it exists
                    m.append(self._ssh_command(context, ssh, channel, 'configuration delete %s' % (os.path.basename(path)), '[^[#]# '))
                except Exception as e:
                    m.append(str(e))

                m.append(self._ssh_command(context, ssh, channel, 'configuration fetch ' + path, '[^[#]# '))
                try:
                    m.append(self._ssh_command(context, ssh, channel, 'configuration copy Active.txt tmp.txt', '[^[#]# '))
                except Exception as e:
                    m.append(str(e))
                try:
                    m.append(self._ssh_command(context, ssh, channel, 'configuration switch-to tmp.txt', '[^[#]# '))
                except Exception as e:
                    m.append(str(e))
                try:
                    m.append(self._ssh_command(context, ssh, channel, 'configuration delete Active.txt', '[^[#]# '))
                except Exception as e:
                    m.append(str(e))

                m.append(self._ssh_command(context, ssh, channel, 'configuration move %s Active.txt ' % (os.path.basename(path)), '[^[#]# '))

                try:
                    m.append(self._ssh_command(context, ssh, channel, 'configuration switch-to Active.txt', '[^[#]# '))
                except Exception as e:
                    m.append(str(e))
                    # switch-to failed, tmp.txt still active
                    try:
                        # get rid of new bad Active.txt
                        m.append(self._ssh_command(context, ssh, channel, 'configuration delete Active.txt', '[^[#]# '))
                    except Exception as e:
                        m.append(str(e))
                    # make tmp.txt the Active.txt again
                    m.append(self._ssh_command(context, ssh, channel, 'configuration copy tmp.txt Active.txt', '[^[#]# '))
                    m.append(self._ssh_command(context, ssh, channel, 'configuration switch-to Active.txt', '[^[#]# '))
                try:
                    m.append(self._ssh_command(context, ssh, channel, 'configuration delete tmp.txt', '[^[#]# '))
                except Exception as e:
                    m.append(str(e))
                api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Config loaded at %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            except Exception as e2:
                m.append(str(e2))
                api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Failed to load config: %s' % '\n'.join(m))
                raise e2
            finally:
                self._ssh_command(context, ssh, channel, 'exit', '[^[#]# ')
        finally:
            self._disconnect(context, ssh, channel)

    def save(self, context, cancellation_context, configuration_type, folder_path, vrf_management_name):
        """
        Creates a configuration file and saves it to the provided destination.
        For a local file, specify the full filename to save. Folders may not be supported.
        For a network location, specify a URL to a folder, e.g. tftp://ip/a
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str configuration_type: Specify whether the file should update the startup or running config. Value can one
        :param str folder_path: The path to the folder in which the configuration file will be saved.
        :param str vrf_management_name: Optional. Virtual routing and Forwarding management name
        :return The configuration file name.
        :rtype: str
        """
        self._log(context, 'GigamonDriverPortUniqueId save called\r\n')

        running_saved = 'active' if configuration_type.lower() == 'running' else 'initial'

        if '://' not in folder_path:
            raise Exception('Destination folder path must include a URL scheme such as tftp://')

        api = CloudShellAPISession(context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   port=context.connectivity.cloudshell_api_port,
                                   domain=context.reservation.domain)
        api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Saving config')

        ssh, channel, _ = self._connect(context)
        try:
            self._ssh_command(context, ssh, channel, 'configure terminal', '[^[#]# ')
            try:
                if self.fakedata:
                    path = 'fakepath/fakename_fakemodel.txt'
                else:
                    self._log(context, 'Attributes: %s' % str(context.resource.attributes))
                    model = context.resource.attributes.get('Model', '')
                    if not model:
                        model = context.resource.model
                    path = '%s/%s_%s.txt' % (folder_path if not folder_path.endswith('/') else folder_path[0:-1],
                                            context.resource.name.replace(' ', '-'),
                                            model.replace(' ', '-'))
                self._ssh_command(context, ssh, channel, 'configuration write', '[^[#]# ')
                self._ssh_command(context, ssh, channel, 'configuration upload %s %s' % (running_saved, path), '[^[#]# ')
                api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Config saved at %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
                return path
            except Exception as e:
                api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Failed to save config: %s' % str(e))
                raise e
            finally:
                self._ssh_command(context, ssh, channel, 'exit', '[^[#]# ')
        finally:
            self._disconnect(context, ssh, channel)

    def load_firmware(self, context, cancellation_context, file_path, remote_host):
        """
        Upload and updates firmware on the resource
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str remote_host: path to tftp server where firmware file is stored
        :param str file_path: firmware file name
        """
        api = CloudShellAPISession(context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   port=context.connectivity.cloudshell_api_port,
                                   domain=context.reservation.domain)
        api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Loading firmware %s' % file_path)
        ssh, channel, _ = self._connect(context)
        try:
            if '://' in file_path:
                self._ssh_command(context, ssh, channel, 'image fetch %s' % file_path, '[^[#]# ')
            elif remote_host == 'none':
                pass
            else:
                self._ssh_command(context, ssh, channel, 'image fetch tftp://%s/%s' % (remote_host, file_path), '[^[#]# ')
            self._ssh_command(context, ssh, channel, 'image install %s' % (os.path.basename(file_path)), '[^[#]# ')
            self._ssh_command(context, ssh, channel, 'image boot next', '[^[#]# ')

            self._ssh_command(context, ssh, channel, 'image delete %s' % (os.path.basename(file_path)), '[^[#]# ')

            api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Loaded firmware %s at %s' % (file_path, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
        except Exception as e:
            api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Failed to load firmware: %s' % str(e))
        finally:
            self._disconnect(context, ssh, channel)

    def run_custom_command(self, context, cancellation_context, custom_command):
        """
        Executes a custom command on the device
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str custom_command: The command to run. Note that commands that require a response are not supported.
        :return: the command result text
        :rtype: str
        """
        ssh, channel, _ = self._connect(context)
        try:
            self._ssh_command(context, ssh, channel, custom_command, '[^[#]# ')
        finally:
            self._disconnect(context, ssh, channel)

    def run_custom_config_command(self, context, cancellation_context, custom_command):
        """
        Executes a custom command on the device in configuration mode
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str custom_command: The command to run. Note that commands that require a response are not supported.
        :return: the command result text
        :rtype: str
        """

        ssh, channel, _ = self._connect(context)
        try:
            self._ssh_command(context, ssh, channel, 'configure terminal', '[^[#]# ')
            rv = self._ssh_command(context, ssh, channel, custom_command, '[^[#]# ')
            self._ssh_command(context, ssh, channel, 'exit', '[^[#]# ')
            return rv
        finally:
            self._disconnect(context, ssh, channel)

    def shutdown(self, context, cancellation_context):
        """
        Sends a graceful shutdown to the device
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        """
        pass

    def reset(self, context, cancellation_context):
        """
        Resets the device to factory settings
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        """
        api = CloudShellAPISession(context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   port=context.connectivity.cloudshell_api_port,
                                   domain=context.reservation.domain)

        api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Resetting switch')

        ssh, channel, _ = self._connect(context)
        self._ssh_command(context, ssh, channel, 'configure terminal', '[^[#]# ')

        self._ssh_command(context, ssh, channel, 'reset factory only-traffic', ': ')
        self._ssh_command(context, ssh, channel, 'YES', '.')
        try:
            self._disconnect(context, ssh, channel)
        except:
            pass
        self._log(context, 'Waiting 30 seconds...')
        time.sleep(30)

        retries = 0
        while retries < 30:
            try:
                self._log(context, 'Trying to connect...')
                ssh, channel, _ = self._connect(context)
                self._log(context, 'Reconnected to device')
                self._disconnect(context, ssh, channel)
                api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Switch finished resetting at %s ' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
                return
            except Exception as e:
                self._log(context, 'Not ready: ' + str(e))
                self._log(context, 'Waiting 10 seconds...')
                time.sleep(10)
                retries += 1
        api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Switch did not come up within 5 minutes after reset')
        raise Exception('Device did not come up within 5 minutes after reset')

    # </editor-fold>

    # <editor-fold desc="Orchestration Save and Restore Standard">
    def orchestration_save(self, context, cancellation_context, mode, custom_params=None):
        """
        Saves the Shell state and returns a description of the saved artifacts and information
        This command is intended for API use only by sandbox orchestration scripts to implement
        a save and restore workflow
        :param ResourceCommandContext context: the context object containing resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str mode: Snapshot save mode, can be one of two values 'shallow' (default) or 'deep'
        :param str custom_params: Set of custom parameters for the save operation
        :return: SavedResults serialized as JSON
        :rtype: OrchestrationSaveResult
        """

        # See below an example implementation, here we use jsonpickle for serialization,
        # to use this sample, you'll need to add jsonpickle to your requirements.txt file
        # The JSON schema is defined at: https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/saved_artifact_info.schema.json
        # You can find more information and examples examples in the spec document at https://github.com/QualiSystems/sandbox_orchestration_standard/blob/master/save%20%26%20restore/save%20%26%20restore%20standard.md
        '''
        # By convention, all dates should be UTC
        created_date = datetime.datetime.utcnow()

        # This can be any unique identifier which can later be used to retrieve the artifact
        # such as filepath etc.

        # By convention, all dates should be UTC
        created_date = datetime.datetime.utcnow()

        # This can be any unique identifier which can later be used to retrieve the artifact
        # such as filepath etc.
        identifier = created_date.strftime('%y_%m_%d %H_%M_%S_%f')

        orchestration_saved_artifact = OrchestrationSavedArtifact('REPLACE_WITH_ARTIFACT_TYPE', identifier)

        saved_artifacts_info = OrchestrationSavedArtifactInfo(
            resource_name="some_resource",
            created_date=created_date,
            restore_rules=OrchestrationRestoreRules(requires_same_resource=True),
            saved_artifact=orchestration_saved_artifact)

        return OrchestrationSaveResult(saved_artifacts_info)
        '''
        self._log(context, 'GigamonDriverPortUniqueId orchestration_save called: %s\r\n' % custom_params)

        p = json.loads(custom_params)
        if 'folder_path' not in p:
            raise Exception('Input JSON should be {"folder_path": "tftp://host/path"}')

        identifier_url = self.save(
            context=context,
            cancellation_context=cancellation_context,
            configuration_type=p.get('configuration_type', 'running'),
            folder_path=p['folder_path'],
            vrf_management_name='no-vrf'
        )
        created_date = datetime.datetime.utcnow()
        orchestration_saved_artifact = OrchestrationSavedArtifact('tftp', identifier_url)
        saved_artifacts_info = OrchestrationSavedArtifactInfo(
            resource_name="some_resource",
            created_date=created_date,
            restore_rules=OrchestrationRestoreRules(requires_same_resource=True),
            saved_artifact=orchestration_saved_artifact)

        self._log(context, 'GigamonDriverPortUniqueId orchestration_save returning\r\n')

        return OrchestrationSaveResult(saved_artifacts_info)

    def orchestration_restore(self, context, cancellation_context, saved_details):
        """
        Restores a saved artifact previously saved by this Shell driver using the orchestration_save function
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str saved_details: A JSON string representing the state to restore including saved artifacts and info
        :return: None
        """
        '''
        # The saved_details JSON will be defined according to the JSON Schema and is the same object returned via the
        # orchestration save function.
        # Example input:
        # {
        #     "saved_artifact": {
        #      "artifact_type": "REPLACE_WITH_ARTIFACT_TYPE",
        #      "identifier": "16_08_09 11_21_35_657000"
        #     },
        #     "resource_name": "some_resource",
        #     "restore_rules": {
        #      "requires_same_resource": true
        #     },
        #     "created_date": "2016-08-09T11:21:35.657000"
        #    }

        # The example code below just parses and prints the saved artifact identifier
        saved_details_object = json.loads(saved_details)
        return saved_details_object[u'saved_artifact'][u'identifier']
        '''

        self._log(context, 'GigamonDriverPortUniqueId orchestration_restore called with input <<<%s>>>\r\n' % saved_details)


        saved_details_object = json.loads(saved_details)
        try:
            url = saved_details_object['saved_artifact']['identifier']
        except:
            url = saved_details_object['saved_artifacts_info']['saved_artifact']['identifier']

        self.restore(
            context=context,
            cancellation_context=cancellation_context,
            path=url,
            restore_method='overwrite',
            configuration_type='running',
            vrf_management_name='no-vrf'
        )

    # </editor-fold>

    # <editor-fold desc="Connectivity Provider Interface (Optional)">


    # The ApplyConnectivityChanges function is intended to be used for using switches as connectivity providers
    # for other devices. If the Switch shell is intended to be used a DUT only there is no need to implement it

    def _refresh_aliases(self, context):
        """
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        """
        api = CloudShellAPISession(context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   port=context.connectivity.cloudshell_api_port,
                                   domain=context.reservation.domain)

        self._fulladdr2alias = {}

        def rtrav(d):
            for attr in d.ResourceAttributes:
                if attr.Name == 'Alias':
                    self._fulladdr2alias[d.FullAddress] = attr.Value
            for dd in d.ChildResources:
                rtrav(dd)

        rtrav(api.GetResourceDetails(context.resource.fullname))


    # </editor-fold>

    # <editor-fold desc="Discovery">

    def get_inventory(self, context):
        """
        Discovers the resource structure and attributes.
        :param AutoLoadCommandContext context: the context the command runs on
        :return Attribute and sub-resource information for the Shell resource you can return an AutoLoadDetails object
        :rtype: AutoLoadDetails
        """
        # See below some example code demonstrating how to return the resource structure
        # and attributes. In real life, of course, if the actual values are not static,
        # this code would be preceded by some SNMP/other calls to get the actual resource information


        '''
           # Add sub resources details
           sub_resources = [ AutoLoadResource(model ='Generic Chassis',name= 'Chassis 1', relative_address='1'),
           AutoLoadResource(model='Generic Module',name= 'Module 1',relative_address= '1/1'),
           AutoLoadResource(model='Generic Port',name= 'Port 1', relative_address='1/1/1'),
           AutoLoadResource(model='Generic Port', name='Port 2', relative_address='1/1/2'),
           AutoLoadResource(model='Generic Power Port', name='Power Port', relative_address='1/PP1')]


           attributes = [ AutoLoadAttribute(relative_address='', attribute_name='Location', attribute_value='Santa Clara Lab'),
                          AutoLoadAttribute('', 'Model', 'Catalyst 3850'),
                          AutoLoadAttribute('', 'Vendor', 'Cisco'),
                          AutoLoadAttribute('1', 'Serial Number', 'JAE053002JD'),
                          AutoLoadAttribute('1', 'Model', 'WS-X4232-GB-RJ'),
                          AutoLoadAttribute('1/1', 'Model', 'WS-X4233-GB-EJ'),
                          AutoLoadAttribute('1/1', 'Serial Number', 'RVE056702UD'),
                          AutoLoadAttribute('1/1/1', 'MAC Address', 'fe80::e10c:f055:f7f1:bb7t16'),
                          AutoLoadAttribute('1/1/1', 'IPv4 Address', '192.168.10.7'),
                          AutoLoadAttribute('1/1/2', 'MAC Address', 'te67::e40c:g755:f55y:gh7w36'),
                          AutoLoadAttribute('1/1/2', 'IPv4 Address', '192.168.10.9'),
                          AutoLoadAttribute('1/PP1', 'Model', 'WS-X4232-GB-RJ'),
                          AutoLoadAttribute('1/PP1', 'Port Description', 'Power'),
                          AutoLoadAttribute('1/PP1', 'Serial Number', 'RVE056702UD')]

           return AutoLoadDetails(sub_resources,attributes)
        '''

        ssh, channel, _ = self._connect(context)
        sub_resources = []
        attributes = [AutoLoadAttribute('', "Vendor", 'Gigamon')]

        for line in self._ssh_command(context, ssh, channel, 'show version', '[^[#]# ').split('\n'):
            if 'Version summary:' in line:
                attributes.append(AutoLoadAttribute('', "OS Version", line.replace('Version summary:', '').strip()))
            if 'Product model:' in line:
                m = line.replace('Product model:', '').strip()
                m = {
                    'gvcc2': 'GigaVUE-HD8',
                }.get(m, m)
                attributes.append(AutoLoadAttribute('', "Model", m))

        chassisaddr = 'bad_chassis_addr'
        already = set()
        for line in self._ssh_command(context, ssh, channel, 'show chassis', '[^[#]# ').split('\n'):
            if 'Box ID' in line:
                chassisaddr = line.replace('Box ID', '').replace(':', '').replace('*', '').strip()
                if chassisaddr == '-':
                    chassisaddr = 'bad_chassis_addr'
                already = set()

            if chassisaddr != 'bad_chassis_addr':
                if 'HW Type' in line and 'HW Type' not in already:
                    already.add('HW Type')
                    attributes.append(AutoLoadAttribute(chassisaddr, 'Model', line.replace('HW Type', '').replace(':', '').strip()))
                if 'Serial Num' in line and 'Serial Num' not in already:
                    already.add('Serial Num')
                    serial = line.replace('Serial Num', '').replace(':', '').strip()
                    attributes.append(AutoLoadAttribute(chassisaddr, 'Serial Number', serial))
                    sub_resources.append(AutoLoadResource(model='Generic Chassis',
                                                          name='Chassis ' + chassisaddr,
                                                          relative_address=chassisaddr,
                                                          unique_identifier='gigamon_%s' % serial))

        cardaddr2card_uniqueid = {}
        chassisaddr = 'bad_chassis_addr'
        for line in self._ssh_command(context, ssh, channel, 'show card', '[^[#]# ').split('\n'):
            if 'Oper Status' in line:
                continue
            if 'Box ID' in line:
                chassisaddr = line.replace('Box ID', '').replace(':', '').replace('*', '').strip()
                if chassisaddr.lower() == 'not configured':
                    chassisaddr = 'bad_chassis_addr'
            #    1     yes     up           PRT-HC0-X24     132-00BD      1BD0-0189   A1-a2
            m = re.match(r'(?P<slot>\S+)\s+'
                         r'(?P<config>\S+)\s+'
                         r'(?P<oper_status>\S+)\s+'
                         r'(?P<hw_type>\S+)\s+'
                         r'(?P<product_code>\S+)\s+'
                         r'(?P<serial_num>\S+)\s+'
                         r'(?P<hw_rev>\S+)',
                         line)
            if m and chassisaddr != 'bad_chassis_addr':
                d = m.groupdict()
                cardaddr = chassisaddr + '/' + d['slot']
                card_uniqueid = 'gigamon_%s' % d['serial_num']
                cardaddr2card_uniqueid[cardaddr] = card_uniqueid
                sub_resources.append(AutoLoadResource(model='Generic Module',
                                                      name='Card ' + d['slot'],
                                                      relative_address=cardaddr,
                                                      unique_identifier=card_uniqueid))

                attributes.append(AutoLoadAttribute(cardaddr, "Model", d['hw_type'] + ' - ' + d['product_code']))
                attributes.append(AutoLoadAttribute(cardaddr, "Version", d['hw_rev']))
                attributes.append(AutoLoadAttribute(cardaddr, "Serial Number", d['serial_num']))

        try:
            o = self._ssh_command(context, ssh, channel, 'show port alias', '[^[#]# ')
        except Exception as e:
            if 'no port alias configured' not in str(e) and 'no chassis configured' not in str(e):
                raise e
            o = ''
        addr2alias = {}
        if o:
            o = o.replace('\r', '')
            # self.log('o1=<<<' + o + '>>>')
            o = '\n'.join(o.split('----\n')[1:]).split('\n----')[0]
            for aliasline in o.split('\n'):
                m = re.match(r'(?P<address>\S+)\s+'
                             r'(?P<type>\S+)\s+'
                             r'(?P<alias>\S.*)',
                             aliasline)
                if not m:
                    continue
                d = m.groupdict()
                addr2alias[d['address']] = d['alias']

        self._fulladdr2alias = {}
        try:
            o = self._ssh_command(context, ssh, channel, 'show port', '[^[#]# ')
        except Exception as e:
            if 'no chassis configured' not in str(e):
                raise e
            o = ''
        if o:
            o = o.replace('\r', '')
            # self.log('o1=<<<' + o + '>>>')
            o = '\n'.join(o.split('----\n')[1:]).split('\n----')[0]
            # self.log('o2=<<<' + o + '>>>')
            for portline in o.split('\n'):
                m = re.match(r'(?P<address>\S+)\s+'
                             r'(?P<type>\S+)\s+'
                             r'(?P<alias>\S+)\s+'
                             r'(?P<admin_enabled>enabled|disabled)\s+'
                             r'(?P<link_status>down|up|-)\s+'
                             r'(?P<min_max_thld_power>[-0-9. ]+)\s+'
                             r'(?P<xcvr_type>.+)\s+'
                             r'(?P<auto_neg>on|off|N/A)\s+'
                             r'(?P<speed>[-0-9]+)\s+'
                             r'(?P<duplex>\S+)\s+'
                             r'(?P<force_up>on|off)\s+'
                             r'(?P<port_relay>\S+)\s*'
                             r'(?P<discovery>\S*)',
                             portline)
                if not m:
                    m = re.match(r'(?P<address>\S+)\s+'
                                 r'(?P<type>\S+)\s+'
                                 r'(?P<admin_enabled>enabled|disabled)\s+'
                                 r'(?P<link_status>down|up|-)\s+'
                                 r'(?P<min_max_thld_power>[-0-9. ]+)\s+'
                                 r'(?P<xcvr_type>.+)\s+'
                                 r'(?P<auto_neg>on|off|N/A)\s+'
                                 r'(?P<speed>[-0-9]+)\s+'
                                 r'(?P<duplex>\S+)\s+'
                                 r'(?P<force_up>on|off)\s+'
                                 r'(?P<port_relay>\S+)\s*'
                                 r'(?P<discovery>\S*)',
                                 portline)
                    if not m:
                        if portline:
                            self._log(context, 'regex failure on line <<<' + portline + '>>>')
                        continue
                    # raise Exception('Failed to parse "show port" data: Line: <<<%s>>> All output: <<<%s>>>' % (portline, o))

                d = m.groupdict()

                portaddr = d['address']
                cardaddr = '/'.join(portaddr.split('/')[0:-1])
                cardserial = cardaddr2card_uniqueid[cardaddr]
                portnum = portaddr.split('/')[-1]
                port_uniqueid = 'gigamon_%s_%s' % (cardserial, portnum)
                self._log(context, 'Port ' + portaddr)
                sub_resources.append(AutoLoadResource(model='Generic Port',
                                                      name='Port ' + portnum,
                                                      relative_address=portaddr,
                                                      unique_identifier=port_uniqueid))

                attributes.append(AutoLoadAttribute(portaddr, "Port Role", d['type'].strip()))

                if portaddr in addr2alias:
                    attributes.append(AutoLoadAttribute(portaddr, "Alias", addr2alias[portaddr]))
                    self._fulladdr2alias[context.resource.address + '/' + portaddr] = addr2alias[portaddr]
                else:
                    attributes.append(AutoLoadAttribute(portaddr, "Alias", ''))

                attributes.append(AutoLoadAttribute(portaddr, "Transceiver Type", d['xcvr_type'].strip()))

                if re.match(r'[0-9]+', d['speed']):
                    attributes.append(AutoLoadAttribute(portaddr, "Bandwidth",
                                                        d['speed']))

                attributes.append(AutoLoadAttribute(portaddr, "Duplex",
                                                    'Full' if d['duplex'] == 'full' else 'Half'))

                attributes.append(AutoLoadAttribute(portaddr, "Auto Negotiation",
                                                    'True' if d['auto_neg'] == 'on' else 'False'))

        rv = AutoLoadDetails(sub_resources, attributes)
        for res in rv.resources:
            self._log(context, 'model=%s name=%s address=%s uniqueid=%s' % (res.model, res.name, res.relative_address, res.unique_identifier))
        for attr in rv.attributes:
            self._log(context, '%s: %s = %s' % (attr.relative_address, attr.attribute_name, attr.attribute_value))
        self._disconnect(context, ssh, channel)
        return rv

    # </editor-fold>

    # <editor-fold desc="Health Check">

    def health_check(self, context, cancellation_context):
        """
        Checks if the device is up and connectable
        :return: Health check on resource ___ passed|failed
        :exception Exception: Raises an error if cannot connect
        """
        api = CloudShellAPISession(context.connectivity.server_address,
                                   token_id=context.connectivity.admin_auth_token,
                                   port=context.connectivity.cloudshell_api_port,
                                   domain=context.reservation.domain)

        rv = 'Health check on resource %s passed' % context.resource.fullname
        api.SetResourceLiveStatus(context.resource.fullname,  'Online', rv)
        return rv


    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass
