import json
import requests
import logging
import sched
import threading
import time
from dateutil.relativedelta import *

from datetime import datetime
from dateutil import parser
from threading import Event

class Device(object):
    """ Base class definition of a device in the alarm system. """

    # Property variables
    __id = None
    __name = None
    __zone = None
    __device_type = None
    __subtype = None
    __preenroll = None
    __warnings = None
    __partitions = None

    def __init__(self, id, name, zone, device_type, subtype,
                 preenroll, warnings, partitions):
        """ Set the private variable values on instantiation. """

        self.__id = id
        self.__name = name
        self.__zone = zone
        self.__device_type = device_type
        self.__subtype = subtype
        self.__preenroll = preenroll
        self.__warnings = warnings
        self.__partitions = partitions

    # Device properties
    @property
    def id(self):
        """ Device ID. """
        return self.__id

    @property
    def name(self):
        """ Device Name. """
        return self.__name

    @property
    def zone(self):
        """ Device zone. """
        return self.__zone

    @property
    def device_type(self):
        """ Device: device type. """
        return self.__device_type

    @property
    def subtype(self):
        """ Device subtype. """
        return self.__subtype

    @property
    def pre_enroll(self):
        """ Device pre_enroll. """
        return self.__preenroll

    @property
    def warnings(self):
        """ Device alarm count. """
        return self.__warnings

    @property
    def partitions(self):
        """ Device partitions. """
        return self.__partitions


class ContactDevice(Device):
    """ Contact device class definition. """

    @property
    def state(self):
        """ Returns the current state of the contact. """
        if self.warnings:
            if 'OPENED' in str(self.warnings):
                return 'opened'
            else:
                return 'closed'
        else:
            return 'closed'

class CameraDevice(Device):
    """ Camera device class definition. """

    @property
    def state(self):
        """ Returns the current state of the camera. """
        return 'UKNOWN'

class SmokeDevice(Device):
    """ Smoke device class definition. """

    @property
    def state(self):
        """ Returns the current state of the smoke. """
        return 'UKNOWN'

class MotionDevice(Device):
    """ Motion device class definition. """

    @property
    def state(self):
        """ Returns the current state of the motion. """
        return 'UKNOWN'

class GenericDevice(Device):
    """ Generic device class definition. """

    @property
    def state(self):
        """ Returns the current state of the motion. """
        return 'UKNOWN'

