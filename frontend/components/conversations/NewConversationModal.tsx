/**
 * Modal for starting new conversations with template messages.
 * Includes country code selector, phone number input, and template selection.
 */

'use client';

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useNotifications } from '@/components/feedback/NotificationSystem';
import { PhoneIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline';

// Country codes for phone number formatting
const COUNTRY_CODES = [
  { code: '+506', country: 'Costa Rica', flag: '🇨🇷' },
  { code: '+1', country: 'United States', flag: '🇺🇸' },
  { code: '+1', country: 'Canada', flag: '🇨🇦' },
  { code: '+52', country: 'Mexico', flag: '🇲🇽' },
  { code: '+34', country: 'Spain', flag: '🇪🇸' },
  { code: '+33', country: 'France', flag: '🇫🇷' },
  { code: '+49', country: 'Germany', flag: '🇩🇪' },
  { code: '+39', country: 'Italy', flag: '🇮🇹' },
  { code: '+44', country: 'United Kingdom', flag: '🇬🇧' },
  { code: '+55', country: 'Brazil', flag: '🇧🇷' },
  { code: '+54', country: 'Argentina', flag: '🇦🇷' },
  { code: '+57', country: 'Colombia', flag: '🇨🇴' },
];

// Form validation schema
const NewConversationSchema = z.object({
  countryCode: z.string().min(1, 'Country code is required'),
  phoneNumber: z
    .string()
    .min(7, 'Phone number must be at least 7 digits')
    .regex(/^\d+$/, 'Phone number must contain only digits')
    .refine((val) => val.length >= 7 && val.length <= 15, 'Phone number must be between 7 and 15 digits'),
  customerName: z.string().optional(),
  templateName: z.string().min(1, 'Template is required'),
  templateLanguage: z.string().default('en_US'),
});

type NewConversationFormData = z.infer<typeof NewConversationSchema>;

interface Template {
  name: string;
  language: string;
  category: string;
  components?: Array<{
    type: string;
    text?: string;
    parameters?: Array<{ type: string; text: string }>;
  }>;
}

interface NewConversationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function NewConversationModal({ 
  isOpen, 
  onClose, 
  onSuccess 
}: NewConversationModalProps) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showSuccess, showError } = useNotifications();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm<NewConversationFormData>({
    resolver: zodResolver(NewConversationSchema),
    defaultValues: {
      countryCode: '+506', // Default to Costa Rica as requested
      templateLanguage: 'en_US',
    },
  });

  const selectedTemplate = watch('templateName');

  // Load templates when modal opens
  useEffect(() => {
    if (isOpen) {
      loadTemplates();
    }
  }, [isOpen]); // loadTemplates is stable, no need to include it

  const loadTemplates = async () => {
    setIsLoadingTemplates(true);
    try {
      const response = await fetch('/api/whatsapp/messages/templates', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to load templates');
      }

      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      showError('Failed to load message templates. Please try again.');
      setTemplates([]);
    } finally {
      setIsLoadingTemplates(false);
    }
  };

  const onSubmit = async (data: NewConversationFormData) => {
    setIsSubmitting(true);
    try {
      // Format the complete phone number
      const fullPhoneNumber = `${data.countryCode.replace('+', '')}${data.phoneNumber}`;

      const requestData = {
        phone_number: fullPhoneNumber,
        customer_name: data.customerName || undefined,
        template_name: data.templateName,
        template_language: data.templateLanguage,
        priority: 'normal',
      };

      const response = await fetch('/api/conversations/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to start conversation');
      }

      const result = await response.json();
      
      showSuccess(
        `Conversation started successfully! ${result.message_sent ? 'Template message sent.' : 'Message sending failed, but conversation was created.'}`
      );
      
      // Reset form and close modal
      reset();
      onClose();
      
      // Call success callback if provided
      if (onSuccess) {
        onSuccess();
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      showError(
        error instanceof Error 
          ? error.message 
          : 'Failed to start conversation. Please try again.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      reset();
      onClose();
    }
  };

  const getTemplatePreview = (template: Template) => {
    if (!template.components) return 'No preview available';
    
    const textComponent = template.components.find(c => c.type === 'BODY');
    if (textComponent && textComponent.text) {
      return textComponent.text.substring(0, 100) + (textComponent.text.length > 100 ? '...' : '');
    }
    
    return 'Template preview not available';
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center space-x-2">
            <ChatBubbleLeftIcon className="w-5 h-5 text-primary" />
            <span>Start New Conversation</span>
          </DialogTitle>
          <DialogDescription>
            Enter a customer&apos;s phone number and select a template to start a new WhatsApp conversation.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Phone Number Section */}
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Country Code */}
              <div>
                <Label htmlFor="countryCode">Country</Label>
                <Select 
                  value={watch('countryCode')} 
                  onValueChange={(value) => setValue('countryCode', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select country" />
                  </SelectTrigger>
                  <SelectContent>
                    {COUNTRY_CODES.map((country) => (
                      <SelectItem key={`${country.code}-${country.country}`} value={country.code}>
                        {country.flag} {country.code} {country.country}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.countryCode && (
                  <p className="text-sm text-error mt-1">{errors.countryCode.message}</p>
                )}
              </div>

              {/* Phone Number */}
              <div className="md:col-span-2">
                <Label htmlFor="phoneNumber">Phone Number</Label>
                <div className="relative">
                  <PhoneIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="phoneNumber"
                    placeholder="84716592"
                    className="pl-10"
                    {...register('phoneNumber')}
                  />
                </div>
                {errors.phoneNumber && (
                  <p className="text-sm text-error mt-1">{errors.phoneNumber.message}</p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Complete number will be: {watch('countryCode') || '+506'}{watch('phoneNumber') || 'XXXXXXXX'}
                </p>
              </div>
            </div>

            {/* Customer Name (Optional) */}
            <div>
              <Label htmlFor="customerName">Customer Name (Optional)</Label>
              <Input
                id="customerName"
                placeholder="John Doe"
                {...register('customerName')}
              />
            </div>
          </div>

          {/* Template Selection */}
          <div className="space-y-4">
            <div>
              <Label>WhatsApp Message Template</Label>
              <p className="text-sm text-muted-foreground">
                Select an approved template to send as the first message.
              </p>
            </div>

            {isLoadingTemplates ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                <p className="text-muted-foreground mt-2">Loading templates...</p>
              </div>
            ) : templates.length === 0 ? (
              <Card>
                <CardContent className="p-6 text-center">
                  <p className="text-muted-foreground">No approved templates found.</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Please configure WhatsApp templates in your Meta Business account.
                  </p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto">
                {templates.map((template) => (
                  <Card 
                    key={`${template.name}-${template.language}`}
                    className={`cursor-pointer transition-all duration-150 ${
                      selectedTemplate === template.name 
                        ? 'ring-2 ring-primary border-primary' 
                        : 'hover:border-primary/50'
                    }`}
                    onClick={() => setValue('templateName', template.name)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <h4 className="font-medium text-foreground">{template.name}</h4>
                            <Badge variant="outline" className="text-xs">
                              {template.category}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {template.language}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {getTemplatePreview(template)}
                          </p>
                        </div>
                        {selectedTemplate === template.name && (
                          <div className="w-4 h-4 bg-primary rounded-full flex items-center justify-center ml-2">
                            <div className="w-2 h-2 bg-white rounded-full"></div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}

            {errors.templateName && (
              <p className="text-sm text-error">{errors.templateName.message}</p>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4 border-t">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || templates.length === 0}
              className="min-w-32"
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Starting...
                </>
              ) : (
                'Start Conversation'
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}