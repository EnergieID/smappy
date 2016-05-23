import requests
import datetime as dt
import pandas as pd

__title__ = "smappy"
__version__ = "0.2.0"
__author__ = "EnergieID.be"
__license__ = "MIT"

URLS = {
    'token': 'https://app1pub.smappee.net/dev/v1/oauth2/token',
    'servicelocation': 'https://app1pub.smappee.net/dev/v1/servicelocation'
}


def authenticated(func):
    """
    Decorator to check if Smappee's access token has expired. If it has, use the refresh token to request a new
    access token
    """
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.refresh_token is not None and self.token_expiration_time <= dt.datetime.utcnow():
            self.re_authenticate()
        return func(*args, **kwargs)
    return wrapper


class Smappee(object):
    """
    Object containing Smappee's API-methods.
    See https://smappee.atlassian.net/wiki/display/DEVAPI/API+Methods
    """
    def __init__(self, client_id, client_secret):
        """
        To receive a client id and secret, you need to request via the Smappee support

        Parameters
        ----------
        client_id : str or None
        client_secret : str or None
            If None, you won't be able to do any authorisation, so it requires that you already have an access token
            somewhere. In that case, the SimpleSmappee class is something for you.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.refresh_token = None
        self.token_expiration_time = None

    def authenticate(self, username, password):
        """
        Uses a Smappee username and password to request an access token, refresh token and expiry date

        Parameters
        ----------
        username : str
        password : str

        Returns
        -------
        nothing
            access token is saved in self.access_token
            refresh token is saved in self.refresh_token
            expiration time is set in self.token_expiration_time as datetime.datetime
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
        if r.status_code != 200:
            raise requests.HTTPError(r.status_code, url, data)
        j = r.json()
        self.access_token = j['access_token']
        self.refresh_token = j['refresh_token']
        self._set_token_expiration_time(expires_in=j['expires_in'])

    def _set_token_expiration_time(self, expires_in):
        """
        Saves the token expiration time by adding the 'expires in' parameter to the current datetime (in utc)

        Parameters
        ----------
        expires_in : int
            number of seconds from the time of the request until expiration

        Returns
        -------
        nothing
            saves expiration time in self.token_expiration_time as datetime.datetime
        """
        self.token_expiration_time = dt.datetime.utcnow() + dt.timedelta(0, expires_in)  # timedelta(days, seconds)

    def re_authenticate(self):
        """
        Uses the refresh token to request a new access token, refresh token and expiration date

        Returns
        -------
        nothing
            access token is saved in self.access_token
            refresh token is saved in self.refresh_token
            expiration time is set in self.token_expiration_time as datetime.datetime
        """
        url = URLS['token']
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        r = requests.post(url, data=data)
        if r.status_code != 200:
            raise requests.HTTPError(r.status_code, url, data)
        j = r.json()
        self.access_token = j['access_token']
        self.refresh_token = j['refresh_token']
        self._set_token_expiration_time(expires_in=j['expires_in'])

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
        if r.status_code != 200:
            raise requests.HTTPError(r.status_code, url, headers)
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
        url = URLS['servicelocation'] + "/{}/info".format(service_location_id)
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        r = requests.get(url, headers=headers)
        if r.status_code != 200:
            raise requests.HTTPError(r.status_code, url, headers)
        return r.json()

    @authenticated
    def get_consumption(self, service_location_id, start, end, aggregation):
        """
        Request Elektricity consumption and Solar production for a given service location

        Parameters
        ----------
        service_location_id : int
        start : datetime-like object (supports epoch, datetime and Pandas Timestamp)
        end : datetime-like object (supports epoch, datetime and Pandas Timestamp)
        aggregation : int (1 to 5)
            1 = 5 min values (only available for the last 14 days)
            2 = hourly values
            3 = daily values
            4 = monthly values
            5 = quarterly values

        Returns
        -------
        dict
        """
        url = URLS['servicelocation'] + "/{}/consumption".format(service_location_id)
        return self._get_consumption(url=url, start=start, end=end, aggregation=aggregation)

    @authenticated
    def get_sensor_consumption(self, service_location_id, sensor_id, start, end, aggregation):
        """
        Request consumption for a given sensor in a given service location

        Parameters
        ----------
        service_location_id : int
        sensor_id : int
        start : datetime-like object (supports epoch, datetime and Pandas Timestamp)
        end : datetime-like object (supports epoch, datetime and Pandas Timestamp)
        aggregation : int (1 to 5)
            1 = 5 min values (only available for the last 14 days)
            2 = hourly values
            3 = daily values
            4 = monthly values
            5 = quarterly values

        Returns
        -------
        dict
        """
        url = URLS['servicelocation'] + "/{}/sensor/{}/consumption".format(service_location_id, sensor_id)
        return self._get_consumption(url=url, start=start, end=end, aggregation=aggregation)

    def _get_consumption(self, url, start, end, aggregation):
        """
        Request for both the get_consumption and get_sensor_consumption methods.

        Parameters
        ----------
        url : str
        start : datetime
        end : datetime
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
        if r.status_code != 200:
            raise requests.HTTPError(r.status_code, url, headers, params)
        return r.json()

    @authenticated
    def get_events(self, service_location_id, appliance_id, start, end, max_number=None):
        """
        Request events for a given appliance

        Parameters
        ----------
        service_location_id : int
        appliance_id : int
        start : datetime-like object (supports epoch, datetime and Pandas Timestamp)
        end : datetime-like object (supports epoch, datetime and Pandas Timestamp)
        max_number : int (optional)
            The maximum number of events that should be returned by this query
            Default returns all events in the selected period

        Returns
        -------
        dict
        """
        start = self._to_milliseconds(start)
        end = self._to_milliseconds(end)

        url = URLS['servicelocation'] + "/{}/events".format(service_location_id)
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        params = {
            "from": start,
            "to": end,
            "applianceId": appliance_id,
            "maxNumber": max_number
        }
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            raise requests.HTTPError(r.status_code, url, headers, params)
        return r.json()

    @authenticated
    def actuator_on(self, service_location_id, actuator_id, duration=None):
        """
        NOT TESTED
        Turn actuator on

        Parameters
        ----------
        service_location_id : int
        actuator_id : int
        duration : int
            300,900,1800 or 3600 , specifying the time in seconds the actuator
            should be turned on. Any other value results in turning on for an
            undetermined period of time.

        Returns
        -------
        Nothing
        """
        return self._actuator_on_off(on_off='on', service_location_id=service_location_id, actuator_id=actuator_id,
                                     duration=duration)

    @authenticated
    def actuator_off(self, service_location_id, actuator_id, duration=None):
        """
        NOT TESTED
        Turn actuator off

        Parameters
        ----------
        service_location_id : int
        actuator_id : int
        duration : int
            300,900,1800 or 3600 , specifying the time in seconds the actuator
            should be turned on. Any other value results in turning on for an
            undetermined period of time.

        Returns
        -------
        Nothing
        """
        return self._actuator_on_off(on_off='off', service_location_id=service_location_id, actuator_id=actuator_id,
                                     duration=duration)

    def _actuator_on_off(self, on_off, service_location_id, actuator_id, duration=None):
        """
            NOT TESTED
            Turn actuator on or off

            Parameters
            ----------
            on_off : str
                'on' or 'off'
            service_location_id : int
            actuator_id : int
            duration : int
                300,900,1800 or 3600 , specifying the time in seconds the actuator
                should be turned on. Any other value results in turning on for an
                undetermined period of time.

            Returns
            -------
            Nothing
            """
        url = URLS['servicelocation'] + "/{}/actuator/{}/{}".format(service_location_id, actuator_id, on_off)
        headers = {"Authorization": "Bearer {}".format(self.access_token)}
        data = {"duration": duration}
        r = requests.post(url, headers=headers, data=data)
        if r.status_code != 200:
            raise requests.HTTPError(r.status_code, url, headers, data)
        return

    def get_consumption_dataframe(self, service_location_id, start, end, aggregation, sensor_id=None, localize=False):
        """
        Extends get_consumption() AND get_sensor_consumption(), parses the results in a Pandas DataFrame

        Parameters
        ----------
        service_location_id : int
        start : datetime
        end : datetime
        aggregation : int (1 to 5)
        sensor_id : int (optional)
            If a sensor id is passed, api method get_sensor_consumption will be used
            otherwise (by default), the get_consumption method will be used: this returns Electricity and Solar
            consumption and production.
        localize : bool (optional, default False)
            default returns timestamps in UTC
            if True, timezone is fetched from service location info and Data Frame is localized

        Returns
        -------
        Pandas DataFrame
        """
        if sensor_id is None:
            data = self.get_consumption(service_location_id=service_location_id, start=start, end=end,
                                        aggregation=aggregation)
            consumptions = data['consumptions']
        else:
            data = self.get_sensor_consumption(service_location_id=service_location_id, sensor_id=sensor_id,
                                               start=start, end=end, aggregation=aggregation)
            consumptions = data['records']  # yeah please someone explain me why they had to name this differently...

        df = pd.DataFrame.from_dict(consumptions)
        if not df.empty:
            df.set_index('timestamp', inplace=True)
            df.index = pd.to_datetime(df.index, unit='ms', utc=True)
            if localize:
                info = self.get_service_location_info(service_location_id=service_location_id)
                timezone = info['timezone']
                df = df.tz_convert(timezone)
        return df

    def _to_milliseconds(self, time):
        """
        Converts a datetime-like object to epoch, in milliseconds

        Parameters
        ----------
        time : datetime-like object (works with datetime and Pandas Timestamp)

        Returns
        -------
        int (epoch)
        """
        if isinstance(time, dt.datetime):
            return int(time.timestamp() * 1e3)
        elif isinstance(time, int):
            return time
        else:
            raise NotImplementedError("Time format not supported. Use epochs, Datetime or Pandas Datetime")


class SimpleSmappee(Smappee):
    """
    Object to use if you have no client id, client secret, refresh token etc, for instance if everything concerning
    oAuth is handed off to a different process like a web layer.
    This object only uses a given access token. It has no means of refreshing it when it expires, in which case
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
