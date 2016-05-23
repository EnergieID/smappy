# Smappy
API wrapper for Smappee

See https://smappee.atlassian.net/wiki/display/DEVAPI/API+Methods

## Create a new connection by supplying your Smappee client id and secret
`s = smappy.Smappee(client_id, client_secret)`

## Authenticate using a Smappee username and password
`s.authenticate(username, password)`

Re-authentication using the refresh token is done automatically when the access token has expired.

## API Requests
6 API requests are supported. The methods return the parsed JSON response as a dict.

### Get Service Locations
`s.get_service_locations()` 

### Get Service Location Info
`s.get_service_location_info(service_location_id)`

### Get Consumption
`s.get_consumption(service_location_id, start, end, aggregation)`

Start & End accept epoch (in milliseconds), datetime and pandas timestamps

Aggregation: 1 = 5 min values (only available for the last 14 days), 2 = hourly values, 3 = daily values, 4 = monthly values, 5 = quarterly values

### Get Events
`s.get_events(service_location_id, appliance_id, start, end, max_number)`

### Actuators
NOTE: These methods are untested, so please provide feeback if you are using them, successfully or otherwise.
`s.actuator_on(self, service_location_id, actuator_id, duration)`
`s.actuator_off(self, service_location_id, actuator_id, duration)`

duration = 300,900,1800 or 3600 , specifying the time in seconds the actuator
should be turned on or off. Any other value results in turning on or off for an
undetermined period of time.

## Consumption as Pandas DataFrame
`s.get_consumption_dataframe(service_location_id, start, end, aggregation, localize)`

Same usage as `get_consumption`, but returns a Pandas DataFrame. Use the localize flag to get localized timestamps.

# Simple Smappee
If you have no client id, client secret, refresh token etc, for instance if everything concerning oAuth is handed off
to a different process like a web layer. This object only uses a given access token. It has no means of refreshing it
when it expires, in which case the requests will raise errors.

`ss = SimpleSmappee(access_token)`

It has the same methods as the normal Smappee class, except authorization and re-authorization will not work.

# Future
Future development may include:

Request error catching and handling.

Implementation of the actuator methods