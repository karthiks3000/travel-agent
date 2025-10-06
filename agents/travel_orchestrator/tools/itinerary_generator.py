"""
Day-by-day itinerary generation engine for comprehensive travel planning
"""
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, time, timedelta
from dataclasses import dataclass, field

from common.models.itinerary_models import (
    TravelItinerary, DailyItinerary, ItineraryActivity, TimeSlot, ActivityType,
    TransportationActivity, GeneralActivity, AttractionResult
)
from common.models.flight_models import FlightResult
from common.models.accommodation_models import PropertyResult
from common.models.food_models import RestaurantResult
from common.models.orchestrator_models import TravelOrchestratorResponse, ResponseType, ResponseStatus

logger = logging.getLogger(__name__)

@dataclass
class TripComponents:
    """Container for all trip components used in itinerary generation"""
    flights: List[FlightResult] = field(default_factory=list)
    accommodations: List[PropertyResult] = field(default_factory=list)
    restaurants: List[RestaurantResult] = field(default_factory=list)
    attractions: List[AttractionResult] = field(default_factory=list)

def generate_comprehensive_itinerary(
    destination: str,
    origin: str,
    start_date: date,
    end_date: date,
    traveler_count: int,
    trip_components: TripComponents,
    preferences: Optional[Dict[str, Any]] = None
) -> TravelOrchestratorResponse:
    """
    Generate a comprehensive day-by-day travel itinerary
    
    Args:
        destination: Primary destination city
        origin: Departure city
        start_date: Trip start date
        end_date: Trip end date  
        traveler_count: Number of travelers
        trip_components: Available flights, accommodations, restaurants, attractions
        preferences: Optional user preferences (budget, pace, interests)
    
    Returns:
        TravelOrchestratorResponse with complete itinerary
    """
    start_time = datetime.now()
    
    try:
        # Calculate trip duration
        total_days = (end_date - start_date).days + 1
        
        # Generate trip title
        trip_title = f"{total_days}-Day {destination} Adventure"
        
        # Create base itinerary structure
        itinerary = TravelItinerary(
            trip_title=trip_title,
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            traveler_count=traveler_count,
            trip_summary=f"A {total_days}-day journey from {origin} to {destination} with carefully planned activities, dining, and accommodations.",
            total_estimated_cost=None,
            packing_suggestions=None,
            travel_tips=None
        )
        
        # Generate daily itineraries
        daily_itineraries = []
        current_date = start_date
        
        for day_num in range(1, total_days + 1):
            daily_itinerary = _generate_daily_itinerary(
                day_number=day_num,
                date=current_date,
                destination=destination,
                origin=origin,
                total_days=total_days,
                trip_components=trip_components,
                preferences=preferences
            )
            daily_itineraries.append(daily_itinerary)
            current_date += timedelta(days=1)
        
        itinerary.daily_itineraries = daily_itineraries
        
        # Calculate total estimated cost
        total_cost = _calculate_total_trip_cost(itinerary, trip_components)
        itinerary.total_estimated_cost = total_cost
        
        # Generate packing suggestions and travel tips
        itinerary.packing_suggestions = _generate_packing_suggestions(destination, total_days, current_date.month)
        itinerary.travel_tips = _generate_travel_tips(destination, trip_components)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.ITINERARY,
            response_status=ResponseStatus.COMPLETE_SUCCESS,
            message=f"Created your complete {total_days}-day {destination} itinerary with {sum(len(day.activities) for day in daily_itineraries)} planned activities.",
            overall_progress_message="Complete travel itinerary generated successfully",
            is_final_response=True,
            itinerary=itinerary,
            estimated_costs={
                "total_trip": total_cost,
                "per_person": total_cost / traveler_count if traveler_count > 0 else total_cost,
                "per_day": total_cost / total_days if total_days > 0 else total_cost
            },
            processing_time_seconds=processing_time,
            success=True,
            error_message=None,
            next_expected_input_friendly=None,
            flight_results=None,
            accommodation_results=None,
            restaurant_results=None,
            attraction_results=None,
            legacy_flight_results=None,
            legacy_accommodation_results=None,
            recommendations=None,
            session_metadata=None
        )
        
    except Exception as e:
        logger.error(f"Itinerary generation failed: {e}")
        
        return TravelOrchestratorResponse(
            response_type=ResponseType.CONVERSATION,
            response_status=ResponseStatus.SYSTEM_ERROR,
            message="I encountered an error while creating your itinerary. Please try again with your travel details.",
            overall_progress_message="Itinerary generation failed",
            is_final_response=True,
            success=False,
            error_message=str(e),
            processing_time_seconds=(datetime.now() - start_time).total_seconds(),
            next_expected_input_friendly=None,
            flight_results=None,
            accommodation_results=None,
            restaurant_results=None,
            attraction_results=None,
            itinerary=None,
            legacy_flight_results=None,
            legacy_accommodation_results=None,
            estimated_costs=None,
            recommendations=None,
            session_metadata=None
        )


