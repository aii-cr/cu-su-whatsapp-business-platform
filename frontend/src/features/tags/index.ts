/**
 * Tags feature exports
 * Centralized exports for the tags feature module
 */

// Models and types
export * from './models/tag';

// API client
export * from './api/tagsApi';

// React hooks
export * from './hooks/useTags';
export * from './hooks/useConversationTags';

// UI Components
export { TagChip } from './components/TagChip';
export { TagAutocomplete } from './components/TagAutocomplete';
export { TagList } from './components/TagList';
export { ConversationTagManager } from './components/ConversationTagManager';
export { TagManagement } from './components/TagManagement';

// Re-export commonly used types for convenience
export type {
  Tag,
  TagSummary,
  TagDenormalized,
  ConversationTag,
  TagCreate,
  TagUpdate,
  TagCategoryType,
  TagColorType,
  TagStatusType,
} from './models/tag';
