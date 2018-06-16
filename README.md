# Smappy
Wrapper for the Smappee API
See https://smappee.atlassian.net/wiki/display/DEVAPI/API+Methods

Local interface to read and control your Smappee over LAN

# Installation
Via pip:

- Mac & Linux: `python3 -m pip install smappy` or `python -m pip install smappy`
- Windows: `python.exe -m pip install smappy`

Via git: `git clone https://github.com/EnergieID/smappy.git`

# API Client Usage

## Create a new client by supplying your Smappee client id and secret
`s = smappy.Smappee(client_id, client_secret)`

## Authenticate using a Smappee username and password
`s.authenticate(username, password)`

Re-authentication using the refresh token is done automatically when the access token has expired.

## API Requests
7 API requests are supported. The methods return the parsed JSON response as a dict.

### Get Service Locations
`s.get_service_locations()` 

### Get Service Location Info
`s.get_service_location_info(service_location_id)`

### Get Consumption
- `s.get_consumption(service_location_id, start, end, aggregation)`
- `s.get_sensor_consumption(service_location_id, sensor_id, start, end, aggregation)`

Start & End accept epoch (in milliseconds), datetime and pandas timestamps

Aggregation: 1 = 5 min values (only available for the last 14 days), 2 = hourly values, 3 = daily values, 4 = monthly values, 5 = quarterly values

### Get Events
`s.get_events(service_location_id, appliance_id, start, end, max_number)`

### Actuators

- `s.actuator_on(self, service_location_id, actuator_id, duration)`
- `s.actuator_off(self, service_location_id, actuator_id, duration)`

duration = 300,900,1800 or 3600 - specifying the time in seconds the actuator
should be turned on or off. Any other value results in turning on or off for an
undetermined period of time.

## Consumption as Pandas DataFrame
Get consumption values in a Pandas Data Frame

- To get total Electricity consumption and Solar production, use:
`s.get_consumption_dataframe(service_location_id, start, end, aggregation, localize)`
-  To get consumption for a specific sensor, include a sensor id:
`s.get_consumption_dataframe(service_location_id, start, end, aggregation, localize, sensor_id)`

Use the localize flag to get localized timestamps.

# Simple Smappee
If you have no client id, client secret, refresh token etc, for instance if everything concerning oAuth is handed off
to a different process like a web layer. This object only uses a given access token. It has no means of refreshing it
when it expires, in which case the requests will raise errors.

`ss = SimpleSmappee(access_token)`

It has the same methods as the normal Smappee class, except authorization and re-authorization will not work.

# LAN Smappee Client

## Create Client

`ls = smappy.LocalSmappee(ip='192.168.0.50')  # fill in local IP-address of your Smappee`

## Log on

`ls.logon(password='admin')  # default password is admin`

## Other methods
- `report_instantaneous_values()`
- `load_instantaneous()`
- `active_power()`
- `active_cosfi()`
- `restart()`
- `reset_active_power_peaks()`
- `lreset_ip_scan_cache()`
- `reset_sensor_cache()`
- `reset_data()`
- `clear_appliances()`
- `load_advanced_config()`
- `load_config()`
- `save_config()`
- `load_command_control_config()`
- `send_group()`
- `on_command_control(val_id)`
- `off_command_control(val_id)`
- `delete_command_control(val_id)`
- `delete_command_control_timers(val_id)`
- `add_command_control_timed()`
- `load_logfiles()`
- `select_logfile(logfile)`
