# Survivor 51 Fantasy Draft

Real-time snake draft app for 4 friends to draft Survivor 51 contestants.

## Stack

- Next.js 16 + Tailwind CSS v4
- Supabase (Postgres + Realtime)
- Vercel hosting

## Setup

1. Create a Supabase project
2. Run `supabase/schema.sql` then `supabase/seed.sql` in the SQL Editor
3. Enable Realtime on both `players` and `draft_state` tables (Database → Replication)
4. Create `.env.local` with your Supabase credentials:
   `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. `npm install && npm run dev`

## How It Works

1. Each player picks their name from the lobby
2. Someone clicks "Randomize Draft Order" to set the snake draft order
3. Click "Start Draft" to begin
4. When it's your turn, click a contestant to draft them
5. Confirm your pick in the modal
6. After 20 picks (5 rounds), the draft is complete

## Draft Math

Survivor 51 has **21 castaways** and there are **4 drafters**, which does not
divide evenly. The draft runs a fixed **5 rounds of 4 = 20 picks**, so everyone
gets exactly 5 castaways and **one castaway goes undrafted**.

These live in `src/lib/types.ts`. `TOTAL_ROUNDS` is declared (not derived from
`TOTAL_PLAYERS / TOTAL_DRAFTERS`), and draft completion is checked against
`TOTAL_PICKS`, never `TOTAL_PLAYERS`.

## Tribes

CBS confirmed Survivor 51 starts with two tribes (purple and yellow) but has not
released who is on which tribe. Every castaway is seeded with `tribe = NULL`, and
the app shows a single flat cast list with hometowns.

Once the split is announced, assign tribes and the grouped-by-tribe view appears
automatically — no code change needed:

```sql
UPDATE players SET tribe = 'Purple' WHERE id IN (1, 2, 3);
UPDATE players SET tribe = 'Yellow' WHERE id IN (4, 5, 6);
```

Real tribes have proper names, so you can also use the Survivor 50 style —
`'Vatu (Purple)'`. `getTribeColor()` in `src/lib/types.ts` matches the color word
anywhere in the label, case-insensitively, and falls back to neutral gray for a
tribe it has no color for.

**Reload every open browser tab after changing the cast or tribes.** Picks are
made against the roster the tab loaded.

## Reset Draft

To draft again, run this SQL in Supabase (then reload open tabs):

```sql
UPDATE players SET drafted_by = NULL, draft_pick = NULL;
UPDATE draft_state SET status = 'not_started', current_pick = 0, draft_order = '[]'::jsonb;
```

## Tests

```bash
npx jest        # draft logic
npx tsc --noEmit
npm run lint
```
