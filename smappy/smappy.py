import requests
import datetime as dt
from functools import wraps
import pytz
import numbers

__title__ = "smappy"
__version__ = "0.2.13"
__author__ = "EnergieID.be"
__license__ = "MIT"

URLS = {
    'token': 'https://app1pub.smappee.net/dev/v1/oauth2/token',
    'servicelocation': 'https://app1pub.smappee.net/dev/v1/servicelocation'
}


def authenticated(func):
    """
    Decorator to check if Smappee's access token has expired.
    If it has, use the refresh token to request a new access token
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.refresh_token is not None and \
           self.token_expiration_time <= dt.datetime.utcnow():
            self.re_authenticate()
        return func(*args, **kwargs)
    return wrapper


class Smappee(object):
    """
    Object containing Smappee's API-methods.
    See https://smappee.atlassian.net/wiki/display/DEVAPI/API+Methods
    """
    def __init__(self, client_id=None, client_secret=None):
        """
        To receive a client id and secret,
        you need to request via the Smappee support

        Parameters
        ----------
        client_id : str, optional
        client_secret : str, optional
            If None, you won't be able to do any authorisation,
            so it requires that you already have an access token somewhere.
            In that case, the SimpleSmappee class is something for you.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.refresh_token = None
        self.token_expiration_time = None

    def authenticate(self, username, password):
        """
        Uses a Smappee username and password to request an access token,
        refresh token and expiry date.

        Parameters
        ----------
        username : str
        password : str

        Returns
        -------
        requests.Response
            access token is saved in self.access_token
            refresh token is saved in self.refresh_token
            expiration time is set in self.token_expiration_time as
            datetime.datetime
        """
        url = URLS['token']
        data = {
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password
        }
        r = requests.post(url, data=data)
        r.raise_for_status()
        j = r.json()
        self.access_token = j['access_token']
        self.refresh_token = j['refresh_token']
        self._set_token_expiration_time(expires_in=j['expires_in'])
        return r

    def _set_token_expiration_time(self, expires_in):
        """
        Saves the token expiration time by adding the 'expires in' parameter
        to the current datetime (in utc).

        Parameters
        ----------
        expires_in : int
            number of seconds from the time of the request until expiration

        Returns
        -------
        nothing
            saves expiration time in self.token_expiration_time as
            datetime.datetime
        """
        self.token_expiration_time = dt.datetime.utcnow() + \
            dt.timedelta(0, expires_in)  # timedelta(days, seconds)

    def re_authenticate(self):
        """
        Uses the refresh token to request a new access token, refresh token and
        expiration date.

        Returns
        -------
        requests.Response
            access token is saved in self.access_token
            refresh token is saved in self.refresh_token
            expiration time is set in self.token_expiration_time as
            datetime.datetime
        """
        url = URLS['token']
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        r = requests.post(url, data=data)
        r.raise_for_status()
        j = r.json()
        self.access_token = j['access_token']
        self.refresh_token = j['refresh_token']
        self._set_token_expiration_time(expires_in=j['expires_in'])
        return r

    @authenticated
    def get_service_locations(self):
        """
        Request service locations

        Returns
        -------
        dict
        """
        url = URLS['servicelocation']
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json()

    @authenticated
    def get_service_location_info(self, service_location_id):
        """
        Request service location info

        Parameters
        ----------
        service_location_id : int

        Returns
        -------
        dict
        """
        url = urljoin(URLS['servicelocation'], service_location_id, "info")
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        return r.json()

    @authenticated
    def get_consumption(self, service_location_id, start, end, aggregation):
        """
        Request Elektricity consumption and Solar production
        for a given service location.

        Parameters
        ----------
        service_location_id : int
        start : int | dt.datetime | pd.Timestamp
        end : int | dt.datetime | pd.Timestamp
            start and end support epoch (in milliseconds),
            datetime and Pandas Timestamp
        aggregation : int
            1 = 5 min values (only available for the last 14 days)
            2 = hourly values
            3 = daily values
            4 = monthly values
            5 = quarterly values

        Returns
        -------
        dict
        """
        url = urljoin(URLS['servicelocation'], service_location_id,
                      "consumption")
        return self._get_consumption(url=url, start=start, end=end,
                                     aggregation=aggregation)

    @authenticated
    def get_sensor_consumption(self, service_location_id, sensor_id, start,
                               end, aggregation):
        """
        Request consumption for a given sensor in a given service location

        Parameters
        ----------
        service_location_id : int
        sensor_id : int
        start : int | dt.datetime | pd.Timestamp
        end : int | dt.datetime | pd.Timestamp
            start and end support epoch (in milliseconds),
            datetime and Pandas Timestamp
            timezone-naive datetimes are assumed to be in UTC
        aggregation : int
            1 = 5 min values (only available for the last 14 days)
            2 = hourly values
            3 = daily values
            4 = monthly values
            5 = quarterly values

        Returns
        -------
        dict
        """
        url = urljoin(URLS['servicelocation'], service_location_id, "sensor",
                      sensor_id, "consumption")
        return self._get_consumption(url=url, start=start, end=end,
                                     aggregation=aggregation)

    def _get_consumption(self, url, start, end, aggregation):
        """
        Request for both the get_consumption and
        get_sensor_consumption methods.

        Parameters
        ----------
        url : str
        start : dt.datetime
        end : dt.datetime
        aggregation : int

        Returns
        -------
        dict
        """
        start = self._to_milliseconds(start)
        end = self._to_milliseconds(end)

        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        params = {
            "aggregation": aggregation,
            "from": start,
            "to": end
        }
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json()

    @authenticated
    def get_events(self, service_location_id, appliance_id, start, end,
                   max_number=None):
        """
        Request events for a given appliance

        Parameters
        ----------
        service_location_id : int
        appliance_id : int
        start : int | dt.datetime | pd.Timestamp
        end : int | dt.datetime | pd.Timestamp
            start and end support epoch (in milliseconds),
            datetime and Pandas Timestamp
            timezone-naive datetimes are assumed to be in UTC
        max_number : int, optional
            The maximum number of events that should be returned by this query
            Default returns all events in the selected period

        Returns
        -------
        dict
        """
        start = self._to_milliseconds(start)
        end = self._to_milliseconds(end)

        url = urljoin(URLS['servicelocation'], service_location_id, "events")
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        params = {
            "from": start,
            "to": end,
            "applianceId": appliance_id,
            "maxNumber": max_number
        }
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json()

    @authenticated
    def actuator_on(self, service_location_id, actuator_id, duration=None):
        """
        Turn actuator on

        Parameters
        ----------
        service_location_id : int
        actuator_id : int
        duration : int, optional
            300,900,1800 or 3600 , specifying the time in seconds the actuator
            should be turned on. Any other value results in turning on for an
            undetermined period of time.

        Returns
        -------
        requests.Response
        """
        return self._actuator_on_off(
            on_off='on', service_location_id=service_location_id,
            actuator_id=actuator_id, duration=duration)

    @authenticated
    def actuator_off(self, service_location_id, actuator_id, duration=None):
        """
        Turn actuator off

        Parameters
        ----------
        service_location_id : int
        actuator_id : int
        duration : int, optional
            300,900,1800 or 3600 , specifying the time in seconds the actuator
            should be turned on. Any other value results in turning on for an
            undetermined period of time.

        Returns
        -------
        requests.Response
        """
        return self._actuator_on_off(
            on_off='off', service_location_id=service_location_id,
            actuator_id=actuator_id, duration=duration)

    def _actuator_on_off(self, on_off, service_location_id, actuator_id,
                         duration=None):
        """
        Turn actuator on or off

        Parameters
        ----------
        on_off : str
            'on' or 'off'
        service_location_id : int
        actuator_id : int
        duration : int, optional
            300,900,1800 or 3600 , specifying the time in seconds the actuator
            should be turned on. Any other value results in turning on for an
            undetermined period of time.

        Returns
        -------
        requests.Response
        """
        url = urljoin(URLS['servicelocation'], service_location_id,
                      "actuator", actuator_id, on_off)
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        if duration is not None:
            data = {"duration": duration}
        else:
            data = {}
        r = requests.post(url, headers=headers, json=data)
        r.raise_for_status()
        return r

    def get_consumption_dataframe(self, service_location_id, start, end,
                                  aggregation, sensor_id=None, localize=False):
        """
        Extends get_consumption() AND get_sensor_consumption(),
        parses the results in a Pandas DataFrame

        Parameters
        ----------
        service_location_id : int
        start : dt.datetime | int
        end : dt.datetime | int
            timezone-naive datetimes are assumed to be in UTC
            epoch timestamps need to be in milliseconds
        aggregation : int
        sensor_id : int, optional
            If a sensor id is passed, api method get_sensor_consumption will
            be used otherwise (by default),
            the get_consumption method will be used: this returns Electricity
            and Solar consumption and production.
        localize : bool
            default False
            default returns timestamps in UTC
            if True, timezone is fetched from service location info and
            Data Frame is localized

        Returns
        -------
        pd.DataFrame
        """
        import pandas as pd

        if sensor_id is None:
            data = self.get_consumption(
                service_location_id=service_location_id, start=start,
                end=end, aggregation=aggregation)
            consumptions = data['consumptions']
        else:
            data = self.get_sensor_consumption(
                service_location_id=service_location_id, sensor_id=sensor_id,
                start=start, end=end, aggregation=aggregation)
            # yeah please someone explain me why they had to name this
            # differently...
            consumptions = data['records']

        df = pd.DataFrame.from_dict(consumptions)
        if not df.empty:
            df.set_index('timestamp', inplace=True)
            df.index = pd.to_datetime(df.index, unit='ms', utc=True)
            if localize:
                info = self.get_service_location_info(
                    service_location_id=service_location_id)
                timezone = info['timezone']
                df = df.tz_convert(timezone)
        return df

    def _to_milliseconds(self, time):
        """
        Converts a datetime-like object to epoch, in milliseconds
        Timezone-naive datetime objects are assumed to be in UTC

        Parameters
        ----------
        time : dt.datetime | pd.Timestamp | int

        Returns
        -------
        int
            epoch milliseconds
        """
        if isinstance(time, dt.datetime):
            if time.tzinfo is None:
                time = time.replace(tzinfo=pytz.UTC)
            return int(time.timestamp() * 1e3)
        elif isinstance(time, numbers.Number):
            return time
        else:
            raise NotImplementedError("Time format not supported. Use milliseconds since epoch,\
                                        Datetime or Pandas Datetime")