def _generate_daily_itinerary(
    day_number: int,
    date: date,
    destination: str,
    origin: str,
    total_days: int,
    trip_components: TripComponents,
    preferences: Optional[Dict[str, Any]] = None
) -> DailyItinerary:
    """Generate activities for a single day"""
    
    activities = []
    daily_cost = 0.0
    
    # Day 1: Arrival day
    if day_number == 1:
        activities, daily_cost = _plan_arrival_day(
            date, destination, origin, trip_components
        )
        daily_summary = f"Arrival day in {destination} - getting settled and initial exploration"
    
    # Last day: Departure day
    elif day_number == total_days:
        activities, daily_cost = _plan_departure_day(
            date, destination, origin, trip_components
        )
        daily_summary = f"Final day in {destination} - last activities and departure"
    
    # Middle days: Full exploration days
    else:
        activities, daily_cost = _plan_full_exploration_day(
            date, destination, day_number, trip_components, preferences
        )
        daily_summary = f"Full day exploring {destination} - attractions, dining, and local experiences"
    
    return DailyItinerary(
        day_number=day_number,
        date=date,
        location=destination,
        daily_summary=daily_summary,
        activities=activities,
        estimated_daily_cost=daily_cost,
        weather_info=None
    )


def _plan_arrival_day(
    date: date,
    destination: str,
    origin: str,
    trip_components: TripComponents
) -> Tuple[List[ItineraryActivity], float]:
    """Plan activities for arrival day"""
    activities = []
    total_cost = 0.0
    
    # Morning: Flight arrival
    if trip_components.flights:
        outbound_flight = trip_components.flights[0]  # Use first flight as outbound
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(8, 0), end_time=time(10, 30), duration_minutes=150),
            activity_type=ActivityType.FLIGHT,
            title=f"Arrive in {destination}",
            activity_details=outbound_flight,
            notes="Allow extra time for customs and baggage claim"
        ))
        total_cost += outbound_flight.price if outbound_flight.price else 500
    
    # Late Morning: Transportation to accommodation
    activities.append(ItineraryActivity(
        time_slot=TimeSlot(start_time=time(11, 0), end_time=time(11, 45), duration_minutes=45),
        activity_type=ActivityType.TRANSPORTATION,
        title="Transfer to accommodation",
        activity_details=TransportationActivity(
            mode="taxi",
            from_location=f"{destination} Airport",
            to_location="Hotel/Accommodation",
            provider=None,
            cost_estimate=50.0,
            notes="Pre-book transfer or use ride-sharing app"
        ),
        notes="Allow extra time for airport delays"
    ))
    total_cost += 50.0
    
    # Afternoon: Check-in and local lunch
    if trip_components.accommodations:
        accommodation = trip_components.accommodations[0]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(12, 0), end_time=time(13, 0), duration_minutes=60),
            activity_type=ActivityType.ACCOMMODATION,
            title="Check-in to accommodation",
            activity_details=accommodation,
            notes="Drop off luggage and freshen up"
        ))
    
    # Lunch: Local restaurant
    if trip_components.restaurants:
        lunch_restaurant = trip_components.restaurants[0]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(13, 30), end_time=time(15, 0), duration_minutes=90),
            activity_type=ActivityType.RESTAURANT,
            title=f"Lunch at {lunch_restaurant.name}",
            activity_details=lunch_restaurant,
            notes="Welcome meal to get oriented with local cuisine"
        ))
        total_cost += 35.0  # Estimated lunch cost per person
    
    # Afternoon: Light exploration or rest
    activities.append(ItineraryActivity(
        time_slot=TimeSlot(start_time=time(15, 30), end_time=time(17, 30), duration_minutes=120),
        activity_type=ActivityType.GENERAL,
        title="Initial neighborhood exploration",
        activity_details=GeneralActivity(
            title="Walk around accommodation area",
            description="Get oriented with the neighborhood, find essentials",
            location=f"Near accommodation in {destination}",
            cost_estimate=0.0,
            notes="Light activity to combat jet lag"
        ),
        notes="Good for getting oriented and combating jet lag"
    ))
    
    # Evening: Dinner
    if len(trip_components.restaurants) > 1:
        dinner_restaurant = trip_components.restaurants[1]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(19, 0), end_time=time(21, 0), duration_minutes=120),
            activity_type=ActivityType.RESTAURANT,
            title=f"Dinner at {dinner_restaurant.name}",
            activity_details=dinner_restaurant,
            notes="First proper meal in the destination"
        ))
        total_cost += 60.0  # Estimated dinner cost per person
    
    return activities, total_cost


