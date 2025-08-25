/**
 * Timezone utilities for Costa Rica timezone conversion.
 * Optimized with single Intl.DateTimeFormat instance for performance.
 */

// Single optimized formatter instance for Costa Rica timezone (12-hour format like WhatsApp)
const crFormatter = new Intl.DateTimeFormat('en-US', {
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
  timeZone: 'America/Costa_Rica',
});

// Single optimized date formatter for day headers
const crDateFormatter = new Intl.DateTimeFormat('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
  timeZone: 'America/Costa_Rica',
});

// Single optimized relative date formatter
const crRelativeDateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
  timeZone: 'America/Costa_Rica',
});

// Formatters for extracting date components in Costa Rica timezone
const crYearFormatter = new Intl.DateTimeFormat('en-US', {
  year: 'numeric',
  timeZone: 'America/Costa_Rica',
});

const crMonthFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'numeric',
  timeZone: 'America/Costa_Rica',
});

const crDayFormatter = new Intl.DateTimeFormat('en-US', {
  day: 'numeric',
  timeZone: 'America/Costa_Rica',
});

/**
 * Convert UTC timestamp to Costa Rica local time for display.
 * Uses optimized formatter instance for microsecond performance.
 * 
 * @param date - UTC timestamp (Date, string, or number)
 * @returns Formatted time string in Costa Rica timezone (HH:mm format)
 */
export function formatMessageTime(date: Date | string | number): string {
  try {
    let dateObj: Date;
    
    if (typeof date === 'string') {
      // Ensure ISO strings are treated as UTC
      if (date.endsWith('Z')) {
        // Already UTC ISO string, parse directly
        dateObj = new Date(date);
      } else {
        // Assume it's UTC and add Z if missing
        const utcString = date.endsWith('Z') ? date : date + 'Z';
        dateObj = new Date(utcString);
      }
    } else {
      dateObj = new Date(date);
    }
    
    if (isNaN(dateObj.getTime())) {
      return ''; // Return empty string for invalid dates
    }
    
    return crFormatter.format(dateObj);
  } catch (error) {
    return ''; // Return empty string for any errors
  }
}

/**
 * Get day banner text for message grouping in Costa Rica timezone.
 * Returns "Today", "Yesterday", or formatted date for grouping messages by day.
 * 
 * @param date - UTC timestamp
 * @returns Day banner text
 */
export function getMessageDayBanner(date: Date | string | number): string {
  try {
    let messageDate = new Date(date);
    if (isNaN(messageDate.getTime())) {
      return ''; // Return empty string for invalid dates
    }
    
    // TEMPORARY FIX: Detect if this is a backend message with timezone offset issue
    // Backend messages from before the fix have timestamps 6 hours in the future
    const now = new Date();
    const timeDiff = messageDate.getTime() - now.getTime();
    const sixHoursInMs = 6 * 60 * 60 * 1000;
    
    // If message timestamp is significantly in the future (more than 3 hours), 
    // it's likely a backend message with the timezone offset issue
    if (timeDiff > (3 * 60 * 60 * 1000)) {
      console.log('🔧 [TIMEZONE] Detected backend message with offset, adjusting timestamp');
      messageDate = new Date(messageDate.getTime() - sixHoursInMs);
    }
    
    // Extract date components in Costa Rica timezone using Intl.DateTimeFormat
    const messageYear = parseInt(crYearFormatter.format(messageDate));
    const messageMonth = parseInt(crMonthFormatter.format(messageDate));
    const messageDay = parseInt(crDayFormatter.format(messageDate));
    
    const nowYear = parseInt(crYearFormatter.format(now));
    const nowMonth = parseInt(crMonthFormatter.format(now));
    const nowDay = parseInt(crDayFormatter.format(now));
    
    // Check if message is from today in Costa Rica timezone
    const isToday = messageYear === nowYear && messageMonth === nowMonth && messageDay === nowDay;
    
    if (isToday) {
      return 'Today';
    }
    
    // Check if message is from yesterday in Costa Rica timezone
    const yesterday = new Date(now);
    yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayYear = parseInt(crYearFormatter.format(yesterday));
    const yesterdayMonth = parseInt(crMonthFormatter.format(yesterday));
    const yesterdayDay = parseInt(crDayFormatter.format(yesterday));
    
    const isYesterday = messageYear === yesterdayYear && messageMonth === yesterdayMonth && messageDay === yesterdayDay;
    
    if (isYesterday) {
      return 'Yesterday';
    }
    
    // For older messages, return formatted date in Costa Rica timezone
    if (messageYear !== nowYear) {
      return crRelativeDateFormatter.format(messageDate);
    }
    
    return crDateFormatter.format(messageDate);
  } catch (error) {
    console.error('Error in getMessageDayBanner:', error);
    return ''; // Return empty string for any errors
  }
}

/**
 * Check if two dates are on the same day in Costa Rica timezone.
 * 
 * @param date1 - First UTC timestamp
 * @param date2 - Second UTC timestamp
 * @returns True if dates are on the same day in Costa Rica timezone
 */
export function isSameDay(date1: Date | string | number, date2: Date | string | number): boolean {
  try {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    
    if (isNaN(d1.getTime()) || isNaN(d2.getTime())) {
      return false;
    }
    
    // Extract date components in Costa Rica timezone using Intl.DateTimeFormat
    const d1Year = parseInt(crYearFormatter.format(d1));
    const d1Month = parseInt(crMonthFormatter.format(d1));
    const d1Day = parseInt(crDayFormatter.format(d1));
    
    const d2Year = parseInt(crYearFormatter.format(d2));
    const d2Month = parseInt(crMonthFormatter.format(d2));
    const d2Day = parseInt(crDayFormatter.format(d2));
    
    return d1Year === d2Year && d1Month === d2Month && d1Day === d2Day;
  } catch (error) {
    console.error('Error in isSameDay:', error);
    return false;
  }
}

/**
 * Get current time in Costa Rica timezone.
 * 
 * @returns Current time string in Costa Rica timezone (HH:mm format)
 */
export function getCurrentCRTime(): string {
  return crFormatter.format(new Date());
}

/**
 * Convert UTC timestamp to Costa Rica datetime object.
 * 
 * @param date - UTC timestamp
 * @returns Date object representing the time in Costa Rica timezone
 */
export function toCRTime(date: Date | string | number): Date {
  const utcDate = new Date(date);
  const crTimeString = utcDate.toLocaleString('en-US', { timeZone: 'America/Costa_Rica' });
  return new Date(crTimeString);
}

// Export the formatter for direct use if needed
export { 
  crFormatter, 
  crDateFormatter, 
  crRelativeDateFormatter,
  crYearFormatter,
  crMonthFormatter,
  crDayFormatter
}; 