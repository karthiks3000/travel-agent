/**
 * ResultsPanel component - Dynamic results display
 * Requirements: 4.4, 8.4
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardContent, CardTitle } from '@/components/ui/card';
import { useChatResults } from '@/stores/chatStore';
import { BarChart3, Plane, Building, UtensilsCrossed, MapPin, AlertCircle } from 'lucide-react';
import type { ResultData } from '@/types/chat';

interface ResultsPanelProps {
  className?: string;
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({ className }) => {
  const { currentResults, resultType } = useChatResults();

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'flights':
        return <Plane className="w-5 h-5" />;
      case 'accommodations':
        return <Building className="w-5 h-5" />;
      case 'restaurants':
        return <UtensilsCrossed className="w-5 h-5" />;
      case 'itinerary':
        return <MapPin className="w-5 h-5" />;
      default:
        return <BarChart3 className="w-5 h-5" />;
    }
  };

  const getResultTitle = (type: string) => {
    switch (type) {
      case 'flights':
        return 'Flight Results';
      case 'accommodations':
        return 'Accommodation Results';
      case 'restaurants':
        return 'Restaurant Results';
      case 'itinerary':
        return 'Trip Itinerary';
      default:
        return 'Results';
    }
  };

  // No results state
  if (!currentResults || !resultType) {
    return (
      <div className={cn("flex flex-col h-full", className)}>
        {/* Header */}
        <Card className="rounded-none border-0 border-b">
          <CardHeader className="pb-3">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-full">
                <BarChart3 className="w-5 h-5 text-gray-600" />
              </div>
              <div>
                <CardTitle className="text-lg">Results</CardTitle>
                <p className="text-sm text-gray-500">Search results will appear here</p>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Empty state */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <BarChart3 className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No Results Yet
            </h3>
            <p className="text-gray-600 mb-4">
              Start a conversation with the travel assistant to see search results, recommendations, and trip details here.
            </p>
            <div className="text-sm text-gray-500">
              <p className="mb-2">Results will include:</p>
              <ul className="space-y-1">
                <li className="flex items-center justify-center">
                  <Plane className="w-4 h-4 mr-2" />
                  Flight options and prices
                </li>
                <li className="flex items-center justify-center">
                  <Building className="w-4 h-4 mr-2" />
                  Hotels and accommodations
                </li>
                <li className="flex items-center justify-center">
                  <UtensilsCrossed className="w-4 h-4 mr-2" />
                  Restaurant recommendations
                </li>
                <li className="flex items-center justify-center">
                  <MapPin className="w-4 h-4 mr-2" />
                  Complete trip itineraries
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <Card className="rounded-none border-0 border-b">
        <CardHeader className="pb-3">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full">
              {getResultIcon(resultType)}
            </div>
            <div className="flex-1">
              <CardTitle className="text-lg">{getResultTitle(resultType)}</CardTitle>
              <p className="text-sm text-gray-500">
                Updated {new Date(currentResults.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Results Content */}
      <div className="flex-1 overflow-auto p-4">
        <ResultsContent results={currentResults} />
      </div>
    </div>
  );
};

// Results content component
interface ResultsContentProps {
  results: ResultData;
}

const ResultsContent: React.FC<ResultsContentProps> = ({ results }) => {
  switch (results.type) {
    case 'flights':
      return <FlightResultsContent results={results} />;
    case 'accommodations':
      return <AccommodationResultsContent results={results} />;
    case 'restaurants':
      return <RestaurantResultsContent results={results} />;
    case 'itinerary':
      return <ItineraryResultsContent results={results} />;
    default:
      return <GenericResultsContent results={results} />;
  }
};

// Placeholder components for different result types
const FlightResultsContent: React.FC<{ results: any }> = ({ results }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center space-x-2 mb-4">
        <Plane className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold">Flight Search Results</h3>
      </div>
      <p className="text-gray-600 mb-4">{results.recommendation}</p>
      
      {results.best_outbound_flight && (
        <div className="space-y-3">
          <h4 className="font-medium">Best Outbound Flight</h4>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><strong>Airline:</strong> {results.best_outbound_flight.airline}</div>
              <div><strong>Price:</strong> ${results.best_outbound_flight.price}</div>
              <div><strong>Departure:</strong> {results.best_outbound_flight.departure_time}</div>
              <div><strong>Arrival:</strong> {results.best_outbound_flight.arrival_time}</div>
              <div><strong>Duration:</strong> {results.best_outbound_flight.duration}</div>
              <div><strong>Stops:</strong> {results.best_outbound_flight.stops}</div>
            </div>
          </div>
        </div>
      )}
      
      {results.best_return_flight && (
        <div className="space-y-3 mt-4">
          <h4 className="font-medium">Best Return Flight</h4>
          <div className="bg-gray-50 p-3 rounded-lg">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><strong>Airline:</strong> {results.best_return_flight.airline}</div>
              <div><strong>Price:</strong> ${results.best_return_flight.price}</div>
              <div><strong>Departure:</strong> {results.best_return_flight.departure_time}</div>
              <div><strong>Arrival:</strong> {results.best_return_flight.arrival_time}</div>
              <div><strong>Duration:</strong> {results.best_return_flight.duration}</div>
              <div><strong>Stops:</strong> {results.best_return_flight.stops}</div>
            </div>
          </div>
        </div>
      )}
    </CardContent>
  </Card>
);

