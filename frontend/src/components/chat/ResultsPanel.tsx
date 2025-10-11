/**
 * ResultsPanel component - Dynamic results display
 * Requirements: 4.4, 8.4
 */

import React from 'react';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { useChatResults } from '@/stores/chatStore';
import { BarChart3, Plane, Building, UtensilsCrossed, MapPin, AlertCircle, ExternalLink, Camera } from 'lucide-react';
import type { ResultData, FlightSearchResults, AccommodationSearchResults, TravelItinerary, RestaurantResult, AttractionResult } from '@/types/chat';
import { FlightOptions, AccommodationOptions } from '@/components/travel/ComponentResults';
import { ItineraryTimeline } from '@/components/travel/ItineraryTimeline';

interface ResultsPanelProps {
  className?: string;
}

// Utility function to generate Google Maps URL from place_id
const getGoogleMapsUrl = (placeId: string): string => {
  return `https://www.google.com/maps/place/?q=place_id:${placeId}`;
};

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
      case 'attractions':
        return <Camera className="w-5 h-5" />;
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
      case 'attractions':
        return 'Attraction Results';
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
        <div className="border-b border-gray-200 bg-white flex-shrink-0">
          <div className="px-4 py-4">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-gray-100 rounded-full">
                <BarChart3 className="w-5 h-5 text-gray-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900">Results</h3>
                <p className="text-sm text-gray-500">Search results will appear here</p>
              </div>
            </div>
          </div>
        </div>

        {/* Empty state */}
        <div className="flex-1 flex items-center justify-center p-8 overflow-auto">
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
                  <Camera className="w-4 h-4 mr-2" />
                  Tourist attractions
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
      <div className="border-b border-gray-200 bg-white flex-shrink-0">
        <div className="px-4 py-4">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full">
              {getResultIcon(resultType)}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900">{getResultTitle(resultType)}</h3>
              <p className="text-sm text-gray-500">
                Updated {new Date(currentResults.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Results Content */}
      <div className="flex-1 min-h-0 overflow-auto p-4">
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
      return <FlightResultsContent results={results as FlightSearchResults} />;
    case 'accommodations':
      return <AccommodationResultsContent results={results as AccommodationSearchResults} />;
    case 'restaurants':
      return <RestaurantResultsContent results={results} />;
    case 'attractions':
      return <AttractionResultsContent results={results} />;
    case 'itinerary':
      return <ItineraryResultsContent results={results} />;
    default:
      return <GenericResultsContent results={results} />;
  }
};

// Flight results component using FlightOptions
const FlightResultsContent: React.FC<{ results: FlightSearchResults }> = ({ results }) => {
  if (!results.flights || results.flights.length === 0) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-gray-600">No flight results available.</p>
        </CardContent>
      </Card>
    );
  }

  return <FlightOptions flights={results.flights} showMultiple={true} />;
};

// Accommodation results component using AccommodationOptions
const AccommodationResultsContent: React.FC<{ results: AccommodationSearchResults }> = ({ results }) => {
  if (!results.best_accommodations || results.best_accommodations.length === 0) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-gray-600">No accommodation results available.</p>
        </CardContent>
      </Card>
    );
  }

  return <AccommodationOptions accommodations={results.best_accommodations} showMultiple={true} />;
};

