INSERT INTO draft_state (id, draft_order, current_pick, status)
VALUES (1, '[]'::jsonb, 0, 'not_started');

-- Survivor 51 cast, announced by CBS in August 2026. Premiere 2026-09-23.
-- (Sources disagree on the exact announcement day, 08-25 vs 08-26.)
-- Two starting tribes (purple and yellow) are confirmed, but CBS has not
-- released who is on which tribe, so `tribe` is NULL for everyone. To fill it
-- in later, run e.g.:
--   UPDATE players SET tribe = 'Purple' WHERE id IN (1, 2, 3, ...);
--   UPDATE players SET tribe = 'Yellow' WHERE id IN (4, 5, 6, ...);
-- The app groups by tribe automatically once those values are set.
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
(14, 'Angelica "Jelly" Loblack', 'Bloomington, Indiana',         NULL),
(15, 'Eric Macksoud',           'Windsor Locks, Connecticut',    NULL),
(16, 'Maggie Nestor',           'Charles Town, West Virginia',   NULL),
(17, 'Thien An Nguyen',         'Fort Worth, Texas',             NULL),
(18, 'Mike Pinsky',             'New York City, New York',       NULL),
(19, 'Aaliyah Puglia',          'Providence, Rhode Island',      NULL),
(20, 'Ana Sani',                'Toronto, Ontario',              NULL),
(21, 'Devin Way',               'Los Angeles, California',       NULL);
