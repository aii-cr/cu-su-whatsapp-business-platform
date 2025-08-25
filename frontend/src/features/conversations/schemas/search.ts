import { z } from 'zod';

export const SearchFiltersSchema = z.object({
  q: z.string().optional(),
  status: z.array(z.string()).optional(),
  tags: z.array(z.string()).optional(),
  agent_ids: z.array(z.string()).optional(),
  date_from: z.string().optional(),
  date_to: z.string().optional(),
  cursor: z.string().optional(),
  limit: z.number().min(1).max(100).optional(),
});

export type SearchFilters = z.infer<typeof SearchFiltersSchema>;


