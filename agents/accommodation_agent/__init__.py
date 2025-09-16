"""
Accommodation Agent - Nova Act Implementation

A multi-platform accommodation search agent using Nova Act browser automation 
to search Airbnb and Booking.com.
"""

__version__ = "0.1.0"
__author__ = "Travel Agent Team"

from .accommodation_agent import AccommodationAgent
from common.models.accommodation_models import PropertyResult, AccommodationAgentResponse

__all__ = [
    "AccommodationAgent",
    "PropertyResult", 
    "AccommodationAgentResponse"
]
