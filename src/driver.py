import re

# from cloudshell.shell.core.interfaces.save_restore import OrchestrationSaveResult
# from cloudshell.shell.core.interfaces.save_restore import OrchestrationSavedArtifact
# from cloudshell.shell.core.interfaces.save_restore import OrchestrationSavedArtifactInfo
# from cloudshell.shell.core.interfaces.save_restore import OrchestrationRestoreRules
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.shell.core.driver_context import InitCommandContext
from cloudshell.shell.core.driver_context import ResourceCommandContext
from cloudshell.shell.core.driver_context import AutoLoadResource
from cloudshell.shell.core.driver_context import AutoLoadAttribute
from cloudshell.shell.core.driver_context import AutoLoadDetails
from cloudshell.shell.core.driver_context import CancellationContext

import os
from cloudshell.api.cloudshell_api import CloudShellAPISession
import time

# paramiko = None
import paramiko


class GigamonDriver (ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.ssh = None
        self.channel = None
        self.fakedata = None
        self._log('__init__ called')

    def _log(self, message):
        with open(r'c:\programdata\qualisystems\gigamon.log', 'a') as f:
            f.write(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()) + ': ' + message+'\r\n')

    def _ssh_connect(self, host, port, username, password, prompt_regex):
        if self.fakedata:
            return
        self._log('connect %s %d %s %s %s' % (host, port, username, password, prompt_regex))
        self.ssh = paramiko.SSHClient()
        self.ssh.load_system_host_keys()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host,
                    port=port,
                    username=username,
                    password=password,
                    look_for_keys=True)
        self.channel = self.ssh.invoke_shell()
        return self._ssh_read(prompt_regex)  # eat banner

    def _ssh_write(self, command):
        if self.fakedata:
            print command
            return
        self._log('sending: <<<' + command + '>>>')
        self.channel.send(command)
        self._log('send complete')

    def _ssh_read(self, prompt_regex):
        if self.fakedata:
            return
        rv = ''
        self._log('read...')
        while True:
            # self.channel.settimeout(30)
            self._log('recv')
            r = self.channel.recv(2048)
            self._log('recv returned: <<<' + str(r) + '>>>')
            if r:
                rv += r
            if not r or len(re.findall(prompt_regex, rv)) > 0:
                if rv:
                    rv = rv.replace('\r', '\n')
                self._log('read complete: <<<' + str(rv) + '>>>')
                return rv

    def _ssh_command(self, command, prompt_regex):
        if self.fakedata:
            print command
            if command in self.fakedata:
                print self.fakedata[command]
                return self.fakedata[command]
            else:
                return ''
        else:
            self._ssh_write(command + '\n')
            rv = self._ssh_read(prompt_regex)
            if '\n%' in rv.replace('\r', '\n'):
                es = 'CLI error message: ' + rv
                self._log(es)
                raise Exception(es)
            return rv

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        self._log('initialize called')

        if not self.fakedata:
            self.api = CloudShellAPISession(context.connectivity.server_address,
                                       token_id=context.connectivity.admin_auth_token,
                                       port=context.connectivity.cloudshell_api_port)

            o = self._ssh_connect(context.resource.address,
                                  22,
                                  context.resource.attributes['User'],
                                  self.api.DecryptPassword(context.resource.attributes['Password']).Value,
                                  '>|security purposes')

            if 'security purposes' in o:
                raise Exception('Switch password needs to be initialized: %s' % o)

            e = self._ssh_command('enable', '[#:]')
            if ':' in e:
                self._ssh_command(self.api.DecryptPassword(context.resource.attributes['Enable Password']).Value,
                                  '[^[#]# ')
        self._ssh_command('cli session terminal type dumb', '[^[#]# ')
        self._ssh_command('cli session terminal length 999', '[^[#]# ')

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
        running_saved = 'running' if configuration_type.lower() == 'running' else 'saved'

        if running_saved != 'running':
            raise Exception('Restoring config for "startup" is not implemented. Only "running" is implemented.')

        if restore_method == 'append':
            raise Exception('Restore method "append" is not implemented. Only "override" is implemented.')

        if '://' not in path:
            raise Exception('Path must include URL scheme such as tftp://')

        path = path.replace('.cfg', '.txt')

        self.api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Restoring config')

        self._ssh_command('configure terminal', '[^[#]# ')
        try:
            self._ssh_command('configuration fetch ' + path, '[^[#]# ')
            try:
                self._ssh_command('configuration copy Active.txt tmp.txt', '[^[#]# ')
            except:
                pass
            try:
                self._ssh_command('configuration switch-to tmp.txt', '[^[#]# ')
            except:
                pass
            try:
                self._ssh_command('configuration delete Active.txt', '[^[#]# ')
            except:
                pass

            self._ssh_command('configuration move %s Active.txt ' % (os.path.basename(path)), '[^[#]# ')

            try:
                self._ssh_command('configuration switch-to Active.txt', '[^[#]# ')
            except:
                # switch-to failed, tmp.txt still active
                try:
                    # get rid of new bad Active.txt
                    self._ssh_command('configuration delete Active.txt', '[^[#]# ')
                except:
                    pass
                # make tmp.txt the Active.txt again
                self._ssh_command('configuration copy tmp.txt Active.txt', '[^[#]# ')
                self._ssh_command('configuration switch-to Active.txt', '[^[#]# ')
            self._ssh_command('configuration delete tmp.txt', '[^[#]# ')
            self.api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Config loaded at %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        except Exception as e:
            self.api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Failed to load config: %s' % str(e))
        finally:
            self._ssh_command('exit', '[^[#]# ')

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
        running_saved = 'active' if configuration_type.lower() == 'running' else 'initial'

        if '://' not in folder_path:
            raise Exception('Destination folder path must include a URL scheme such as tftp://')

        self.api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Saving config')

        self._ssh_command('configure terminal', '[^[#]# ')
        try:
            if self.fakedata:
                path = 'fakepath/fakename_fakemodel.txt'
            else:
                path = '%s/%s_%s.txt' % (folder_path if not folder_path.endswith('/') else folder_path[0:-1],
                                        context.resource.name.replace(' ', '-'),
                                        context.resource.model.replace(' ', '-'))
            self._ssh_command('configuration upload %s %s' % (running_saved, path), '[^[#]# ')
            self.api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Config saved at %s' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
            return path
        except Exception as e:
            self.api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Failed to save config: %s' % str(e))
        finally:
            self._ssh_command('exit', '[^[#]# ')

    def load_firmware(self, context, cancellation_context, file_path, remote_host):
        """
        Upload and updates firmware on the resource
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str remote_host: path to tftp server where firmware file is stored
        :param str file_path: firmware file name
        """
        self.api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Loading firmware %s' % file_path)
        try:
            if '://' in file_path:
                self._ssh_command('image fetch %s' % file_path, '[^[#]# ')
            elif remote_host == 'none':
                pass
            else:
                self._ssh_command('image fetch tftp://%s/%s' % (remote_host, file_path), '[^[#]# ')
            self._ssh_command('image install %s' % (os.path.basename(file_path)), '[^[#]# ')
            self._ssh_command('image boot next', '[^[#]# ')
            self.api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Loaded firmware %s at %s' % (file_path, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())))
        except Exception as e:
            self.api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Failed to load firmware: %s' % str(e))

    def run_custom_command(self, context, cancellation_context, custom_command):
        """
        Executes a custom command on the device
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str custom_command: The command to run. Note that commands that require a response are not supported.
        :return: the command result text
        :rtype: str
        """
        return self._ssh_command(custom_command, '[^[#]# ')

    def run_custom_config_command(self, context, cancellation_context, custom_command):
        """
        Executes a custom command on the device in configuration mode
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param CancellationContext cancellation_context: Object to signal a request for cancellation. Must be enabled in drivermetadata.xml as well
        :param str custom_command: The command to run. Note that commands that require a response are not supported.
        :return: the command result text
        :rtype: str
        """

        self._ssh_command('configure terminal', '[^[#]# ')
        rv = self._ssh_command(custom_command, '[^[#]# ')
        self._ssh_command('exit', '[^[#]# ')
        return rv

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
        self.api.SetResourceLiveStatus(context.resource.fullname,  'Progress 10', 'Resetting switch')
        self._ssh_command('configure terminal', '[^[#]# ')

        self._ssh_command('reset factory only-traffic', ': ')
        self._ssh_command('YES', '.')
        self._log('Waiting 30 seconds...')
        time.sleep(30)

        retries = 0
        while retries < 30:
            try:
                self._log('Trying to connect...')
                self.initialize(context)
                self._log('Reconnected to device')
                self.api.SetResourceLiveStatus(context.resource.fullname,  'Online', 'Switch finished resetting at %s ' % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
                return
            except Exception as e:
                self._log('Not ready: ' + str(e))
                self._log('Waiting 10 seconds...')
                time.sleep(10)
                retries += 1
        self.api.SetResourceLiveStatus(context.resource.fullname,  'Error', 'Switch did not come up within 5 minutes after reset')
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
        pass

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
        pass

    # </editor-fold>

    # <editor-fold desc="Connectivity Provider Interface (Optional)">

    '''
    # The ApplyConnectivityChanges function is intended to be used for using switches as connectivity providers
    # for other devices. If the Switch shell is intended to be used a DUT only there is no need to implement it

    def ApplyConnectivityChanges(self, context, request):
        """
        Configures VLANs on multiple ports or port-channels
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str request: A JSON object with the list of requested connectivity changes
        :return: a json object with the list of connectivity changes which were carried out by the switch
        :rtype: str
        """

        pass

    '''

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

        sub_resources = []
        attributes = [AutoLoadAttribute('', "Vendor", 'Gigamon')]

        for line in self._ssh_command('show version', '[^[#]# ').split('\n'):
            if 'Version summary:' in line:
                attributes.append(AutoLoadAttribute('', "OS Version", line.replace('Version summary:', '').strip()))
            if 'Product model:' in line:
                attributes.append(AutoLoadAttribute('', "Model", line.replace('Product model:', '').strip()))

        chassisaddr = 'bad_chassis_addr'
        patt2attr = {}
        for line in self._ssh_command('show chassis', '[^[#]# ').split('\n'):
            if 'Box ID' in line:
                chassisaddr = line.replace('Box ID', '').replace(':', '').replace('*', '').strip()
                sub_resources.append(AutoLoadResource(model='Generic Chassis',
                                                      name='Chassis ' + chassisaddr,
                                                      relative_address=chassisaddr))
                patt2attr = {
                    'HW Type': 'Model',
                    'Serial Num': 'Serial Number'
                }

            for patt in list(patt2attr.keys()):
                if patt in line:
                    attributes.append(AutoLoadAttribute(chassisaddr, patt2attr[patt],
                                                    line.replace(patt, '').replace(':', '').strip()))
                    patt2attr.pop(patt, None)

        chassisaddr = 'bad_chassis_addr'
        for line in self._ssh_command('show card', '[^[#]# ').split('\n'):
            if 'Oper Status' in line:
                continue
            if 'Box ID' in line:
                chassisaddr = line.replace('Box ID', '').replace(':', '').replace('*', '').strip()
            #    1     yes     up           PRT-HC0-X24     132-00BD      1BD0-0189   A1-a2
            m = re.match(r'(?P<slot>\S+)\s+'
                         r'(?P<config>\S+)\s+'
                         r'(?P<oper_status>\S+)\s+'
                         r'(?P<hw_type>\S+)\s+'
                         r'(?P<product_code>\S+)\s+'
                         r'(?P<serial_num>\S+)\s+'
                         r'(?P<hw_rev>\S+)',
                         line)
            if m:
                d = m.groupdict()
                cardaddr = chassisaddr + '/' + d['slot']
                sub_resources.append(AutoLoadResource(model='Generic Module',
                                                      name='Card ' + d['slot'],
                                                      relative_address=cardaddr))

                attributes.append(AutoLoadAttribute(cardaddr, "Model", d['hw_type'] + ' - ' + d['product_code']))
                attributes.append(AutoLoadAttribute(cardaddr, "Version", d['hw_rev']))
                attributes.append(AutoLoadAttribute(cardaddr, "Serial Number", d['serial_num']))

        o = self._ssh_command('show port', '[^[#]# ')
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
                        self._log('regex failure on line <<<' + portline + '>>>')
                    continue
                # raise Exception('Failed to parse "show port" data: Line: <<<%s>>> All output: <<<%s>>>' % (portline, o))

            d = m.groupdict()

            portaddr = d['address']
            portnum = portaddr.split('/')[-1]
            self._log('Port ' + portaddr)
            sub_resources.append(AutoLoadResource(model='Generic Port',
                                                  name='Port ' + portnum,
                                                  relative_address=portaddr))

            attributes.append(AutoLoadAttribute(portaddr, "Port Description",
                                                '%s - xcvr %s - %s' % (d['type'].strip(), d['xcvr_type'].strip(), d.get('alias', 'noalias'))))
            if re.match(r'[0-9]+', d['speed']):
                attributes.append(AutoLoadAttribute(portaddr, "Bandwidth", 
                                                    d['speed']))

            attributes.append(AutoLoadAttribute(portaddr, "Duplex",
                                                'Full' if d['duplex'] == 'full' else 'Half'))
            
            attributes.append(AutoLoadAttribute(portaddr, "Auto Negotiation",
                                                'True' if d['auto_neg'] == 'on' else 'False'))

        return AutoLoadDetails(sub_resources, attributes)

    # </editor-fold>

    # <editor-fold desc="Health Check">

    def health_check(self,cancellation_context):
        """
        Checks if the device is up and connectable
        :return: None
        :exception Exception: Raises an error if cannot connect
        """
        pass

    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files
        """
        pass