// Attraction results component
const AttractionResultsContent: React.FC<{ results: ResultData }> = ({ results }) => {
  // Type guard for attraction results
  if (!('attractions' in results)) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-gray-600">No attraction results available.</p>
        </CardContent>
      </Card>
    );
  }

  const attractionResults = results as { attractions: AttractionResult[]; recommendation?: string };
  
  return (
    <Card>
      <CardContent className="p-4">
        {attractionResults.recommendation && (
          <p className="text-gray-600 mb-4">{attractionResults.recommendation}</p>
        )}
        
        {attractionResults.attractions && attractionResults.attractions.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium">Popular Attractions</h4>
            {attractionResults.attractions.slice(0, 5).map((attraction: AttractionResult, index: number) => (
              <div key={index} className="bg-gray-50 p-3 rounded-lg">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><strong>Name:</strong> {attraction.name}</div>
                  <div><strong>Rating:</strong> {attraction.rating || 'N/A'}</div>
                  <div><strong>Visit Duration:</strong> {attraction.visit_duration_estimate ? `${attraction.visit_duration_estimate} min` : 'N/A'}</div>
                  <div><strong>Open Now:</strong> {attraction.opening_hours?.open_now ? 'Yes' : 'No'}</div>
                  <div className="col-span-2"><strong>Address:</strong> {attraction.formatted_address}</div>
                  {attraction.website && (
                    <div className="col-span-2">
                      <strong>Website:</strong>{' '}
                      <a 
                        href={attraction.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Visit website
                      </a>
                    </div>
                  )}
                </div>
                {attraction.place_id && (
                  <div className="mt-3 pt-2 border-t border-gray-200">
                    <a
                      href={getGoogleMapsUrl(attraction.place_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                    >
                      <MapPin className="w-4 h-4 mr-1" />
                      View on Google Maps
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Restaurant results component
const RestaurantResultsContent: React.FC<{ results: ResultData }> = ({ results }) => {
  // Type guard for restaurant results
  if (!('restaurants' in results)) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-gray-600">No restaurant results available.</p>
        </CardContent>
      </Card>
    );
  }

  const restaurantResults = results as { restaurants: RestaurantResult[]; recommendation?: string };
  
  return (
    <Card>
      <CardContent className="p-4">
        {restaurantResults.recommendation && (
          <p className="text-gray-600 mb-4">{restaurantResults.recommendation}</p>
        )}
        
        {restaurantResults.restaurants && restaurantResults.restaurants.length > 0 && (
          <div className="space-y-3">
            <h4 className="font-medium">Recommended Restaurants</h4>
            {restaurantResults.restaurants.slice(0, 3).map((restaurant: RestaurantResult, index: number) => (
              <div key={index} className="bg-gray-50 p-3 rounded-lg">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div><strong>Name:</strong> {restaurant.name}</div>
                  <div><strong>Rating:</strong> {restaurant.rating || 'N/A'}</div>
                  <div><strong>Price Level:</strong> {restaurant.price_level || 'N/A'}</div>
                  <div><strong>Open Now:</strong> {restaurant.is_open_now ? 'Yes' : 'No'}</div>
                  <div className="col-span-2"><strong>Address:</strong> {restaurant.address}</div>
                </div>
                {restaurant.place_id && (
                  <div className="mt-3 pt-2 border-t border-gray-200">
                    <a
                      href={getGoogleMapsUrl(restaurant.place_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                    >
                      <MapPin className="w-4 h-4 mr-1" />
                      View on Google Maps
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Itinerary results component - handles TravelItinerary format
const ItineraryResultsContent: React.FC<{ results: ResultData }> = ({ results }) => {
  // Check if it's the TravelItinerary format
  if ('trip_title' in results && 'daily_itineraries' in results) {
    const travelItinerary = results as TravelItinerary & { type: 'itinerary'; timestamp: Date };
    
    // Add missing fields for ItineraryTimeline component
    const itineraryWithDefaults: TravelItinerary = {
      ...travelItinerary,
      trip_summary: travelItinerary.trip_summary || 'Your travel itinerary',
      created_at: travelItinerary.created_at || new Date().toISOString(),
      last_updated: travelItinerary.last_updated || new Date().toISOString(),
    };
    
    return <ItineraryTimeline itinerary={itineraryWithDefaults} />;
  }
  
  // No itinerary data available
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-gray-600">No itinerary data available.</p>
      </CardContent>
    </Card>
  );
};

// Generic results fallback component
const GenericResultsContent: React.FC<{ results: ResultData }> = ({ results }) => (
  <Card>
    <CardContent className="p-4">
      <div className="flex items-center space-x-2 mb-4">
        <AlertCircle className="w-5 h-5 text-gray-600" />
        <h3 className="font-semibold">Results</h3>
      </div>
      <p className="text-gray-600">{'recommendation' in results ? results.recommendation : 'Results received from travel assistant.'}</p>
      
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <pre className="text-xs text-gray-700 whitespace-pre-wrap">
          {JSON.stringify(results, null, 2)}
        </pre>
      </div>
    </CardContent>
  </Card>
);
