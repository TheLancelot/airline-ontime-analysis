# Schema Metadata

Allowed tables:
- dbo.Airline (carrier_code, airline_name)
- dbo.Airport (airport_code, airport_name, city, state)
- dbo.FlightInstance (carrier_code, flight_date, flight_number, origin_airport_code, destination_airport_code, departure_delay_minutes, arrival_delay_minutes, scheduled_elapsed_minutes, actual_elapsed_minutes)

Business rules:
- Only the 11 busiest US origin airports are present in the sample, but destination airports may be any airport in the Airport table.
- Delay values can be negative (early) or NULL.
- There are no cancellation or diversion fields.
- Output should be a read-only SELECT only.