class System(object):
    """ Class definition of the main alarm system. """

    # API Connection
    __api = None

    # Property variables
    __system_serial = None
    __system_model = None
    __system_ready = False
    __system_state = None
    __system_alerts = None
    __system_troubles = None
    __system_connected = False
    __system_alarm = False
    __system_devices = []

    def __init__(self, hostname, app_id, user_code, user_email, user_password, panel_id, partition):
        """ Initiate the connection to the Visonic API """
        self.__api = API(hostname, app_id, user_code, user_email, user_password, panel_id, partition)

    # System properties
    @property
    def serial_number(self):
        """ Serial number of the system. """
        return self.__system_serial

    @property
    def model(self):
        """ Model of the system. """
        return self.__system_model

    @property
    def ready(self):
        """ If the system is ready to be armed. If doors or windows are open
        the system can't be armed. """
        return self.__system_ready

    @property
    def state(self):
        """ Current state of the alarm system. """
        return self.__system_state

    @property
    def alarm(self):
        """ Current alarm of the alarm system. """
        return self.__system_alarm

    @property
    def is_token_valid(self):
        """ If the alarm system is active or not. """
        return self.__api.is_logged_in

    @property
    def session_token(self):
        """ Return the current session token. """
        return self.__api.session_token

    @property
    def connected(self):
        """ If the alarm system is connected to the API server or not. """
        return self.__system_connected

    @property
    def devices(self):
        """ A list of devices connected to the alarm system and their state. """
        return self.__system_devices

    def get_device_by_id(self, id):
        """ Get a device by its ID. """
        for device in self.__system_devices:
            if device.id == id:
                return device
        return None

    def disarm(self):
        """ Send Disarm command to the alarm system. """
        self.__api.disarm(self.__api.partition)

    def arm_home(self):
        """ Send Arm Home command to the alarm system. """
        self.__api.arm_home(self.__api.partition)

    def arm_away(self):
        """ Send Arm Away command to the alarm system. """
        self.__api.arm_away(self.__api.partition)

    def connect(self):
        """ Connect to the alarm system and get the static system info. """

        # Check that the server support API version 4.0 or 8.0.
        rest_versions = self.__api.get_version_info()['rest_versions']

        if '8.0' in rest_versions:
            print('Rest API version 8.0 is supported.')
        else:
            raise Exception('Rest API version 8.0 is not supported by server.')

        # Try to login and get a user token.
        self.__api.login()
        logging.debug('Login successful')

        # Try to panel login and get a session token.
        # This will raise an exception on failure.
        self.__api.panel_login()
        logging.debug('Panel Login successful')

        # Get general panel information
        gpi = self.__api.get_panel_info()
        self.__system_serial = gpi['serial']
        self.__system_model = gpi['model']

        self.update_status()

    def get_last_event(self, timestamp_hour_offset=0):
        """ Get the last event. """

        events = self.__api.get_events()

        if events is None:
            return None
        else:
            last_event = events[-1]
            data = dict()

            # Event ID
            data['event_id'] = last_event['event']

            # Determine the arm state.
            if last_event['type_id'] == 89:
                data['action'] = 'Disarm'
            elif last_event['type_id'] == 85:
                data['action'] = 'ArmHome'
            elif last_event['type_id'] == 86:
                data['action'] = 'ArmAway'
            elif last_event['type_id'] == 2:
                data['action'] = 'Alarm'
            else:
                data['action'] = 'Unknown type_id: {0}'.format(
                    str(last_event['type_id']))

            # User that caused the event
            data['user'] = last_event['appointment']

            # Event timestamp
            dt = parser.parse(last_event['datetime'])
            dt = dt + relativedelta(hours=timestamp_hour_offset)
            timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            data['timestamp'] = timestamp

            return data

    def print_system_information(self):
        """ Print system information. """

        print()
        print('---------------------------------')
        print(' Connection specific information ')
        print('---------------------------------')
        print('Host:          {0}'.format(self.__api.hostname))
        print('User Code:     {0}'.format(self.__api.user_code))
        print('App ID:       {0}'.format(self.__api.app_id))
        print('Panel ID:      {0}'.format(self.__api.panel_id))
        print('Partition:     {0}'.format(self.__api.partition))
        print('Session-Token: {0}'.format(self.__api.session_token))
        print('User-Token: {0}'.format(self.__api.user_token))
        print()
        print('----------------------------')
        print(' General system information ')
        print('----------------------------')
        print('Serial:       {0}'.format(self.__system_serial))
        print('Model:        {0}'.format(self.__system_model))
        print('Ready:        {0}'.format(self.__system_ready))
        print('State:        {0}'.format(self.__system_state))
        print('Connected:    {0}'.format(self.__system_connected))

    def print_system_devices(self, detailed=False):
        """ Print information about the devices in the alarm system. """

        for index, device in enumerate(self.__system_devices):
            print()
            print('--------------')
            print(' Device #{0} '.format(index+1))
            print('--------------')
            print('ID:             {0}'.format(device.id))
            print('Name:           {0}'.format(device.name))
            print('Zone:           {0}'.format(device.zone))
            print('Device Type:    {0}'.format(device.device_type))
            print('Subtype:        {0}'.format(device.subtype))
            print('Warnings:       {0}'.format(device.warnings))

            if detailed:
                print('Pre-enroll:     {0}'.format(device.pre_enroll))
                print('Partitions:     {0}'.format(device.partitions))
            if isinstance(device, ContactDevice):
                print('State:          {0}'.format(device.state))

    def print_events(self):
        """ Print a list of all recent events. """

        events = self.__api.get_events()

        for index, event in enumerate(events):
            print()
            print('--------------')
            print(' Event #{0} '.format(index+1))
            print('--------------')
            print('Event:         {0}'.format(event['event']))
            print('Type ID:       {0}'.format(event['type_id']))
            print('Label:         {0}'.format(event['label']))
            print('Description:   {0}'.format(event['description']))
            print('Appointment:   {0}'.format(event['appointment']))
            print('Datetime:      {0}'.format(event['datetime']))
            print('Video:         {0}'.format(event['video']))
            print('Device Type:   {0}'.format(event['device_type']))
            print('Zone:          {0}'.format(event['zone']))
            print('Partitions:    {0}'.format(event['partitions']))

    def update_status(self):
        """ Update all variables that are populated by the call
        to the status() API method. """
    
        status = self.__api.get_status()
        partition = status['partitions'][0]

        self.__system_ready = partition['ready']
        self.__system_connected = status['connected']

        alarms_events = self.__api.get_alarms()

        if alarms_events is None or len(alarms_events) == 0:
            if partition['status'] == 'EXIT' and (partition['state'] == 'AWAY' or partition['state'] == 'HOME'):
                self.__system_state = 'ARMING'
            else:
                self.__system_state = partition['state']
                self.__system_alarm = False
        else:
            state = partition['state']
            self.__system_alarm = True

            if state == 'HOME' or state == 'AWAY':
                self.__system_state = 'ALARM'
            else:
                self.__system_state = partition['state']

    def update_troubles(self):
        """ Update all variables that are populated by the call
        to the troubles() API method. """
        troubles = self.__api.get_troubles()

        self.__system_troubles = troubles

    def update_devices(self):
        """ Update all devices in the system with fresh information. """

        devices = self.__api.get_all_devices()

        # Clear the list since there is no way to uniquely identify the devices.
        self.__system_devices.clear()

        for device in devices:
            if device['subtype'] == 'CONTACT_AUX' or device['subtype'] == 'CONTACT':
                contact_device = ContactDevice(
                    id=device['id'],
                    name=device['name'],
                    zone=device['zone_type'],
                    device_type=device['device_type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    warnings=device['warnings'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(contact_device)
            elif device['subtype'] == 'MOTION_CAMERA':
                camera_device = CameraDevice(
                    id=device['id'],
                    name=device['name'],
                    zone=device['zone_type'],
                    device_type=device['device_type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    warnings=device['warnings'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(camera_device)
            elif device['subtype'] == 'MOTION' or device['subtype'] == 'CURTAIN':
                motion_device = MotionDevice(
                    id=device['id'],
                    name=device['name'],
                    zone=device['zone_type'],
                    device_type=device['device_type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    warnings=device['warnings'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(motion_device)
            elif device['subtype'] == 'SMOKE':
                smoke_device = SmokeDevice(
                    id=device['id'],
                    name=device['name'],
                    zone=device['zone_type'],
                    device_type=device['device_type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    warnings=device['warnings'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(smoke_device)
            else:
                generic_device = GenericDevice(
                    id=device['id'],
                    name=device['name'],
                    zone=device['zone_type'],
                    device_type=device['device_type'],
                    subtype=device['subtype'],
                    preenroll=device['preenroll'],
                    warnings=device['warnings'],
                    partitions=device['partitions']
                )
                self.__system_devices.append(generic_device)


class API(object):
    """ Class used for communication with the Visonic API """

    # Client configuration
    __app_type = 'com.visonic.PowerMaxApp'
    __user_agent = 'Visonic%20GO/2.8.62.91 CFNetwork/901.1 Darwin/17.6.0'
    __rest_version = '8.0'
    __hostname = 'visonic.tycomonitor.com'
    __user_code = '1234'
    __app_id = '00000000-0000-0000-0000-000000000000'
    __panel_id = '123456'
    __partition = '-1'
    __user_email = 'example@example.com'
    __user_password = 'example'

    # The Visonic API URLs used
    __url_base = None
    __url_version = None
    __url_login = None
    __url_panel_login = None
    __url_status = None
    __url_alarms = None
    __url_alerts = None
    __url_troubles = None
    __url_panel_info = None
    __url_events = None
    __url_wakeup_sms = None
    __url_all_devices = None
    __url_set_state = None
    __url_locations = None
    __url_process_status = None

    # API session token
    __session_token = None
    __user_token = None # Used in version 8.0

    # Use a session to reuse one TCP connection instead of creating a new
    # connection for every call to the API
    __session = None
    __system_devices = []

    def __init__(self, hostname, app_id, user_code, user_email, user_password, panel_id, partition):
        """ Class constructor initializes all URL variables. """

        # Set connection specific details
        self.__hostname = hostname
        self.__user_code = user_code
        self.__app_id = app_id
        self.__panel_id = panel_id
        self.__partition = partition
        self.__user_email = user_email
        self.__user_password = user_password

        # Visonic API URLs that should be used
        self.__url_base = 'https://' + self.__hostname + '/rest_api/' + \
                          self.__rest_version

        self.__url_version = 'https://' + self.__hostname + '/rest_api/version'

        self.__url_panel_login = self.__url_base + '/panel/login'
        self.__url_login = self.__url_base + '/auth'
        self.__url_status = self.__url_base + '/status'
        self.__url_alarms = self.__url_base + '/alarms'
        self.__url_alerts = self.__url_base + '/alerts'
        self.__url_troubles = self.__url_base + '/troubles'

        self.__url_panel_info = self.__url_base + '/panel_info'
        self.__url_events = self.__url_base + '/events'
        self.__url_wakeup_sms = self.__url_base + '/wakeup_sms'
        self.__url_all_devices = self.__url_base + '/devices'
        self.__url_set_state = self.__url_base + '/set_state'
        self.__url_locations = self.__url_base + '/locations'
        self.__url_process_status = self.__url_base + '/process_status'

        # Create a new session
        self.__session = requests.session()

    def __send_get_request(self, url, with_user_token, with_session_token):
        """ Send a GET request to the server. Includes the Session-Token
        only if with_session_token is True. """

        # Prepare the headers to be sent
        headers = {
            'Host': self.__hostname,
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': self.__user_agent,
            'Accept-Language': 'en-us',
            'Accept-Encoding': 'br, gzip, deflate'
        }

        # Include the session token in the header
        if with_session_token:
            headers['Session-Token'] = self.__session_token

        # Include the user token in the header
        if with_user_token:
            headers['User-Token'] = self.__user_token

        logging.debug('=== GET REQUEST -> ' + url + " ===")
        logging.debug(headers)
        logging.debug('=== END REQUEST ===')

        # Perform the request and log an exception
        # if the response is not OK (HTML 200)
        logging.debug('=== BEGIN RESPONSE ===')
        try:
            response = self.__session.get(url, headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(err)
            logging.error(response.content.decode('utf-8'))

        if response.status_code == requests.codes.ok:
            resp = json.loads(response.content.decode('utf-8'))
            logging.debug(resp)

            logging.debug('=== END RESPONSE ===')
            return resp
        else:
            logging.error(response.content.decode('utf-8'))
            logging.debug('=== END RESPONSE ===')

    def __send_post_request(self, url, data_json, with_user_token, with_session_token):
        """ Send a POST request to the server. Includes the Session-Token
        only if with_session_token is True. """

        # Prepare the headers to be sent
        headers = {
            'Host': self.__hostname,
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'User-Agent': self.__user_agent,
            'Content-Length': str(len(data_json)),
            'Accept-Language': 'en-us',
            'Accept-Encoding': 'br, gzip, deflate'
        }

        # Include the session token in the header
        if with_session_token:
            headers['Session-Token'] = self.__session_token

        # Include the user token in the header
        if with_user_token:
            headers['User-Token'] = self.__user_token

        logging.debug('=== POST REQUEST -> ' + url + " ===")
        logging.debug(headers)
        logging.debug(data_json)
        logging.debug('=== END REQUEST ===')
        
        # Perform the request and log an exception
        # if the response is not OK (HTML 200)
        logging.debug('=== BEGIN RESPONSE ===')
        try:
            response = self.__session.post(url, headers=headers, data=data_json)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.error(err)
            logging.error(response.content.decode('utf-8'))

        # Check HTTP response code
        if response.status_code == requests.codes.ok:
            resp = json.loads(response.content.decode('utf-8'))
            logging.debug(resp)
            logging.debug('=== END RESPONSE ===')
            return resp
        else:
            logging.error(response.content.decode('utf-8'))
            logging.debug('=== END RESPONSE ===')
            return None

    ######################
    # Public API methods #
    ######################

    @property
    def session_token(self):
        """ Property to keep track of the session token. """
        return self.__session_token

    @property
    def user_token(self):
        """ Property to keep track of the user token. """
        return self.__user_token

    @property
    def hostname(self):
        """ Property to keep track of the API servers hostname. """
        return self.__hostname

    @property
    def user_code(self):
        """ Property to keep track of the user code beeing used. """
        return self.__user_code

    @property
    def app_id(self):
        """ Property to keep track of the user id (UUID) beeing used. """
        return self.__app_id

    @property
    def panel_id(self):
        """ Property to keep track of the panel id (panel web name). """
        return self.__panel_id

    @property
    def partition(self):
        """ Property to keep track of the partition. """
        return self.__partition

    def get_version_info(self):
        """ Find out which REST API versions are supported. """
        return self.__send_get_request(self.__url_version,
                                       with_user_token=False,
                                       with_session_token=False)

    def login(self):
        """ Try to login and get a user token. """

        login_info = {
            'email': self.__user_email,
            'password': self.__user_password,
            'app_id': self.__app_id
        }

        login_json = json.dumps(login_info, separators=(',', ':'))
        res = self.__send_post_request(self.__url_login, login_json,
                                       with_user_token=False,
                                       with_session_token=False)

        self.__user_token = res['user_token']

    def panel_login(self):
        """ Try to panel login and get a session token. """
        
        # Setup authentication information
        panel_login_info = {
            'user_code': self.__user_code,
            'app_type': self.__app_type,
            'app_id': self.__app_id,
            'panel_serial': self.__panel_id
        }
        
        panel_login_json = json.dumps(panel_login_info, separators=(',', ':'))
        res = self.__send_post_request(self.__url_panel_login, panel_login_json,
                                        with_user_token=True,
                                        with_session_token=False)
        
        self.__session_token = res['session_token']

    def is_logged_in(self):
        """ Check if the session token is still valid. """
        try:
            self.get_status()
            return True
        except requests.HTTPError:
            return False

    def get_status(self):
        """ Get the current status of the alarm system. """
        return self.__send_get_request(self.__url_status,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_alarms(self):
        """ Get the current alarms. """

        return self.__send_get_request(self.__url_alarms,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_troubles(self):
        """ Get the current troubles. """

        return self.__send_get_request(self.__url_troubles,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_alerts(self):
        """ Get the current alerts. """

        return self.__send_get_request(self.__url_alerts,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_panel_info(self):
        """ Get the panel information. """
        return self.__send_get_request(self.__url_panel_info,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_events(self):
        """ Get the alarm panel events. """
        return self.__send_get_request(self.__url_events,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_wakeup_sms(self):
        """ Get the information needed to send a
        wakeup SMS to the alarm system. """
        return self.__send_get_request(self.__url_wakeup_sms,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_all_devices(self):
        """ Get the device specific information. """

        return self.__send_get_request(self.__url_all_devices,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_locations(self):
        """ Get all locations in the alarm system. """
        return self.__send_get_request(self.__url_locations,
                                       with_user_token=True,
                                       with_session_token=True)

    def arm_home(self, partition):
        """ Arm in Home mode and with Exit Delay. """
        arm_info = {
            'partition': -1,
            'state': "HOME"
        }
        arm_json = json.dumps(arm_info, separators=(',', ':'))

        return self.__send_post_request(self.__url_set_state, arm_json,
                                       with_user_token=True,
                                       with_session_token=True)

    def get_process_status(self, token):
        res = self.__send_get_request(self.__url_process_status + '?process_tokens=' + token,
                                       with_user_token=True,
                                       with_session_token=True)

        return res[0]

    def arm_away(self, partition):
        """ Arm in Away mode and with Exit Delay. """
        arm_info = {
            'partition': -1,
            'state': "AWAY"
        }
        arm_json = json.dumps(arm_info, separators=(',', ':'))

        return self.__send_post_request(self.__url_set_state, arm_json,
                                        with_user_token=True,
                                        with_session_token=True)

    def disarm(self, partition):
        """ Disarm the alarm system. """
        disarm_info = {
            'partition': -1,
            'state': "DISARM"
        }
        disarm_json = json.dumps(disarm_info, separators=(',', ':'))

        return self.__send_post_request(self.__url_set_state, disarm_json,
                                        with_user_token=True,
                                        with_session_token=True)