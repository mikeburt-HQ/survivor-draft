# Survivor 50 Fantasy Draft

Real-time snake draft app for 4 friends to draft Survivor 50 contestants.

## Stack

- Next.js 16 + Tailwind CSS v4
- Supabase (Postgres + Realtime)
- Vercel hosting

## Setup

1. Create a Supabase project
2. Run `supabase/schema.sql` then `supabase/seed.sql` in the SQL Editor
3. Enable Realtime on both `players` and `draft_state` tables (Database → Replication)
4. Copy `.env.local.example` to `.env.local` and fill in your Supabase credentials
5. `npm install && npm run dev`

## How It Works

1. Each player picks their name from the lobby
2. Someone clicks "Randomize Draft Order" to set the snake draft order
3. Click "Start Draft" to begin
4. When it's your turn, click a contestant to draft them
5. Confirm your pick in the modal
6. After 24 picks (6 rounds), the draft is complete

## Reset Draft

To draft again, run this SQL in Supabase:

```sql
UPDATE players SET drafted_by = NULL, draft_pick = NULL;
UPDATE draft_state SET status = 'not_started', current_pick = 0, draft_order = '[]'::jsonb;
```
