/**
 * Day banner component for grouping messages by day.
 * Shows "Today", "Yesterday", or formatted date for message grouping.
 */

import * as React from 'react';
import { getMessageDayBanner } from '@/lib/utils';
import { cn } from '@/lib/utils';

export interface DayBannerProps {
  date: Date | string | number;
  className?: string;
}

const DayBanner = React.forwardRef<HTMLDivElement, DayBannerProps>(
  ({ date, className }, ref) => {
    console.log('🎯 [DAY_BANNER] Raw date received:', date);
    console.log('🎯 [DAY_BANNER] Date as ISO:', new Date(date).toISOString());
    console.log('🎯 [DAY_BANNER] Current time Costa Rica:', new Intl.DateTimeFormat('en-US', {
      weekday: 'long',
      month: 'long', 
      day: 'numeric',
      timeZone: 'America/Costa_Rica'
    }).format(new Date()));
    
    const bannerText = getMessageDayBanner(date);
    
    console.log('🎯 [DAY_BANNER] Banner text result:', bannerText);

    return (
      <div
        ref={ref}
        className={cn(
          'flex justify-center my-4',
          className
        )}
      >
        <div className="bg-slate-100 dark:bg-slate-700/50 text-slate-600 dark:text-slate-300 text-xs font-medium px-3 py-1.5 rounded-full shadow-sm">
          {bannerText}
        </div>
      </div>
    );
  }
);

DayBanner.displayName = 'DayBanner';

export { DayBanner };