def _plan_departure_day(
    date: date,
    destination: str,
    origin: str,
    trip_components: TripComponents
) -> Tuple[List[ItineraryActivity], float]:
    """Plan activities for departure day"""
    activities = []
    total_cost = 0.0
    
    # Morning: Check-out and final activity
    if trip_components.accommodations:
        accommodation = trip_components.accommodations[0]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(10, 0), end_time=time(10, 30), duration_minutes=30),
            activity_type=ActivityType.ACCOMMODATION,
            title="Check-out",
            activity_details=accommodation,
            notes="Store luggage if departure is later"
        ))
    
    # Late Morning: Final attraction or shopping
    if trip_components.attractions:
        # Choose a quick attraction for final visit
        final_attraction = trip_components.attractions[-1]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(11, 0), end_time=time(12, 30), duration_minutes=90),
            activity_type=ActivityType.ATTRACTION,
            title=f"Final visit to {final_attraction.name}",
            activity_details=final_attraction,
            notes="Last chance to see this attraction"
        ))
    
    # Lunch: Final meal
    if trip_components.restaurants:
        final_restaurant = trip_components.restaurants[-1]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(13, 0), end_time=time(14, 30), duration_minutes=90),
            activity_type=ActivityType.RESTAURANT,
            title=f"Farewell lunch at {final_restaurant.name}",
            activity_details=final_restaurant,
            notes="Last taste of local cuisine"
        ))
        total_cost += 40.0
    
    # Afternoon: Transportation to airport
    activities.append(ItineraryActivity(
        time_slot=TimeSlot(start_time=time(15, 0), end_time=time(16, 0), duration_minutes=60),
        activity_type=ActivityType.TRANSPORTATION,
        title="Transfer to airport",
        activity_details=TransportationActivity(
            mode="taxi",
            from_location="Accommodation/City Center",
            to_location=f"{destination} Airport",
            provider=None,
            cost_estimate=50.0,
            notes="Allow extra time for traffic and check-in"
        ),
        notes="Final journey - ensure you have all luggage"
    ))
    total_cost += 50.0
    
    # Evening: Departure flight
    if len(trip_components.flights) > 1:
        return_flight = trip_components.flights[1]  # Return flight
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(18, 0), end_time=time(22, 0), duration_minutes=240),
            activity_type=ActivityType.FLIGHT,
            title=f"Departure to {origin}",
            activity_details=return_flight,
            notes="End of your wonderful journey"
        ))
    
    return activities, total_cost


def _plan_full_exploration_day(
    date: date,
    destination: str,
    day_number: int,
    trip_components: TripComponents,
    preferences: Optional[Dict[str, Any]] = None
) -> Tuple[List[ItineraryActivity], float]:
    """Plan a full day of exploration activities"""
    activities = []
    total_cost = 0.0
    
    # Morning: Major attraction
    if trip_components.attractions and len(trip_components.attractions) >= day_number - 1:
        morning_attraction = trip_components.attractions[min(day_number - 2, len(trip_components.attractions) - 1)]
        duration = morning_attraction.visit_duration_estimate or 120
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(9, 0), end_time=time(11, 0), duration_minutes=duration),
            activity_type=ActivityType.ATTRACTION,
            title=f"Visit {morning_attraction.name}",
            activity_details=morning_attraction,
            notes="Start early to avoid crowds"
        ))
        # Estimate attraction cost based on price level
        attraction_cost = _estimate_attraction_cost(morning_attraction.price_level)
        total_cost += attraction_cost
    
    # Lunch: Local restaurant
    restaurant_index = min((day_number - 1) * 2, len(trip_components.restaurants) - 1) if trip_components.restaurants else 0
    if trip_components.restaurants and restaurant_index < len(trip_components.restaurants):
        lunch_restaurant = trip_components.restaurants[restaurant_index]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(12, 30), end_time=time(14, 0), duration_minutes=90),
            activity_type=ActivityType.RESTAURANT,
            title=f"Lunch at {lunch_restaurant.name}",
            activity_details=lunch_restaurant,
            notes="Midday break with local flavors"
        ))
        total_cost += 35.0
    
    # Afternoon: Second attraction or activity
    if len(trip_components.attractions) > 1:
        afternoon_attraction_index = min((day_number - 1) + 1, len(trip_components.attractions) - 1)
        if afternoon_attraction_index < len(trip_components.attractions):
            afternoon_attraction = trip_components.attractions[afternoon_attraction_index]
            duration = afternoon_attraction.visit_duration_estimate or 90
            activities.append(ItineraryActivity(
                time_slot=TimeSlot(start_time=time(14, 30), end_time=time(16, 0), duration_minutes=duration),
                activity_type=ActivityType.ATTRACTION,
                title=f"Explore {afternoon_attraction.name}",
                activity_details=afternoon_attraction,
                notes="Afternoon cultural exploration"
            ))
            total_cost += _estimate_attraction_cost(afternoon_attraction.price_level)
    
    # Late Afternoon: Free time or transportation
    activities.append(ItineraryActivity(
        time_slot=TimeSlot(start_time=time(16, 30), end_time=time(17, 30), duration_minutes=60),
        activity_type=ActivityType.GENERAL,
        title="Free time and local exploration",
        activity_details=GeneralActivity(
            title="Wander and discover",
            description="Explore local neighborhoods, shop for souvenirs, or relax",
            location=f"{destination} city center",
            cost_estimate=20.0,
            notes="Personal time to explore at your own pace"
        ),
        notes="Perfect time to discover local gems"
    ))
    total_cost += 20.0
    
    # Dinner: Evening dining
    dinner_index = min((day_number - 1) * 2 + 1, len(trip_components.restaurants) - 1) if trip_components.restaurants else 0
    if trip_components.restaurants and dinner_index < len(trip_components.restaurants):
        dinner_restaurant = trip_components.restaurants[dinner_index]
        activities.append(ItineraryActivity(
            time_slot=TimeSlot(start_time=time(19, 0), end_time=time(21, 0), duration_minutes=120),
            activity_type=ActivityType.RESTAURANT,
            title=f"Dinner at {dinner_restaurant.name}",
            activity_details=dinner_restaurant,
            notes="Evening dining experience"
        ))
        total_cost += 65.0
    
    return activities, total_cost


