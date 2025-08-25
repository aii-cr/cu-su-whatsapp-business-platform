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
    const bannerText = getMessageDayBanner(date);

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