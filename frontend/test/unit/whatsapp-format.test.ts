/**
 * Test to verify time format matches WhatsApp's exact format.
 * WhatsApp displays times in 12-hour format with AM/PM (e.g., "3:34 PM").
 */

import { formatMessageTime } from '@/lib/timezone';

describe('WhatsApp Time Format', () => {
  it('should match WhatsApp format exactly', () => {
    // Test various times to ensure they match WhatsApp format
    
    // Morning time
    const morningTime = new Date('2024-01-15T10:30:00Z'); // 10:30 AM UTC
    expect(formatMessageTime(morningTime)).toBe('4:30 AM'); // 4:30 AM CR
    
    // Afternoon time
    const afternoonTime = new Date('2024-01-15T18:30:00Z'); // 6:30 PM UTC
    expect(formatMessageTime(afternoonTime)).toBe('12:30 PM'); // 12:30 PM CR
    
    // Evening time
    const eveningTime = new Date('2024-01-15T21:34:00Z'); // 9:34 PM UTC
    expect(formatMessageTime(eveningTime)).toBe('3:34 PM'); // 3:34 PM CR
    
    // Midnight
    const midnightTime = new Date('2024-01-15T00:00:00Z'); // Midnight UTC
    expect(formatMessageTime(midnightTime)).toBe('6:00 PM'); // 6:00 PM CR (previous day)
    
    // Noon
    const noonTime = new Date('2024-01-15T12:00:00Z'); // Noon UTC
    expect(formatMessageTime(noonTime)).toBe('6:00 AM'); // 6:00 AM CR
  });

  it('should handle single digit hours correctly', () => {
    // Test times that should show single digit hours (like "3:34 PM")
    const singleDigitTime = new Date('2024-01-15T21:34:00Z'); // 9:34 PM UTC
    const result = formatMessageTime(singleDigitTime);
    
    // Should be "3:34 PM" (not "03:34 PM")
    expect(result).toBe('3:34 PM');
    expect(result).toMatch(/^\d{1}:\d{2} (AM|PM)$/); // Single digit hour
  });

  it('should handle double digit hours correctly', () => {
    // Test times that should show double digit hours
    const doubleDigitTime = new Date('2024-01-15T18:30:00Z'); // 6:30 PM UTC
    const result = formatMessageTime(doubleDigitTime);
    
    // Should be "12:30 PM"
    expect(result).toBe('12:30 PM');
    expect(result).toMatch(/^\d{2}:\d{2} (AM|PM)$/); // Double digit hour
  });

  it('should match the exact format from the screenshot', () => {
    // Based on the screenshot showing "3:34 PM"
    const screenshotTime = new Date('2024-01-15T21:34:00Z'); // 9:34 PM UTC
    const result = formatMessageTime(screenshotTime);
    
    // Should match exactly: "3:34 PM"
    expect(result).toBe('3:34 PM');
  });

  it('should handle ISO string timestamps correctly', () => {
    // Test with ISO string format that comes from backend
    const isoString = '2024-01-15T21:34:00Z';
    const result = formatMessageTime(isoString);
    
    // Should be "3:34 PM" (9:34 PM UTC = 3:34 PM CR)
    expect(result).toBe('3:34 PM');
  });

  it('should handle ISO string without Z suffix', () => {
    // Test with ISO string without Z (should be treated as UTC)
    const isoString = '2024-01-15T21:34:00';
    const result = formatMessageTime(isoString);
    
    // Should be "3:34 PM" (9:34 PM UTC = 3:34 PM CR)
    expect(result).toBe('3:34 PM');
  });
}); 