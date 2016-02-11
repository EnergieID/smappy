# Smappy
API wrapper for Smappee

See https://smappee.atlassian.net/wiki/display/DEVAPI/API+Methods

## Create a new connection by supplying your Smappee client id and secret
`s = smappy.Smappee(client_id='<your client id>', client_secret='<your client secret>')`

## Authenticate using a Smappee username and password
`s.authenticate(username='<your username>', password='<your password>')`

Re-authentication using the refresh token is done automatically when the authorization token has expired.

## API Requests
4 API requests are supported. The methods return the parsed JSON response as a dict.

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

## Consumption as Pandas DataFrame
`s.get_consumption_dataframe(service_location_id, start, end, aggregation, localize)`

Same usage as `get_consumption`, but returns a Pandas DataFrame. Use the localize flag to get localized timestamps.

# Future
Future development may include:

'Authorization key only'-mode. For when you don't have direct access to user names passwords or even client id and secret.
When the python part of your code is running as a job in the back-end for example.

Request error catching and handling.