import type { 
  FlightResult, 
  PropertyResult, 
  RestaurantResult, 
  AttractionResult 
} from '../../types/chat';
import { Card, CardContent, CardDescription, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { 
  PlaneIcon, 
  BuildingIcon, 
  UtensilsIcon, 
  MapPinIcon,
  StarIcon,
  ClockIcon,
  DollarSignIcon,
  ExternalLinkIcon
} from 'lucide-react';

// Flight Options Component
interface FlightOptionsProps {
  flights: FlightResult[];
  onSelectFlight?: (flight: FlightResult) => void;
  showMultiple?: boolean;
}

export function FlightOptions({ flights, onSelectFlight, showMultiple = true }: FlightOptionsProps) {
  const displayFlights = showMultiple ? flights : flights.slice(0, 1);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <PlaneIcon className="h-5 w-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Flight Options</h3>
        <span className="text-sm text-muted-foreground">({flights.length} found)</span>
      </div>
      
      <div className="grid gap-3">
        {displayFlights.map((flight, idx) => (
          <Card key={idx} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-center">
                    <div className="font-semibold">{flight.departure_time}</div>
                    <div className="text-xs text-muted-foreground">{flight.departure_airport}</div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <PlaneIcon className="h-4 w-4 text-muted-foreground" />
                    <div className="text-xs">
                      <div>{flight.duration}</div>
                      <div className="text-muted-foreground">
                        {flight.stops === 0 ? 'Non-stop' : `${flight.stops} stop${flight.stops > 1 ? 's' : ''}`}
                      </div>
                    </div>
                  </div>
                  
                  <div className="text-center">
                    <div className="font-semibold">{flight.arrival_time}</div>
                    <div className="text-xs text-muted-foreground">{flight.arrival_airport}</div>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-xl font-bold text-blue-600">${flight.price}</div>
                  <div className="text-xs text-muted-foreground">{flight.airline}</div>
                  <div className="text-xs text-muted-foreground">{flight.booking_class}</div>
                </div>
                
                {onSelectFlight && (
                  <Button
                    size="sm"
                    onClick={() => onSelectFlight(flight)}
                    className="ml-4"
                  >
                    Select
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Accommodation Options Component
interface AccommodationOptionsProps {
  accommodations: PropertyResult[];
  onSelectAccommodation?: (accommodation: PropertyResult) => void;
  showMultiple?: boolean;
}

export function AccommodationOptions({ accommodations, onSelectAccommodation, showMultiple = true }: AccommodationOptionsProps) {
  const displayAccommodations = showMultiple ? accommodations : accommodations.slice(0, 1);

  const formatPrice = (accommodation: PropertyResult) => {
    if (accommodation.price_per_night) {
      return `$${accommodation.price_per_night}/night`;
    } else if (accommodation.total_price) {
      return `$${accommodation.total_price} total`;
    }
    return 'Price on request';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <BuildingIcon className="h-5 w-5 text-green-600" />
        <h3 className="text-lg font-semibold">Accommodation Options</h3>
        <span className="text-sm text-muted-foreground">({accommodations.length} found)</span>
      </div>
      
      <div className="grid gap-3">
        {displayAccommodations.map((accommodation, idx) => (
          <Card key={idx} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex gap-4 flex-1">
                  {accommodation.image_url && (
                    <img
                      src={accommodation.image_url}
                      alt={accommodation.title}
                      className="w-24 h-24 object-cover rounded-md"
                    />
                  )}
                  
                  <div className="flex-1">
                    <CardTitle className="text-base">{accommodation.title}</CardTitle>
                    <CardDescription className="text-sm">{accommodation.location}</CardDescription>
                    
                    <div className="flex items-center gap-2 mt-2">
                      {accommodation.rating && (
                        <div className="flex items-center gap-1">
                          <StarIcon className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                          <span className="text-sm">{accommodation.rating}</span>
                          {accommodation.review_count && (
                            <span className="text-xs text-muted-foreground">({accommodation.review_count})</span>
                          )}
                        </div>
                      )}
                      
                      <span className="text-xs text-muted-foreground">•</span>
                      <span className="text-xs">{accommodation.property_type}</span>
                      
                      {accommodation.guests_capacity && (
                        <>
                          <span className="text-xs text-muted-foreground">•</span>
                          <span className="text-xs">{accommodation.guests_capacity} guests</span>
                        </>
                      )}
                    </div>
                    
                    {accommodation.amenities && accommodation.amenities.length > 0 && (
                      <div className="mt-2 text-xs text-muted-foreground">
                        {accommodation.amenities.slice(0, 3).join(', ')}
                        {accommodation.amenities.length > 3 && ` +${accommodation.amenities.length - 3} more`}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="text-right ml-4">
                  <div className="text-lg font-bold text-green-600">
                    {formatPrice(accommodation)}
                  </div>
                  <div className="text-xs text-muted-foreground capitalize">
                    {accommodation.platform}
                  </div>
                  
                  <div className="flex gap-2 mt-2">
                    {accommodation.url && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(accommodation.url, '_blank')}
                      >
                        <ExternalLinkIcon className="h-3 w-3 mr-1" />
                        View
                      </Button>
                    )}
                    
                    {onSelectAccommodation && (
                      <Button
                        size="sm"
                        onClick={() => onSelectAccommodation(accommodation)}
                      >
                        Select
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Restaurant Options Component
interface RestaurantOptionsProps {
  restaurants: RestaurantResult[];
  onSelectRestaurant?: (restaurant: RestaurantResult) => void;
  showMultiple?: boolean;
}

export function RestaurantOptions({ restaurants, onSelectRestaurant, showMultiple = true }: RestaurantOptionsProps) {
  const displayRestaurants = showMultiple ? restaurants : restaurants.slice(0, 1);

  const formatPriceLevel = (priceLevel?: string) => {
    const levelMap = {
      'PRICE_LEVEL_FREE': 'Free',
      'PRICE_LEVEL_INEXPENSIVE': '$',
      'PRICE_LEVEL_MODERATE': '$$',
      'PRICE_LEVEL_EXPENSIVE': '$$$',
      'PRICE_LEVEL_VERY_EXPENSIVE': '$$$$'
    };
    return priceLevel ? levelMap[priceLevel as keyof typeof levelMap] || '?' : '?';
  };

  const getCuisineFromTypes = (types: string[]) => {
    const cuisineTypes = types.filter(type => 
      type.includes('restaurant') && type !== 'restaurant'
    );
    return cuisineTypes[0]?.replace('_restaurant', '').replace('_', ' ') || 'Restaurant';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <UtensilsIcon className="h-5 w-5 text-orange-600" />
        <h3 className="text-lg font-semibold">Restaurant Options</h3>
        <span className="text-sm text-muted-foreground">({restaurants.length} found)</span>
      </div>
      
      <div className="grid gap-3">
        {displayRestaurants.map((restaurant, idx) => (
          <Card key={idx} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-base">{restaurant.name}</CardTitle>
                  <CardDescription className="text-sm">{restaurant.address}</CardDescription>
                  
                  <div className="flex items-center gap-4 mt-2">
                    {restaurant.rating && (
                      <div className="flex items-center gap-1">
                        <StarIcon className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="text-sm">{restaurant.rating}</span>
                        {restaurant.user_rating_count && (
                          <span className="text-xs text-muted-foreground">({restaurant.user_rating_count})</span>
                        )}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-1">
                      <DollarSignIcon className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{formatPriceLevel(restaurant.price_level)}</span>
                    </div>
                    
                    <span className="text-sm capitalize">{getCuisineFromTypes(restaurant.types)}</span>
                    
                    {restaurant.is_open_now !== undefined && (
                      <div className={`text-xs px-2 py-1 rounded ${restaurant.is_open_now ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                        {restaurant.is_open_now ? 'Open Now' : 'Closed'}
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex gap-2 ml-4">
                  {restaurant.website_uri && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => window.open(restaurant.website_uri, '_blank')}
                    >
                      <ExternalLinkIcon className="h-3 w-3 mr-1" />
                      Website
                    </Button>
                  )}
                  
                  {onSelectRestaurant && (
                    <Button
                      size="sm"
                      onClick={() => onSelectRestaurant(restaurant)}
                    >
                      Select
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Attraction Options Component
interface AttractionOptionsProps {
  attractions: AttractionResult[];
  onSelectAttraction?: (attraction: AttractionResult) => void;
  showMultiple?: boolean;
}

export function AttractionOptions({ attractions, onSelectAttraction, showMultiple = true }: AttractionOptionsProps) {
  const displayAttractions = showMultiple ? attractions : attractions.slice(0, 1);

  const formatPriceLevel = (priceLevel?: number) => {
    if (priceLevel === undefined) return '?';
    const levels = ['Free', '$', '$$', '$$$', '$$$$'];
    return levels[priceLevel] || '?';
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'TBD';
    if (minutes < 60) return `${minutes}min`;
    const hours = Math.floor(minutes / 60);
    const remainingMin = minutes % 60;
    return remainingMin > 0 ? `${hours}h ${remainingMin}min` : `${hours}h`;
  };

  const getAttractionType = (types: string[]) => {
    const attractionTypes = types.filter(type => 
      !['establishment', 'point_of_interest'].includes(type)
    );
    return attractionTypes[0]?.replace('_', ' ') || 'Attraction';
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <MapPinIcon className="h-5 w-5 text-purple-600" />
        <h3 className="text-lg font-semibold">Attraction Options</h3>
        <span className="text-sm text-muted-foreground">({attractions.length} found)</span>
      </div>
      
      <div className="grid gap-3">
        {displayAttractions.map((attraction, idx) => (
          <Card key={idx} className="hover:shadow-md transition-shadow">
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-base">{attraction.name}</CardTitle>
                  <CardDescription className="text-sm">{attraction.formatted_address}</CardDescription>
                  
                  <div className="flex items-center gap-4 mt-2">
                    {attraction.rating && (
                      <div className="flex items-center gap-1">
                        <StarIcon className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                        <span className="text-sm">{attraction.rating}</span>
                        {attraction.user_ratings_total && (
                          <span className="text-xs text-muted-foreground">({attraction.user_ratings_total.toLocaleString()})</span>
                        )}
                      </div>
                    )}
                    
                    <div className="flex items-center gap-1">
                      <DollarSignIcon className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm">{formatPriceLevel(attraction.price_level)}</span>
                    </div>
                    
                    {attraction.visit_duration_estimate && (
                      <div className="flex items-center gap-1">
                        <ClockIcon className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm">{formatDuration(attraction.visit_duration_estimate)}</span>
                      </div>
                    )}
                    
                    <span className="text-sm capitalize">{getAttractionType(attraction.types)}</span>
                  </div>
                  
                  {attraction.opening_hours && 'open_now' in attraction.opening_hours && (
                    <div className={`inline-block text-xs px-2 py-1 rounded mt-2 ${
                      attraction.opening_hours.open_now ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {attraction.opening_hours.open_now ? 'Open Now' : 'Closed'}
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 ml-4">
                  {attraction.website && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => window.open(attraction.website, '_blank')}
                    >
                      <ExternalLinkIcon className="h-3 w-3 mr-1" />
                      Website
                    </Button>
                  )}
                  
                  {onSelectAttraction && (
                    <Button
                      size="sm"
                      onClick={() => onSelectAttraction(attraction)}
                    >
                      Select
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// Combined Results Component for Mixed Responses
interface MixedResultsProps {
  flightResults?: FlightResult[];
  accommodationResults?: PropertyResult[];
  restaurantResults?: RestaurantResult[];
  attractionResults?: AttractionResult[];
  onSelectFlight?: (flight: FlightResult) => void;
  onSelectAccommodation?: (accommodation: PropertyResult) => void;
  onSelectRestaurant?: (restaurant: RestaurantResult) => void;
  onSelectAttraction?: (attraction: AttractionResult) => void;
}

export function MixedResults({ 
  flightResults, 
  accommodationResults, 
  restaurantResults, 
  attractionResults,
  onSelectFlight,
  onSelectAccommodation,
  onSelectRestaurant,
  onSelectAttraction
}: MixedResultsProps) {
  return (
    <div className="space-y-8">
      {flightResults && flightResults.length > 0 && (
        <FlightOptions 
          flights={flightResults} 
          onSelectFlight={onSelectFlight}
          showMultiple={true}
        />
      )}
      
      {accommodationResults && accommodationResults.length > 0 && (
        <AccommodationOptions 
          accommodations={accommodationResults}
          onSelectAccommodation={onSelectAccommodation}
          showMultiple={true}
        />
      )}
      
      {restaurantResults && restaurantResults.length > 0 && (
        <RestaurantOptions 
          restaurants={restaurantResults}
          onSelectRestaurant={onSelectRestaurant}
          showMultiple={true}
        />
      )}
      
      {attractionResults && attractionResults.length > 0 && (
        <AttractionOptions 
          attractions={attractionResults}
          onSelectAttraction={onSelectAttraction}
          showMultiple={true}
        />
      )}
    </div>
  );
}

export default MixedResults;
