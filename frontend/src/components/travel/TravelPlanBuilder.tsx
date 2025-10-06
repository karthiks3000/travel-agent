import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { 
  PlaneIcon, 
  BuildingIcon, 
  UtensilsIcon, 
  MapPinIcon,
  CalendarIcon,
  UsersIcon
} from 'lucide-react';

interface TravelPlanBuilderProps {
  onSearch: (query: string) => void;
  onAdvancedSearch: (searchParams: TravelSearchParams) => void;
  isLoading?: boolean;
}

export interface TravelSearchParams {
  searchType: 'flights' | 'accommodations' | 'restaurants' | 'attractions' | 'comprehensive';
  destination?: string;
  origin?: string;
  departureDate?: string;
  returnDate?: string;
  travelers?: number;
  cuisineType?: string;
  priceRange?: string;
  attractionTypes?: string[];
  maxResults?: number;
}

export function TravelPlanBuilder({ onSearch, onAdvancedSearch, isLoading }: TravelPlanBuilderProps) {
  const [searchParams, setSearchParams] = useState<TravelSearchParams>({
    searchType: 'comprehensive',
    maxResults: 5
  });
  
  const [quickSearch, setQuickSearch] = useState('');

  const handleQuickSearch = () => {
    if (quickSearch.trim()) {
      onSearch(quickSearch);
    }
  };

  const handleAdvancedSearch = () => {
    onAdvancedSearch(searchParams);
  };

  const getSearchDescription = () => {
    const descriptions = {
      flights: 'Search for flight options with flexible dates and preferences',
      accommodations: 'Find hotels, Airbnb, and other accommodation options',
      restaurants: 'Discover restaurants with cuisine and price preferences',
      attractions: 'Explore tourist attractions, museums, and activities',
      comprehensive: 'Create a complete day-by-day travel itinerary'
    };
    return descriptions[searchParams.searchType];
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Quick Search */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPinIcon className="h-5 w-5 text-primary" />
            Quick Travel Search
          </CardTitle>
          <CardDescription>
            Ask for anything: "Best flight to Paris", "5 hotels under $200", "Plan my 7-day Rome vacation"
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="e.g., Plan my 5-day trip to Tokyo from New York in April"
              value={quickSearch}
              onChange={(e) => setQuickSearch(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleQuickSearch()}
              className="flex-1"
            />
            <Button onClick={handleQuickSearch} disabled={isLoading || !quickSearch.trim()}>
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Search Builder */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Travel Planning</CardTitle>
          <CardDescription>
            {getSearchDescription()}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Type Selector */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
            {[
              { type: 'flights', icon: PlaneIcon, label: 'Flights' },
              { type: 'accommodations', icon: BuildingIcon, label: 'Hotels' },
              { type: 'restaurants', icon: UtensilsIcon, label: 'Restaurants' },
              { type: 'attractions', icon: MapPinIcon, label: 'Attractions' },
              { type: 'comprehensive', icon: CalendarIcon, label: 'Full Plan' }
            ].map((option) => (
              <Button
                key={option.type}
                variant={searchParams.searchType === option.type ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSearchParams({ ...searchParams, searchType: option.type as TravelSearchParams['searchType'] })}
                className="flex items-center gap-1"
              >
                <option.icon className="h-4 w-4" />
                {option.label}
              </Button>
            ))}
          </div>

          {/* Core Travel Information */}
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="destination">Destination *</Label>
              <Input
                id="destination"
                placeholder="e.g., Paris, Tokyo, London"
                value={searchParams.destination || ''}
                onChange={(e) => setSearchParams({ ...searchParams, destination: e.target.value })}
              />
            </div>

            {(searchParams.searchType === 'flights' || searchParams.searchType === 'comprehensive') && (
              <div>
                <Label htmlFor="origin">Origin City *</Label>
                <Input
                  id="origin"
                  placeholder="e.g., New York, Los Angeles, Chicago"
                  value={searchParams.origin || ''}
                  onChange={(e) => setSearchParams({ ...searchParams, origin: e.target.value })}
                />
              </div>
            )}
          </div>

          {/* Dates and Travelers */}
          <div className="grid md:grid-cols-3 gap-4">
            {(searchParams.searchType === 'flights' || searchParams.searchType === 'accommodations' || searchParams.searchType === 'comprehensive') && (
              <>
                <div>
                  <Label htmlFor="departureDate">Departure Date *</Label>
                  <Input
                    id="departureDate"
                    type="date"
                    value={searchParams.departureDate || ''}
                    onChange={(e) => setSearchParams({ ...searchParams, departureDate: e.target.value })}
                  />
                </div>

                <div>
                  <Label htmlFor="returnDate">Return Date</Label>
                  <Input
                    id="returnDate"
                    type="date"
                    value={searchParams.returnDate || ''}
                    onChange={(e) => setSearchParams({ ...searchParams, returnDate: e.target.value })}
                  />
                </div>
              </>
            )}

            <div>
              <Label htmlFor="travelers">Travelers</Label>
              <div className="flex items-center gap-2">
                <UsersIcon className="h-4 w-4 text-muted-foreground" />
                <Input
                  id="travelers"
                  type="number"
                  min="1"
                  max="10"
                  value={searchParams.travelers || 2}
                  onChange={(e) => setSearchParams({ ...searchParams, travelers: parseInt(e.target.value) || 2 })}
                />
              </div>
            </div>
          </div>

          {/* Restaurant-specific options */}
          {searchParams.searchType === 'restaurants' && (
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="cuisineType">Cuisine Type</Label>
                <Input
                  id="cuisineType"
                  placeholder="e.g., Italian, Japanese, Seafood"
                  value={searchParams.cuisineType || ''}
                  onChange={(e) => setSearchParams({ ...searchParams, cuisineType: e.target.value })}
                />
              </div>
              
              <div>
                <Label htmlFor="priceRange">Price Range</Label>
                <select
                  className="w-full p-2 border border-input rounded-md"
                  value={searchParams.priceRange || ''}
                  onChange={(e) => setSearchParams({ ...searchParams, priceRange: e.target.value })}
                >
                  <option value="">Any price</option>
                  <option value="budget">Budget ($)</option>
                  <option value="moderate">Moderate ($$)</option>
                  <option value="expensive">Expensive ($$$)</option>
                  <option value="luxury">Luxury ($$$$)</option>
                </select>
              </div>
            </div>
          )}

          {/* Attraction-specific options */}
          {searchParams.searchType === 'attractions' && (
            <div>
              <Label>Attraction Types</Label>
              <div className="grid grid-cols-3 gap-2 mt-2">
                {['museum', 'park', 'monument', 'church', 'art_gallery', 'zoo'].map((type) => (
                  <Button
                    key={type}
                    size="sm"
                    variant={searchParams.attractionTypes?.includes(type) ? 'default' : 'outline'}
                    onClick={() => {
                      const current = searchParams.attractionTypes || [];
                      const updated = current.includes(type)
                        ? current.filter(t => t !== type)
                        : [...current, type];
                      setSearchParams({ ...searchParams, attractionTypes: updated });
                    }}
                    className="capitalize text-xs"
                  >
                    {type.replace('_', ' ')}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {/* Results count */}
          <div>
            <Label htmlFor="maxResults">Number of Results</Label>
            <select
              className="w-full p-2 border border-input rounded-md"
              value={searchParams.maxResults || 5}
              onChange={(e) => setSearchParams({ ...searchParams, maxResults: parseInt(e.target.value) })}
            >
              <option value={1}>Best option (1)</option>
              <option value={3}>Top 3 options</option>
              <option value={5}>Top 5 options</option>
              <option value={10}>Up to 10 options</option>
            </select>
          </div>

          {/* Search Button */}
          <Button 
            onClick={handleAdvancedSearch}
            disabled={isLoading || !searchParams.destination}
            className="w-full"
          >
            {isLoading ? 'Searching...' : `Search ${searchParams.searchType === 'comprehensive' ? 'Complete Itinerary' : searchParams.searchType}`}
          </Button>
        </CardContent>
      </Card>

      {/* Quick Action Buttons */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          onClick={() => onSearch("Show me the best flight options to Paris next month")}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <PlaneIcon className="h-4 w-4" />
          Quick Flight Search
        </Button>
        
        <Button
          variant="outline"
          onClick={() => onSearch("Plan a complete 7-day European vacation")}
          disabled={isLoading}
          className="flex items-center gap-2"
        >
          <CalendarIcon className="h-4 w-4" />
          Full Itinerary
        </Button>
      </div>
    </div>
  );
}

export default TravelPlanBuilder;
