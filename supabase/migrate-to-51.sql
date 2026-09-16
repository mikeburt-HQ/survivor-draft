-- Migrate an existing Survivor 50 draft database to Survivor 51.
-- Run this ONCE in the Supabase SQL Editor. It replaces the cast entirely and
-- clears any previous draft, so only run it when you are done with Survivor 50.
--
-- For a brand new Supabase project, use schema.sql + seed.sql instead.

BEGIN;

-- 1. Cast members now carry a hometown, and tribe is unknown until the premiere.
ALTER TABLE players ADD COLUMN IF NOT EXISTS hometown TEXT;
ALTER TABLE players ALTER COLUMN tribe DROP NOT NULL;

-- 2. Clear the Survivor 50 cast and any picks made against it.
DELETE FROM players;

-- 3. Survivor 51 cast, announced by CBS in August 2026. Premiere 2026-09-23.
--    Tribes are NULL because CBS has not released the split yet.
--    Note: ADD COLUMN appends, so `hometown` ends up LAST here while
--    schema.sql puts it 3rd. Semantically identical (same type, same
--    nullability) and harmless because every INSERT names its columns.
INSERT INTO players (id, name, hometown, tribe) VALUES
(1,  'Rob Antonson',            'Cumberland, Rhode Island',      NULL),
(2,  'Brady Booker',            'Knoxville, Tennessee',          NULL),
(3,  'Patt Cannaday',           'Washington, D.C.',              NULL),
(4,  'Linnea Capobianco',       'Jersey City, New Jersey',       NULL),
(5,  'Cristian Chavez',         'Salt Lake City, Utah',          NULL),
(6,  'Sharonda Cox',            'Richmond, Kentucky',            NULL),
(7,  'Jenna Doore',             'Toledo, Ohio',                  NULL),
(8,  'Kristin Flickinger',      'Santa Barbara, California',     NULL),
(9,  'Ori Jean-Charles',        'Spring Valley, New York',       NULL),
(10, 'Lewis Kelly',             'Corozal, Puerto Rico',          NULL),
(11, 'Danny Kilby',             'London, Ontario',               NULL),
(12, 'Carter Krull',            'Sioux Falls, South Dakota',     NULL),
(13, 'Alexis Levine',           'Atlanta, Georgia',              NULL),
(14, 'Angelica "Jelly" Loblack','Bloomington, Indiana',          NULL),
(15, 'Eric Macksoud',           'Windsor Locks, Connecticut',    NULL),
(16, 'Maggie Nestor',           'Charles Town, West Virginia',   NULL),
(17, 'Thien An Nguyen',         'Fort Worth, Texas',             NULL),
(18, 'Mike Pinsky',             'New York City, New York',       NULL),
(19, 'Aaliyah Puglia',          'Providence, Rhode Island',      NULL),
(20, 'Ana Sani',                'Toronto, Ontario',              NULL),
(21, 'Devin Way',               'Los Angeles, California',       NULL);

-- 4. Now that every row has one, make hometown required.
ALTER TABLE players ALTER COLUMN hometown SET NOT NULL;

-- 5. Reset the draft itself.
UPDATE draft_state
SET status = 'not_started', current_pick = 0, draft_order = '[]'::jsonb
WHERE id = 1;

COMMIT;

-- Sanity check — expect 21 castaways, 0 drafted:
--   SELECT count(*) AS cast_size,
--          count(drafted_by) AS drafted
--   FROM players;
