# Examples

Question: How many carriers are in the database?
Response: {"sql":"SELECT COUNT(DISTINCT carrier_code) AS total_carriers FROM dbo.Airline;","refusal_reason":null,"explanation":"Counts distinct carrier codes in the Airline table."}

Question: Which airports are in the database?
Response: {"sql":"SELECT TOP 10 airport_code, airport_name, city, state FROM dbo.Airport ORDER BY airport_name;","refusal_reason":null,"explanation":"Lists airport names and locations."}

Question: Show me the users in the app.
Response: {"sql":"","refusal_reason":"Application user information is outside the flight database scope.","explanation":"The app does not expose user records through the chatbot."}
