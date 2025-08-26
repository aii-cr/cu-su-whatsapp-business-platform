/**
 * Enhanced Modal for starting new conversations with template messages.
 * Features glass effect styling, template search/filtering, and dynamic parameters.
 */

'use client';

import { useState, useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQueryClient } from '@tanstack/react-query';
import { conversationQueryKeys } from '@/features/conversations/hooks/useConversations';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/Dialog';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { toast } from '@/components/feedback/Toast';
import { getApiUrl } from '@/lib/config';
import { 
  PhoneIcon, 
  ChatBubbleLeftIcon,
  XMarkIcon,
  MagnifyingGlassIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  DocumentTextIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import styles from './NewConversationModal.module.scss';

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

// Template interface
interface Template {
  id: string;
  name: string;
  language: string;
  category: string;
  status: string;
  sub_category?: string;
  parameter_format?: string;
  components?: Array<{
    type: string;
    text?: string;
    format?: string;
    example?: any;
    buttons?: Array<{
      type: string;
      text: string;
      url?: string;
    }>;
  }>;
  preview_text?: string;
  parameters?: Array<{
    type: string;
    name: string;
    label: string;
    example: string;
    component: string;
    position: number;
  }>;
}

// Base form schema
const baseFormSchema = z.object({
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

// Create dynamic schema based on selected template
const createFormSchema = (selectedTemplate?: Template) => {
  const extendedFields: Record<string, z.ZodString> = {};

  // Add dynamic parameter fields based on selected template
  if (selectedTemplate?.parameters) {
    selectedTemplate.parameters.forEach((param) => {
      extendedFields[param.name] = z.string().min(1, `${param.label} is required`);
    });
  }

  return baseFormSchema.extend(extendedFields);
};

type BaseFormData = z.infer<typeof baseFormSchema>;
type NewConversationFormData = BaseFormData & Record<string, string>;

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
  const queryClient = useQueryClient();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showSuccess, setShowSuccess] = useState(false);

  // Get unique categories from templates
  const categories = useMemo(() => {
    const uniqueCategories = new Set(templates.map(t => t.category).filter(Boolean));
    return Array.from(uniqueCategories).sort();
  }, [templates]);

  // Filter templates based on search and category
  const filteredTemplates = useMemo(() => {
    return templates.filter(template => {
      const matchesSearch = !searchQuery || 
        template.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        template.preview_text?.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
      
      return matchesSearch && matchesCategory && template.status === 'APPROVED';
    });
  }, [templates, searchQuery, selectedCategory]);

  const [selectedTemplateName, setSelectedTemplateName] = useState<string>('');
  const selectedTemplate = templates.find(t => t.name === selectedTemplateName);

  const formSchema = createFormSchema(selectedTemplate);
  
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      countryCode: '+506', // Default to Costa Rica
      templateLanguage: 'en_US',
    },
  });

  const watchedValues = watch();

  // Load templates when modal opens
  useEffect(() => {
    if (isOpen) {
      loadTemplates();
      // Reset form when modal opens
      reset({
        countryCode: '+506',
        templateLanguage: 'en_US',
      });
      setSearchQuery('');
      setSelectedCategory('all');
      setSelectedTemplateName('');
      setShowSuccess(false);
    }
  }, [isOpen, reset]);

  const loadTemplates = async () => {
    setIsLoadingTemplates(true);
    try {
      const response = await fetch(getApiUrl('messages/templates'), {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to load templates');
      }

      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      toast.error('Failed to load message templates. Please try again.');
      setTemplates([]);
    } finally {
      setIsLoadingTemplates(false);
    }
  };

  const onSubmit = async (data: any) => {
    setIsSubmitting(true);
    try {
      // Format the complete phone number
      const fullPhoneNumber = `${data.countryCode.replace('+', '')}${data.phoneNumber}`;

      // Prepare template parameters
      const templateParameters: Array<{ type: string; text: string }> = [];
      
      // For start_conversation template, we need to handle special parameter mapping
      if (data.templateName === 'start_conversation') {
        // The start_conversation template expects exactly 2 parameters:
        // {{1}} = Customer name, {{2}} = Service/product name
        
        // Parameter 1: Customer name (prioritize form input, fallback to customer name field)
        const customerNameParam = data.customerName || 'Customer';
        
        // Parameter 2: Service/product from dynamic parameters
        let serviceParam = '';
        if (selectedTemplate?.parameters) {
          // Get the first (and usually only) dynamic parameter as the service name
          const firstParam = selectedTemplate.parameters[0];
          if (firstParam) {
            serviceParam = (data as any)[firstParam.name] || '';
          }
        }
        
        // Only add parameters if we have both
        if (customerNameParam && serviceParam) {
          templateParameters.push({
            type: 'text',
            text: customerNameParam
          });
          templateParameters.push({
            type: 'text',
            text: serviceParam
          });
        }
      } else {
        // For other templates, use the standard parameter mapping
        if (selectedTemplate?.parameters) {
          selectedTemplate.parameters.forEach((param) => {
            const value = (data as any)[param.name];
            if (value) {
              templateParameters.push({
                type: 'text',
                text: value
              });
            }
          });
        }
      }

      const requestData = {
        customer_phone: fullPhoneNumber,
        customer_name: data.customerName || undefined,
        template_name: data.templateName,
        language_code: data.templateLanguage,
        parameters: templateParameters.length > 0 ? templateParameters : undefined,
      };

      const response = await fetch(getApiUrl('messages/template'), {
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
      
      // Show success state briefly
      setShowSuccess(true);
      
      toast.success(
        'Conversation started successfully! Template message sent.'
      );
      
      // Invalidate and refetch conversations list for real-time updates
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: conversationQueryKeys.stats() });
      
      // Wait a moment to show success animation, then close
      setTimeout(() => {
        reset();
        setSelectedTemplateName('');
        setShowSuccess(false);
        onClose();
        
        // Call success callback if provided
        if (onSuccess) {
          onSuccess();
        }
      }, 1000);
    } catch (error) {
      console.error('Error starting conversation:', error);
      toast.error(
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
      setSelectedTemplateName('');
      setSearchQuery('');
      setSelectedCategory('all');
      setShowSuccess(false);
      onClose();
    }
  };

  const handleTemplateSelect = (template: Template) => {
    setSelectedTemplateName(template.name);
    setValue('templateName', template.name);
    setValue('templateLanguage', template.language);
  };

  const getPreviewText = (template: Template) => {
    return template.preview_text || 'No preview available';
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'approved':
        return 'approved';
      case 'pending':
        return 'pending';
      case 'rejected':
        return 'rejected';
      default:
        return 'pending';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className={styles.modalContent}>
        <DialogHeader className={styles.modalHeader}>
          <DialogTitle className={styles.modalTitle}>
            <ChatBubbleLeftIcon className="w-5 h-5" />
            <span>Start New Conversation</span>
          </DialogTitle>
          <DialogDescription className={styles.modalDescription}>
            Enter a customer&apos;s phone number and select a template to start a new WhatsApp conversation.
          </DialogDescription>
          <Button
            variant="ghost"
            size="icon"
            onClick={handleClose}
            className={styles.closeButton}
            disabled={isSubmitting}
          >
            <XMarkIcon className="w-4 h-4" />
          </Button>
        </DialogHeader>

        <div className={styles.modalBody}>
          {/* Phone Number Section */}
          <div className={styles.section}>
            <h3 className={styles.sectionTitle}>
              <PhoneIcon className="w-4 h-4" />
              Customer Contact
            </h3>
            
            <div className={styles.phoneNumberGrid}>
              {/* Country Code */}
              <div>
                <Label htmlFor="countryCode">Country</Label>
                <Select 
                  value={watchedValues.countryCode} 
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
              <div>
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
              </div>
            </div>

            <div className={styles.phonePreview}>
              <strong>Complete number:</strong> {watchedValues.countryCode || '+506'}{watchedValues.phoneNumber || 'XXXXXXXX'}
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
          <div className={styles.templateSection}>
            <h3 className={styles.sectionTitle}>
              <DocumentTextIcon className="w-4 h-4" />
              WhatsApp Message Template
            </h3>
            
            {/* Template Filters */}
            <div className={styles.templateFilters}>
              <div className={styles.searchInput}>
                <Label htmlFor="templateSearch">Search Templates</Label>
                <div className="relative">
                  <MagnifyingGlassIcon className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="templateSearch"
                    placeholder="Search by name or content..."
                    className="pl-10"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>
              
              <div className={styles.categorySelect}>
                <Label htmlFor="categoryFilter">Category</Label>
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    {categories.map((category) => (
                      <SelectItem key={category} value={category}>
                        {category}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Templates Grid */}
            {isLoadingTemplates ? (
              <div className={styles.loadingState}>
                <div className={styles.spinner} />
                <p>Loading templates...</p>
              </div>
            ) : filteredTemplates.length === 0 ? (
              <div className={styles.emptyState}>
                {templates.length === 0 ? (
                  <>
                    <DocumentTextIcon className={styles.emptyIcon} />
                    <h3>No Templates Available</h3>
                    <p>
                      No approved templates found. Please configure WhatsApp templates in your Meta Business account.
                    </p>
                  </>
                ) : (
                  <>
                    <MagnifyingGlassIcon className={styles.emptyIcon} />
                    <h3>No Templates Found</h3>
                    <p>
                      No templates match your search criteria. Try adjusting your search or category filter.
                    </p>
                  </>
                )}
              </div>
            ) : (
              <div className={styles.templatesGrid}>
                {filteredTemplates.map((template) => (
                  <div 
                    key={`${template.name}-${template.language}`}
                    className={`${styles.templateCard} ${selectedTemplateName === template.name ? styles.selected : ''}`}
                    onClick={() => handleTemplateSelect(template)}
                  >
                    <div className={styles.templateHeader}>
                      <div className="flex-1">
                        <h4 className={styles.templateName}>{template.name}</h4>
                        <div className={styles.templateBadges}>
                          <span className={`${styles.templateBadge} ${styles.category}`}>
                            {template.category}
                          </span>
                          <span className={`${styles.templateBadge} ${styles.language}`}>
                            {template.language}
                          </span>
                          <span className={`${styles.templateBadge} ${styles.status} ${styles[getStatusBadgeClass(template.status)]}`}>
                            {template.status}
                          </span>
                        </div>
                      </div>
                      {selectedTemplateName === template.name && (
                        <div className={styles.selectionIndicator}>
                          <CheckIcon className={styles.checkIcon} />
                        </div>
                      )}
                    </div>
                    
                    <div className={styles.templatePreview}>
                      {getPreviewText(template)}
                    </div>
                    
                    {template.parameters && template.parameters.length > 0 && (
                      <div className={styles.templateParameters}>
                        <span style={{ fontSize: '0.7rem', color: 'rgb(var(--muted-foreground))' }}>
                          Parameters: 
                        </span>
                        {template.parameters.map((param) => (
                          <span key={param.name} className={styles.parameterChip}>
                            {param.label}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {errors.templateName && (
              <p className="text-sm text-error">{errors.templateName.message}</p>
            )}
          </div>

          {/* Dynamic Parameters Section */}
          {selectedTemplate?.parameters && selectedTemplate.parameters.length > 0 && (
            <div className={styles.parametersSection}>
              <h3 className={styles.sectionTitle}>
                <SparklesIcon className="w-4 h-4" />
                Template Parameters
              </h3>
              
              {selectedTemplate.parameters.map((param) => (
                <div key={param.name} className={styles.parameterGroup}>
                  <Label htmlFor={param.name} className={styles.parameterLabel}>
                    {param.label}
                    {param.example && (
                      <span className={styles.exampleText}>
                        (e.g., {param.example})
                      </span>
                    )}
                  </Label>
                  <Input
                    id={param.name}
                    placeholder={param.example}
                    {...register(param.name as any)}
                  />
                  {(errors as any)[param.name] && (
                    <p className="text-sm text-error">
                      {(errors as any)[param.name]?.message}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Actions - Always visible at bottom */}
        <div className={styles.actions}>
          <Button
            type="button"
            onClick={handleClose}
            disabled={isSubmitting}
            className={styles.cancelButton}
          >
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSubmit(onSubmit)}
            disabled={isSubmitting || !selectedTemplateName}
            className={`${styles.startButton} ${showSuccess ? styles.success : ''}`}
          >
            {showSuccess ? (
              <>
                <CheckIcon className="w-4 h-4 mr-2" />
                Success!
              </>
            ) : isSubmitting ? (
              <>
                <div className={styles.loadingSpinner} />
                Starting...
              </>
            ) : (
              <>
                <ChatBubbleLeftIcon className="w-4 h-4 mr-2" />
                Start Conversation
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
