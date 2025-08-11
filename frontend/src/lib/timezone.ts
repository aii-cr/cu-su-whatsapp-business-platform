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
    const messageDate = new Date(date);
    if (isNaN(messageDate.getTime())) {
      return ''; // Return empty string for invalid dates
    }
    
    const now = new Date();
    
    // Convert both dates to Costa Rica timezone for comparison
    const crMessageDate = new Date(messageDate.toLocaleString('en-US', { timeZone: 'America/Costa_Rica' }));
    const crNow = new Date(now.toLocaleString('en-US', { timeZone: 'America/Costa_Rica' }));
    
    // Check if message is from today in Costa Rica timezone
    const isToday = crMessageDate.toDateString() === crNow.toDateString();
    
    if (isToday) {
      return 'Today';
    }
    
    // Check if message is from yesterday in Costa Rica timezone
    const yesterday = new Date(crNow);
    yesterday.setDate(yesterday.getDate() - 1);
    const isYesterday = crMessageDate.toDateString() === yesterday.toDateString();
    
    if (isYesterday) {
      return 'Yesterday';
    }
    
    // For older messages, return formatted date in Costa Rica timezone
    const year = crMessageDate.getFullYear();
    const currentYear = crNow.getFullYear();
    
    if (year !== currentYear) {
      return crRelativeDateFormatter.format(messageDate);
    }
    
    return crDateFormatter.format(messageDate);
  } catch (error) {
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
  const d1 = new Date(date1);
  const d2 = new Date(date2);
  
  // Convert both dates to Costa Rica timezone for comparison
  const crD1 = new Date(d1.toLocaleString('en-US', { timeZone: 'America/Costa_Rica' }));
  const crD2 = new Date(d2.toLocaleString('en-US', { timeZone: 'America/Costa_Rica' }));
  
  return crD1.toDateString() === crD2.toDateString();
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
export { crFormatter, crDateFormatter, crRelativeDateFormatter }; 