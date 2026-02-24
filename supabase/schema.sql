CREATE TABLE players (
  id INT PRIMARY KEY,
  name TEXT NOT NULL,
  tribe TEXT NOT NULL,
  drafted_by TEXT,
  draft_pick INT
);

CREATE TABLE draft_state (
  id INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  draft_order JSONB NOT NULL DEFAULT '[]'::jsonb,
  current_pick INT NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started', 'in_progress', 'complete'))
);

ALTER TABLE players ENABLE ROW LEVEL SECURITY;
ALTER TABLE draft_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow all access to players" ON players FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to draft_state" ON draft_state FOR ALL USING (true) WITH CHECK (true);
