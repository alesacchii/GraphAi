from typing import Literal
from typing_extensions import TypedDict
from datetime import date, time

class FlightData(TypedDict):
    """
    This class is used to define the state of the flight data.
    {
        "Flight Number": "",
        "Departure Airport": "",
        "Arrival Airport": "",
        "Departure Date": "",
        "Departure Time": "",
        "Arrival Date": "",
        "Arrival Time": "",
        "Passengers Name": []
    }
    """

    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_date: date
    departure_time: time
    arrival_date: date
    arrival_time: time
    passengers_name: list[str]

class EmailState(TypedDict):
    '''
    This class is used to define the state of the email graph.
    {
        "document_category": "",  # One of: "Confirmation", "Cancellation", "Schedule Change", "Not Useful"
        "pnr": "",  # Booking Number
        "flights": [FlightData]  # List of FlightData
    }
    '''
    file_path: str # Path al file .eml da elaborare
    raw_email: str
    image_path: str #La mail verrà convertita in Immagine per mantenere le formattazioni Originali
    validator_check: bool # Flag per indicare se il documento è valido

    document_category: Literal["Confirmation", "Cancellation", "Schedule Change", "Not Useful"]
    pnr: str
    flights: list[FlightData]
