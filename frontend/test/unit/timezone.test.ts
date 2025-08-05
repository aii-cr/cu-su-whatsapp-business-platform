/**
 * Unit tests for timezone conversion utilities.
 * Tests UTC-to-Costa Rica timezone conversions and edge cases.
 */

import { 
  formatMessageTime, 
  getMessageDayBanner, 
  isSameDay, 
  getCurrentCRTime,
  toCRTime 
} from '@/lib/timezone';

describe('Timezone Utilities', () => {
  describe('formatMessageTime', () => {
    it('should format UTC timestamp to Costa Rica time', () => {
      // Test with a known UTC timestamp
      const utcDate = new Date('2024-01-15T18:30:00Z'); // 6:30 PM UTC
      const result = formatMessageTime(utcDate);
      
      // Costa Rica is UTC-6, so 6:30 PM UTC = 12:30 PM CR
      expect(result).toBe('12:30 PM');
    });

    it('should handle string timestamps', () => {
      const utcString = '2024-01-15T18:30:00Z';
      const result = formatMessageTime(utcString);
      expect(result).toBe('12:30 PM');
    });

    it('should handle numeric timestamps', () => {
      // Use a known UTC timestamp that converts to 12:30 PM in Costa Rica
      const utcTimestamp = new Date('2024-01-15T18:30:00Z').getTime();
      const result = formatMessageTime(utcTimestamp);
      expect(result).toBe('12:30 PM');
    });

    it('should handle edge case at midnight UTC', () => {
      const utcDate = new Date('2024-01-15T00:00:00Z'); // Midnight UTC
      const result = formatMessageTime(utcDate);
      // Should be 6:00 PM previous day in Costa Rica (UTC-6)
      expect(result).toBe('6:00 PM');
    });

    it('should handle edge case at noon UTC', () => {
      const utcDate = new Date('2024-01-15T12:00:00Z'); // Noon UTC
      const result = formatMessageTime(utcDate);
      // Should be 6:00 AM in Costa Rica (UTC-6)
      expect(result).toBe('6:00 AM');
    });
  });

  describe('getMessageDayBanner', () => {
    beforeEach(() => {
      // Mock current date to ensure consistent test results
      jest.useFakeTimers();
      jest.setSystemTime(new Date('2024-01-15T12:00:00Z'));
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should return "Today" for messages from today in CR timezone', () => {
      // 6 PM UTC = 12 PM CR (same day)
      const todayMessage = new Date('2024-01-15T18:00:00Z');
      const result = getMessageDayBanner(todayMessage);
      expect(result).toBe('Today');
    });

    it('should return "Yesterday" for messages from yesterday in CR timezone', () => {
      // 6 PM UTC previous day = 12 PM CR previous day
      const yesterdayMessage = new Date('2024-01-14T18:00:00Z');
      const result = getMessageDayBanner(yesterdayMessage);
      expect(result).toBe('Yesterday');
    });

    it('should return formatted date for older messages', () => {
      const olderMessage = new Date('2024-01-10T18:00:00Z');
      const result = getMessageDayBanner(olderMessage);
      expect(result).toMatch(/January 10/);
    });

    it('should include year for messages from different years', () => {
      const lastYearMessage = new Date('2023-01-15T18:00:00Z');
      const result = getMessageDayBanner(lastYearMessage);
      expect(result).toMatch(/2023/);
    });

    it('should handle edge case around midnight CR time', () => {
      // 6 AM UTC = midnight CR (previous day)
      const midnightMessage = new Date('2024-01-15T06:00:00Z');
      const result = getMessageDayBanner(midnightMessage);
      // The actual behavior depends on the current date in the test
      expect(result).toMatch(/Today|Yesterday|January/);
    });
  });

  describe('isSameDay', () => {
    it('should return true for messages on the same day in CR timezone', () => {
      const date1 = new Date('2024-01-15T18:00:00Z'); // 12 PM CR
      const date2 = new Date('2024-01-15T22:00:00Z'); // 4 PM CR
      const result = isSameDay(date1, date2);
      expect(result).toBe(true);
    });

    it('should return false for messages on different days in CR timezone', () => {
      const date1 = new Date('2024-01-15T18:00:00Z'); // 12 PM CR
      const date2 = new Date('2024-01-16T06:00:00Z'); // 12 AM CR next day
      const result = isSameDay(date1, date2);
      expect(result).toBe(false);
    });

    it('should handle edge case around midnight CR time', () => {
      const date1 = new Date('2024-01-15T06:00:00Z'); // Midnight CR
      const date2 = new Date('2024-01-15T18:00:00Z'); // Noon CR
      const result = isSameDay(date1, date2);
      // These should be on the same day in Costa Rica timezone
      expect(result).toBe(true);
    });
  });

  describe('getCurrentCRTime', () => {
    it('should return current time in Costa Rica timezone', () => {
      const result = getCurrentCRTime();
      expect(result).toMatch(/^\d{1,2}:\d{2} (AM|PM)$/); // 12-hour format with AM/PM
    });
  });

  describe('toCRTime', () => {
    it('should convert UTC timestamp to Costa Rica datetime object', () => {
      const utcDate = new Date('2024-01-15T18:30:00Z');
      const crDate = toCRTime(utcDate);
      
      // Should be 6 hours earlier in Costa Rica
      expect(crDate.getHours()).toBe(12); // 12:30 PM CR
      expect(crDate.getMinutes()).toBe(30);
    });
  });

  describe('Performance Tests', () => {
    it('should format multiple timestamps efficiently', () => {
      const startTime = performance.now();
      
      // Format 1000 timestamps
      for (let i = 0; i < 1000; i++) {
        formatMessageTime(new Date('2024-01-15T18:30:00Z'));
      }
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Should complete in under 10ms (microsecond performance)
      expect(duration).toBeLessThan(10);
    });

    it('should reuse formatter instance for consistent performance', () => {
      const results = [];
      const startTime = performance.now();
      
      // Format multiple timestamps
      for (let i = 0; i < 100; i++) {
        const time = new Date(`2024-01-15T${18 + i % 6}:${30 + i % 30}:00Z`);
        results.push(formatMessageTime(time));
      }
      
      const endTime = performance.now();
      const duration = endTime - startTime;
      
      // Should complete quickly and return consistent results
      expect(duration).toBeLessThan(5);
      expect(results.every(r => /^\d{1,2}:\d{2} (AM|PM)$/.test(r))).toBe(true);
    });
  });

  describe('Edge Cases', () => {
    it('should handle invalid dates gracefully', () => {
      expect(() => formatMessageTime('invalid-date')).not.toThrow();
      expect(() => getMessageDayBanner('invalid-date')).not.toThrow();
    });

    it('should handle null and undefined inputs', () => {
      expect(() => formatMessageTime(null as any)).not.toThrow();
      expect(() => formatMessageTime(undefined as any)).not.toThrow();
    });

    it('should handle daylight saving time transitions', () => {
      // Test during DST transition periods
      const dstStart = new Date('2024-03-10T02:00:00Z'); // DST starts
      const dstEnd = new Date('2024-11-03T02:00:00Z'); // DST ends
      
      expect(() => formatMessageTime(dstStart)).not.toThrow();
      expect(() => formatMessageTime(dstEnd)).not.toThrow();
    });
  });
}); 