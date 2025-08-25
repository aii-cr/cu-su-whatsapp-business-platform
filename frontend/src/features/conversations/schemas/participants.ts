import { z } from 'zod';

export const ParticipantRole = z.enum(['primary', 'agent', 'observer']);

export const ParticipantInSchema = z.object({
  user_id: z.string().min(1),
  role: ParticipantRole,
});

export const ParticipantOutSchema = z.object({
  _id: z.string(),
  user_id: z.string(),
  role: ParticipantRole,
  added_at: z.string(),
  removed_at: z.string().nullable().optional(),
});

export type ParticipantRole = z.infer<typeof ParticipantRole>;
export type ParticipantIn = z.infer<typeof ParticipantInSchema>;
export type ParticipantOut = z.infer<typeof ParticipantOutSchema>;


