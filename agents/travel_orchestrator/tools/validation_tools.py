"""
Validation tools for travel information completeness
"""
from datetime import date, datetime
from typing import Dict, List

from agents.models.travel_models import TravelInformation, ValidationResult
from agents.models.base_models import TripType


def validate_travel_requirements(travel_info: TravelInformation) -> ValidationResult:
    """
    Validate completeness of travel information for specialist agent calls
    
    Args:
        travel_info: Structured travel information using TravelInformation model
        
    Returns:
        ValidationResult with detailed validation analysis
    """
    
    result = ValidationResult()
    
    # Flight validation logic
    flight_missing = []
    if not travel_info.origin:
        flight_missing.append("origin")
    if not travel_info.destination:
        flight_missing.append("destination") 
    if not travel_info.departure_date:
        flight_missing.append("departure_date")
    if not travel_info.passengers:
        flight_missing.append("passengers")
    
    # Check trip type requirements
    if travel_info.trip_type == TripType.ROUND_TRIP and not travel_info.return_date:
        flight_missing.append("return_date")
    elif not travel_info.trip_type and travel_info.return_date:
        # If return date provided but no trip type, infer round trip
        travel_info.trip_type = TripType.ROUND_TRIP
    elif not travel_info.trip_type:
        # Default to one-way if no return date
        travel_info.trip_type = TripType.ONE_WAY
    
    result.missing_info["flights"] = flight_missing
    result.can_search["flights"] = len(flight_missing) == 0
    
    # Accommodation validation logic
    accommodation_missing = []
    if not travel_info.destination:
        accommodation_missing.append("destination")
    if not travel_info.check_in:
        accommodation_missing.append("check_in")
    if not travel_info.check_out:
        accommodation_missing.append("check_out")
    if not travel_info.guests:
        accommodation_missing.append("guests")
    
    result.missing_info["accommodations"] = accommodation_missing
    result.can_search["accommodations"] = len(accommodation_missing) == 0
    
    # Restaurant validation (minimal requirements)
    if travel_info.destination:
        result.can_search["restaurants"] = True
    else:
        result.missing_info["restaurants"] = ["destination"]
    
    # Generate contextual questions
    result.next_questions = _generate_questions(result.missing_info, travel_info)
    
    # Calculate completeness score
    total_core_fields = 8  # Core required fields
    complete_fields = sum([
        bool(travel_info.origin),
        bool(travel_info.destination), 
        bool(travel_info.departure_date),
        bool(travel_info.passengers),
        bool(travel_info.check_in),
        bool(travel_info.check_out),
        bool(travel_info.guests),
        bool(travel_info.trip_type)
    ])
    result.completeness_score = complete_fields / total_core_fields
    
    # Identify ready agents
    result.ready_agents = [agent for agent, ready in result.can_search.items() if ready]
    
    # Generate validation summary
    result.validation_summary = _generate_validation_summary(result, travel_info)
    
    return result


def _generate_questions(missing_info: Dict[str, List[str]], travel_info: TravelInformation) -> List[str]:
    """Generate contextual questions based on missing information"""
    questions = []
    
    # Prioritize flight questions first (most critical)
    if "origin" in missing_info.get("flights", []):
        questions.append("What city or airport will you be departing from?")
    
    if "destination" in missing_info.get("flights", []) and not travel_info.destination:
        questions.append("What's your destination city?")
    
    if "departure_date" in missing_info.get("flights", []):
        questions.append("What's your preferred departure date?")
    
    if "passengers" in missing_info.get("flights", []):
        questions.append("How many passengers will be flying?")
    
    if "return_date" in missing_info.get("flights", []):
        questions.append("What's your return date? (Leave blank for one-way trip)")
    
    # Accommodation questions
    if "check_in" in missing_info.get("accommodations", []):
        if travel_info.departure_date:
            questions.append(f"When would you like to check into your accommodation? (You're departing {travel_info.departure_date})")
        else:
            questions.append("When would you like to check into your accommodation?")
    
    if "check_out" in missing_info.get("accommodations", []):
        if travel_info.return_date:
            questions.append(f"When will you be checking out? (Your return flight is {travel_info.return_date})")
        else:
            questions.append("When will you be checking out?")
    
    if "guests" in missing_info.get("accommodations", []):
        if travel_info.passengers:
            questions.append(f"How many guests need accommodation? (Same as {travel_info.passengers} passengers?)")
        else:
            questions.append("How many guests need accommodation?")
    
    return questions


def _generate_validation_summary(result: ValidationResult, travel_info: TravelInformation) -> str:
    """Generate a human-readable validation summary"""
    summary_parts = []
    
    # Basic trip info
    if travel_info.destination and travel_info.origin:
        summary_parts.append(f"Trip: {travel_info.origin} → {travel_info.destination}")
    elif travel_info.destination:
        summary_parts.append(f"Destination: {travel_info.destination}")
    
    # Completeness
    percentage = int(result.completeness_score * 100)
    summary_parts.append(f"Information: {percentage}% complete")
    
    # Ready agents
    if result.ready_agents:
        summary_parts.append(f"Ready to search: {', '.join(result.ready_agents)}")
    
    # Missing critical info
    total_missing = sum(len(missing) for missing in result.missing_info.values())
    if total_missing > 0:
        summary_parts.append(f"Missing {total_missing} required details")
    
    return " | ".join(summary_parts)


def validate_dates(travel_info: TravelInformation) -> List[str]:
    """
    Validate that all dates are in the future or today
    
    Returns:
        List of validation error messages (empty if all dates are valid)
    """
    errors = []
    today = date.today()
    
    # Check departure date
    if travel_info.departure_date and travel_info.departure_date < today:
        errors.append(f"Departure date ({travel_info.departure_date}) cannot be in the past. Today is {today}.")
    
    # Check return date
    if travel_info.return_date and travel_info.return_date < today:
        errors.append(f"Return date ({travel_info.return_date}) cannot be in the past. Today is {today}.")
    
    # Check check-in date
    if travel_info.check_in and travel_info.check_in < today:
        errors.append(f"Check-in date ({travel_info.check_in}) cannot be in the past. Today is {today}.")
    
    # Check check-out date
    if travel_info.check_out and travel_info.check_out < today:
        errors.append(f"Check-out date ({travel_info.check_out}) cannot be in the past. Today is {today}.")
    
    return errors


def infer_missing_dates(travel_info: TravelInformation) -> TravelInformation:
    """
    Intelligently infer missing dates based on provided information
    
    Args:
        travel_info: Travel information with some dates potentially missing
        
    Returns:
        Travel information with inferred dates filled in where possible
    """
    # If departure date is provided but no check-in, assume same day check-in
    if travel_info.departure_date and not travel_info.check_in:
        travel_info.check_in = travel_info.departure_date
    
    # If return date is provided but no check-out, assume same day check-out
    if travel_info.return_date and not travel_info.check_out:
        travel_info.check_out = travel_info.return_date
    
    # If check-in is provided but no departure date, assume departure same day
    if travel_info.check_in and not travel_info.departure_date:
        travel_info.departure_date = travel_info.check_in
    
    # If check-out is provided but no return date for round trip, assume return same day
    if travel_info.check_out and not travel_info.return_date and travel_info.trip_type == TripType.ROUND_TRIP:
        travel_info.return_date = travel_info.check_out
    
    # If passengers are provided but no guests, assume same number
    if travel_info.passengers and not travel_info.guests:
        travel_info.guests = travel_info.passengers
    
    # If guests are provided but no passengers, assume same number
    if travel_info.guests and not travel_info.passengers:
        travel_info.passengers = travel_info.guests
    
    return travel_info