class SimpleSmappee(Smappee):
    """
    Object to use if you have no client id, client secret, refresh token etc,
    for instance if everything concerning
    oAuth is handed off to a different process like a web layer.
    This object only uses a given access token.
    It has no means of refreshing it when it expires, in which case
    the requests will return errors.
    """
    def __init__(self, access_token):
        """
        Parameters
        ----------
        access_token : str
        """
        super(SimpleSmappee, self).__init__(client_id=None, client_secret=None)
        self.access_token = access_token


class LocalSmappee(object):
    """
    Access a Smappee in your local network
    """
    def __init__(self, ip):
        """
        Parameters
        ----------
        ip : str
            local IP-address of your Smappee
        """
        self.ip = ip
        self.headers = {'Content-Type': 'application/json;charset=UTF-8'}
        self.session = requests.Session()

    @property
    def base_url(self):
        url = urljoin('http://', self.ip, 'gateway', 'apipublic')
        return url

    def _basic_post(self, url, data=None):
        """
        Because basically every post request is the same

        Parameters
        ----------
        url : str
        data : str, optional

        Returns
        -------
        requests.Response
        """
        _url = urljoin(self.base_url, url)
        r = self.session.post(_url, data=data, headers=self.headers, timeout=5)
        r.raise_for_status()
        return r

    def _basic_get(self, url, params=None):
        _url = urljoin(self.base_url, url)
        r = self.session.get(_url, params=params, headers=self.headers,
                             timeout=5)
        r.raise_for_status()
        return r

    def logon(self, password='admin'):
        """
        Parameters
        ----------
        password : str
            default 'admin'

        Returns
        -------
        dict
        """
        r = self._basic_post(url='logon', data=password)
        return r.json()

    def report_instantaneous_values(self):
        """
        Returns
        -------
        dict
        """
        r = self._basic_get(url='reportInstantaneousValues')
        return r.json()

    def load_instantaneous(self):
        """
        Returns
        -------
        dict
        """
        r = self._basic_post(url='instantaneous', data="loadInstantaneous")
        return r.json()

    def active_power(self):
        """
        Takes the sum of all instantaneous active power values
        Returns them in kWh

        Returns
        -------
        float
        """
        inst = self.load_instantaneous()
        values = [float(i['value']) for i in inst if i['key'].endswith('ActivePower')]
        return sum(values) / 1000

    def active_cosfi(self):
        """
        Takes the average of all instantaneous cosfi values

        Returns
        -------
        float
        """
        inst = self.load_instantaneous()
        values = [float(i['value']) for i in inst if i['key'].endswith('Cosfi')]
        return sum(values) / len(values)

    def restart(self):
        """
        Returns
        -------
        requests.Response
        """
        return self._basic_get(url='restartSmappee?action=2')

    def reset_active_power_peaks(self):
        """
        Returns
        -------
        requests.Response
        """
        return self._basic_post(url='resetActivePowerPeaks')

    def reset_ip_scan_cache(self):
        """
        Returns
        -------
        requests.Response
        """
        return self._basic_post(url='resetIPScanCache')

    def reset_sensor_cache(self):
        """
        Returns
        -------
        requests.Response
        """
        return self._basic_post(url='resetSensorCache')

    def reset_data(self):
        """
        Returns
        -------
        requests.Response
        """
        return self._basic_post(url='clearData')

    def clear_appliances(self):
        """
        Returns
        -------
        requests.Response
        """
        return self._basic_post(url='clearAppliances')

    def load_advanced_config(self):
        """
        Returns
        -------
        dict
        """
        r = self._basic_post(url='advancedConfigPublic', data='load')
        return r.json()

    def load_config(self):
        """
        Returns
        -------
        dict
        """
        r = self._basic_post(url='configPublic', data='load')
        return r.json()

    def save_config(self, *args, **kwargs):
        """
        Parameters
        ----------
        args
        kwargs

        Raises
        ------
        NotImplementedError
        """
        raise NotImplementedError("JavaScript Code can be found on "
                                  "https://github.com/EnergyID/smappy/issues/16"
                                  ", feel free to implement it, or create an "
                                  "issue if you have need for this function")

    def load_command_control_config(self):
        """
        Returns
        -------
        dict
        """
        r = self._basic_post(url='commandControlPublic', data='load')
        return r.json()

    def send_group(self):
        """
        Returns
        -------
        requests.Response
        """
        return self._basic_post(url='commandControlPublic', data='controlGroup')

    def on_off_command_control(self, val_id):
        """
        Parameters
        ----------
        val_id : str

        Returns
        -------
        requests.Response
        """
        data = "control,controlId=" + val_id
        return self._basic_post(url='commandControlPublic', data=data)

    def add_command_control(self, *args, **kwargs):
        """
        Parameters
        ----------
        args
        kwargs

        Raises
        -------
        NotImplementedError
        """
        raise NotImplementedError("JavaScript Code can be found on "
                                  "https://github.com/EnergyID/smappy/issues/16"
                                  ", feel free to implement it, or create an "
                                  "issue if you have need for this function")

    def delete_command_control(self, val_id):
        """
        Parameters
        ----------
        val_id : str

        Returns
        -------
        requests.Response
        """

        data = "delete,controlId=" + val_id
        return self._basic_post(url='commandControlPublic', data=data)

    def delete_command_control_timers(self, val_id):
        """
        Parameters
        ----------
        val_id : str

        Returns
        -------
        requests.Response
        """
        data = "deleteTimers,controlId=" + val_id
        return self._basic_post(url='commandControlPublic', data=data)

    def add_command_control_timed(self, *args, **kwargs):
        """
        Parameters
        ----------
        args
        kwargs

        Raises
        -------
        NotImplementedError
        """
        raise NotImplementedError("JavaScript Code can be found on "
                                  "https://github.com/EnergyID/smappy/issues/16"
                                  ", feel free to implement it, or create an "
                                  "issue if you have need for this function")

    def load_logfiles(self):
        """
        Returns
        -------
        dict
        """
        r = self._basic_post(url='logBrowser', data='logFileList')
        return r.json()

    def select_logfile(self, logfile):
        """
        Parameters
        ----------
        logfile : str

        Returns
        -------
        dict
        """
        data = 'logFileSelect,' + logfile
        r = self._basic_post(url='logBrowser', data=data)
        return r.json()


def urljoin(*parts):
    """
    Join terms together with forward slashes

    Parameters
    ----------
    parts

    Returns
    -------
    str
    """
    # first strip extra forward slashes (except http:// and the likes) and
    # create list
    part_list = []
    for part in parts:
        p = str(part)
        if p.endswith('//'):
            p = p[0:-1]
        else:
            p = p.strip('/')
        part_list.append(p)
    # join everything together
    url = '/'.join(part_list)
    return url
