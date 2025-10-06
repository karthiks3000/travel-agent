import type { TravelItinerary, DailyItinerary, ItineraryActivity, ActivityType } from '../../types/chat';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { CalendarIcon, ClockIcon, MapPinIcon } from 'lucide-react';

interface ItineraryTimelineProps {
  itinerary: TravelItinerary;
  onActivityClick?: (activity: ItineraryActivity) => void;
  onDayClick?: (day: DailyItinerary) => void;
}

export function ItineraryTimeline({ itinerary, onActivityClick, onDayClick }: ItineraryTimelineProps) {
  const formatCurrency = (amount?: number) => {
    return amount ? `$${amount.toFixed(0)}` : 'TBD';
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Trip Header */}
      <Card className="border-2 border-primary/20">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl font-bold text-primary">
                {itinerary.trip_title}
              </CardTitle>
              <CardDescription className="text-base">
                {itinerary.trip_summary}
              </CardDescription>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-primary">
                {formatCurrency(itinerary.total_estimated_cost)}
              </div>
              <div className="text-sm text-muted-foreground">
                {formatCurrency((itinerary.total_estimated_cost || 0) / itinerary.traveler_count)} per person
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-4 text-sm text-muted-foreground pt-2">
            <div className="flex items-center gap-1">
              <CalendarIcon className="h-4 w-4" />
              <span>{itinerary.start_date} to {itinerary.end_date}</span>
            </div>
            <div className="flex items-center gap-1">
              <MapPinIcon className="h-4 w-4" />
              <span>{itinerary.destination}</span>
            </div>
            <div>
              {itinerary.traveler_count} traveler{itinerary.traveler_count > 1 ? 's' : ''}
            </div>
            <div>
              {itinerary.total_days} day{itinerary.total_days > 1 ? 's' : ''}
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Daily Itineraries */}
      <div className="space-y-6">
        {itinerary.daily_itineraries.map((day) => (
          <DayCard
            key={`day-${day.day_number}`}
            day={day}
            onActivityClick={onActivityClick}
            onDayClick={onDayClick}
          />
        ))}
      </div>

      {/* Trip Summary */}
      {(itinerary.packing_suggestions?.length || itinerary.travel_tips?.length) && (
        <div className="grid md:grid-cols-2 gap-4">
          {itinerary.packing_suggestions?.length && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">📦 Packing Suggestions</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {itinerary.packing_suggestions.map((suggestion, idx) => (
                    <li key={idx} className="text-sm flex items-start gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span>{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
          
          {itinerary.travel_tips?.length && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">💡 Travel Tips</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-1">
                  {itinerary.travel_tips.map((tip, idx) => (
                    <li key={idx} className="text-sm flex items-start gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

interface DayCardProps {
  day: DailyItinerary;
  onActivityClick?: (activity: ItineraryActivity) => void;
  onDayClick?: (day: DailyItinerary) => void;
}

function DayCard({ day, onActivityClick, onDayClick }: DayCardProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const formatTime = (timeStr: string) => {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const period = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours === 0 ? 12 : hours > 12 ? hours - 12 : hours;
    return `${displayHours}:${minutes.toString().padStart(2, '0')} ${period}`;
  };

  const getActivityIcon = (activityType: ActivityType) => {
    const iconMap = {
      flight: '✈️',
      accommodation: '🏨',
      restaurant: '🍽️',
      attraction: '🏛️',
      transportation: '🚗',
      general: '📍'
    };
    return iconMap[activityType] || '📍';
  };

  const getActivityColor = (activityType: ActivityType) => {
    const colorMap = {
      flight: 'border-blue-200 bg-blue-50',
      accommodation: 'border-green-200 bg-green-50',
      restaurant: 'border-orange-200 bg-orange-50',
      attraction: 'border-purple-200 bg-purple-50',
      transportation: 'border-gray-200 bg-gray-50',
      general: 'border-indigo-200 bg-indigo-50'
    };
    return colorMap[activityType] || 'border-gray-200 bg-gray-50';
  };

  return (
    <Card 
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={() => onDayClick?.(day)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl">
              Day {day.day_number} • {formatDate(day.date)}
            </CardTitle>
            <CardDescription className="text-base">
              {day.daily_summary}
            </CardDescription>
          </div>
          <div className="text-right">
            <div className="text-lg font-semibold">
              {day.estimated_daily_cost ? `$${day.estimated_daily_cost.toFixed(0)}` : 'TBD'}
            </div>
            <div className="text-sm text-muted-foreground">
              {day.activities.length} activities
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2 text-sm text-muted-foreground pt-1">
          <MapPinIcon className="h-4 w-4" />
          <span>{day.location}</span>
          {day.weather_info && (
            <>
              <span>•</span>
              <span>{day.weather_info}</span>
            </>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {/* Activity Timeline */}
        <div className="space-y-2">
          {day.activities.map((activity, actIdx) => (
            <div
              key={actIdx}
              className={`border rounded-lg p-3 cursor-pointer hover:shadow-sm transition-shadow ${getActivityColor(activity.activity_type)}`}
              onClick={(e) => {
                e.stopPropagation();
                onActivityClick?.(activity);
              }}
            >
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 min-w-20">
                  <span className="text-lg">{getActivityIcon(activity.activity_type)}</span>
                  <div className="text-xs">
                    <ClockIcon className="h-3 w-3 inline mr-1" />
                    {formatTime(activity.time_slot.start_time)}
                  </div>
                </div>
                
                <div className="flex-1">
                  <div className="font-medium text-sm">{activity.title}</div>
                  {activity.notes && (
                    <div className="text-xs text-muted-foreground">{activity.notes}</div>
                  )}
                </div>
                
                {/* Activity-specific details */}
                <div className="text-xs text-muted-foreground">
                  {activity.activity_type === 'restaurant' && 'activity_details' in activity.activity_details && 
                   'rating' in activity.activity_details && activity.activity_details.rating && (
                    <span>⭐ {activity.activity_details.rating}</span>
                  )}
                  {activity.activity_type === 'attraction' && 'activity_details' in activity.activity_details && 
                   'visit_duration_estimate' in activity.activity_details && activity.activity_details.visit_duration_estimate && (
                    <span>{activity.activity_details.visit_duration_estimate}min</span>
                  )}
                  {activity.activity_type === 'transportation' && 'activity_details' in activity.activity_details && 
                   'cost_estimate' in activity.activity_details && activity.activity_details.cost_estimate && (
                    <span>${activity.activity_details.cost_estimate}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export default ItineraryTimeline;
