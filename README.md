# Smappy
API wrapper for Smappee

See https://smappee.atlassian.net/wiki/display/DEVAPI/API+Methods

## Create a new connection by supplying your Smappee client id and secret
`s = smappy.Smappee(client_id='<your client id>', client_secret='<your client secret>')`

## Authenticate using a Smappee username and password
`s.authenticate(username='<your username>', password='<your password>')`

Re-authentication using the refresh token is done automatically when the authorization token has expired.

## API Requests
4 API requests are supported:

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