const AccommodationResultsContent: React.FC<{ results: any }> = ({ results }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center space-x-2 mb-4">
        <Building className="w-5 h-5 text-green-600" />
        <h3 className="font-semibold">Accommodation Results</h3>
      </div>
      <p className="text-gray-600 mb-4">{results.recommendation}</p>
      
      {results.best_accommodations && results.best_accommodations.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium">Recommended Properties</h4>
          {results.best_accommodations.slice(0, 3).map((property: any, index: number) => (
            <div key={index} className="bg-gray-50 p-3 rounded-lg">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><strong>Title:</strong> {property.title || 'N/A'}</div>
                <div><strong>Price:</strong> ${property.price_per_night || 'N/A'}/night</div>
                <div><strong>Rating:</strong> {property.rating || 'N/A'}</div>
                <div><strong>Platform:</strong> {property.platform}</div>
                <div className="col-span-2"><strong>Location:</strong> {property.location || 'N/A'}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </CardContent>
  </Card>
);

const RestaurantResultsContent: React.FC<{ results: any }> = ({ results }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center space-x-2 mb-4">
        <UtensilsCrossed className="w-5 h-5 text-orange-600" />
        <h3 className="font-semibold">Restaurant Results</h3>
      </div>
      <p className="text-gray-600 mb-4">{results.recommendation}</p>
      
      {results.restaurants && results.restaurants.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-medium">Recommended Restaurants</h4>
          {results.restaurants.slice(0, 3).map((restaurant: any, index: number) => (
            <div key={index} className="bg-gray-50 p-3 rounded-lg">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><strong>Name:</strong> {restaurant.name}</div>
                <div><strong>Rating:</strong> {restaurant.rating || 'N/A'}</div>
                <div><strong>Price Level:</strong> {restaurant.price_level || 'N/A'}</div>
                <div><strong>Open Now:</strong> {restaurant.is_open_now ? 'Yes' : 'No'}</div>
                <div className="col-span-2"><strong>Address:</strong> {restaurant.address}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </CardContent>
  </Card>
);

const ItineraryResultsContent: React.FC<{ results: any }> = ({ results }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center space-x-2 mb-4">
        <MapPin className="w-5 h-5 text-purple-600" />
        <h3 className="font-semibold">Trip Itinerary</h3>
      </div>
      
      <div className="space-y-3">
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div><strong>Destination:</strong> {results.destination}</div>
          <div><strong>Travelers:</strong> {results.travelers}</div>
          <div><strong>Start Date:</strong> {results.startDate}</div>
          <div><strong>End Date:</strong> {results.endDate}</div>
        </div>
        
        {results.items && results.items.length > 0 && (
          <div className="mt-4">
            <h4 className="font-medium mb-3">Itinerary Items</h4>
            <div className="space-y-2">
              {results.items.map((item: any, index: number) => (
                <div key={index} className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                      {item.type}
                    </span>
                    <span className="text-sm font-medium">{item.title}</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <div><strong>Date:</strong> {item.date} {item.time && `at ${item.time}`}</div>
                    <div><strong>Description:</strong> {item.description}</div>
                    {item.location && <div><strong>Location:</strong> {item.location}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </CardContent>
  </Card>
);

const GenericResultsContent: React.FC<{ results: any }> = ({ results }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center space-x-2 mb-4">
        <AlertCircle className="w-5 h-5 text-gray-600" />
        <h3 className="font-semibold">Results</h3>
      </div>
      <p className="text-gray-600">{results.recommendation || 'Results received from travel assistant.'}</p>
      
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <pre className="text-xs text-gray-700 whitespace-pre-wrap">
          {JSON.stringify(results, null, 2)}
        </pre>
      </div>
    </CardContent>
  </Card>
);
