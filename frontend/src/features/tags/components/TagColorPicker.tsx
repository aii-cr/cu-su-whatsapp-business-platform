/**
 * TagColorPicker component - ClickUp-style color picker for tag creation
 * Supports predefined colors and custom hex input
 */

import * as React from 'react';
import { Check, Palette, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { DEFAULT_TAG_COLORS, validateHexColor } from '../models/tag';

export interface TagColorPickerProps {
  selectedColor: string;
  onColorChange: (color: string) => void;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function TagColorPicker({
  selectedColor,
  onColorChange,
  size = 'md',
  className,
}: TagColorPickerProps) {
  const [showCustomInput, setShowCustomInput] = React.useState(false);
  const [customColor, setCustomColor] = React.useState(selectedColor);
  const [customColorError, setCustomColorError] = React.useState<string | null>(null);

  // Handle predefined color selection
  const handleColorSelect = React.useCallback((color: string) => {
    onColorChange(color);
    setShowCustomInput(false);
    setCustomColorError(null);
  }, [onColorChange]);

  // Handle custom color input
  const handleCustomColorChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setCustomColor(value);
    setCustomColorError(null);

    // Auto-apply if valid hex color
    if (validateHexColor(value)) {
      onColorChange(value.toUpperCase());
    }
  }, [onColorChange]);

  // Handle custom color submit
  const handleCustomColorSubmit = React.useCallback(() => {
    if (validateHexColor(customColor)) {
      onColorChange(customColor.toUpperCase());
      setShowCustomInput(false);
      setCustomColorError(null);
    } else {
      setCustomColorError('Please enter a valid hex color (e.g., #FF5733)');
    }
  }, [customColor, onColorChange]);

  // Handle custom color key press
  const handleCustomColorKeyPress = React.useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleCustomColorSubmit();
    } else if (e.key === 'Escape') {
      setShowCustomInput(false);
      setCustomColor(selectedColor);
      setCustomColorError(null);
    }
  }, [handleCustomColorSubmit, selectedColor]);

  const colorSwatchSize = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-10 w-10',
  };

  const checkIconSize = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <div className={cn('space-y-3', className)}>
      {/* Predefined colors grid */}
      <div className="grid grid-cols-6 gap-2">
        {DEFAULT_TAG_COLORS.map((color) => (
          <button
            key={color}
            type="button"
            onClick={() => handleColorSelect(color)}
            className={cn(
              'relative rounded-md border-2 transition-all duration-150 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1',
              colorSwatchSize[size],
              selectedColor === color 
                ? 'border-gray-400 shadow-md' 
                : 'border-gray-200 hover:border-gray-300'
            )}
            style={{ backgroundColor: color }}
            aria-label={`Select color ${color}`}
            title={color}
          >
            {selectedColor === color && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Check 
                  className={cn(
                    'text-white drop-shadow-sm',
                    checkIconSize[size]
                  )} 
                />
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Custom color section */}
      <div className="space-y-2">
        {!showCustomInput ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => {
              setShowCustomInput(true);
              setCustomColor(selectedColor);
            }}
            className="w-full text-xs"
          >
            <Palette className="h-3 w-3 mr-1" />
            Custom Color
          </Button>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'flex-shrink-0 rounded border border-gray-200',
                  colorSwatchSize[size]
                )}
                style={{ 
                  backgroundColor: validateHexColor(customColor) ? customColor : '#cccccc'
                }}
                title={validateHexColor(customColor) ? customColor : 'Invalid color'}
              />
              
              <Input
                type="text"
                value={customColor}
                onChange={handleCustomColorChange}
                onKeyDown={handleCustomColorKeyPress}
                placeholder="#FF5733"
                maxLength={7}
                className={cn(
                  'flex-1 text-xs font-mono',
                  customColorError && 'border-destructive'
                )}
                autoFocus
              />
              
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  setShowCustomInput(false);
                  setCustomColor(selectedColor);
                  setCustomColorError(null);
                }}
                className="p-1 h-6 w-6"
              >
                <X className="h-3 w-3" />
              </Button>
            </div>

            {customColorError && (
              <p className="text-xs text-destructive">{customColorError}</p>
            )}

            <div className="flex gap-1">
              <Button
                type="button"
                size="sm"
                onClick={handleCustomColorSubmit}
                disabled={!validateHexColor(customColor)}
                className="flex-1 text-xs"
              >
                Apply
              </Button>
              
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowCustomInput(false);
                  setCustomColor(selectedColor);
                  setCustomColorError(null);
                }}
                className="text-xs"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* Current color preview */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>Selected:</span>
        <div
          className={cn(
            'rounded border border-gray-200',
            size === 'sm' && 'h-4 w-4',
            size === 'md' && 'h-5 w-5',
            size === 'lg' && 'h-6 w-6'
          )}
          style={{ backgroundColor: selectedColor }}
        />
        <code className="font-mono text-xs">{selectedColor}</code>
      </div>
    </div>
  );
}

export default TagColorPicker;