def _calculate_total_trip_cost(itinerary: TravelItinerary, trip_components: TripComponents) -> float:
    """Calculate estimated total cost for the entire trip"""
    total_cost = 0.0
    
    # Add daily costs
    for day in itinerary.daily_itineraries:
        if day.estimated_daily_cost:
            total_cost += day.estimated_daily_cost
    
    # Add accommodation costs (per night)
    if trip_components.accommodations:
        accommodation = trip_components.accommodations[0]
        nights = itinerary.total_days - 1  # Usually one less night than days
        if hasattr(accommodation, 'price_per_night') and accommodation.price_per_night:
            total_cost += accommodation.price_per_night * nights
        elif hasattr(accommodation, 'total_price') and accommodation.total_price:
            total_cost += accommodation.total_price
        else:
            # Estimate accommodation cost
            total_cost += 150 * nights  # $150 per night estimate
    
    return round(total_cost, 2)


def _estimate_attraction_cost(price_level: Optional[int]) -> float:
    """Estimate attraction cost based on Google Places price level"""
    if price_level is None:
        return 15.0  # Default estimate
    
    price_mapping = {
        0: 0.0,     # Free
        1: 10.0,    # Inexpensive
        2: 20.0,    # Moderate
        3: 35.0,    # Expensive
        4: 50.0     # Very expensive
    }
    
    return price_mapping.get(price_level, 15.0)


def _generate_packing_suggestions(destination: str, total_days: int, month: int) -> List[str]:
    """Generate packing suggestions based on destination and season"""
    suggestions = [
        "Comfortable walking shoes",
        "Weather-appropriate clothing",
        "Travel documents and copies",
        "Phone charger and adapter",
        "Camera or smartphone for photos"
    ]
    
    # Season-based suggestions
    if month in [12, 1, 2]:  # Winter
        suggestions.extend([
            "Warm jacket or coat",
            "Gloves and hat",
            "Layers for varying temperatures"
        ])
    elif month in [6, 7, 8]:  # Summer
        suggestions.extend([
            "Sunscreen and sunglasses",
            "Light, breathable clothing",
            "Hat for sun protection"
        ])
    
    # Duration-based suggestions
    if total_days > 7:
        suggestions.append("Laundry supplies or laundry service plan")
    
    if total_days < 4:
        suggestions.append("Pack light - carry-on only if possible")
    
    return suggestions


def _generate_travel_tips(destination: str, trip_components: TripComponents) -> List[str]:
    """Generate helpful travel tips"""
    tips = [
        "Check visa requirements and passport validity",
        "Notify bank of travel plans to avoid card blocks",
        "Download offline maps and translation apps",
        "Research local customs and tipping practices",
        "Keep emergency contacts and embassy information handy"
    ]
    
    if trip_components.restaurants:
        tips.append("Make restaurant reservations in advance for popular venues")
    
    if trip_components.attractions:
        tips.append("Book attraction tickets online to skip lines and save money")
    
    tips.extend([
        "Carry a portable phone charger",
        "Learn basic phrases in the local language",
        "Have a backup payment method (cash, different card)",
        "Take photos of important documents and store them securely online"
    ])
    
    return tips
