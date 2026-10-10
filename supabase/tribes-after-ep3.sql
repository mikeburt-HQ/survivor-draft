-- Survivor 51 tribes as of the end of episode 3 (aired 2026-10-07).
-- Idempotent: safe whether or not tribes were set before.
-- Carter Krull moved Savu -> Toka in episode 3.
-- Names are exactly as stored in players.name.

UPDATE players SET tribe = 'Savu (Purple)' WHERE name IN (
  'Alexis Levine',
  'Ana Sani',
  'Cristian Chavez',
  'Eric Macksoud',
  'Kristin Flickinger',
  'Linnea Capobianco',
  'Ori Jean-Charles',
  'Rob Antonson',
  'Sharonda Cox'
);  -- 9 rows

UPDATE players SET tribe = 'Toka (Yellow)' WHERE name IN (
  'Aaliyah Puglia',
  'Angelica "Jelly" Loblack',
  'Brady Booker',
  'Carter Krull',
  'Danny Kilby',
  'Devin Way',
  'Jenna Doore',
  'Lewis Kelly',
  'Maggie Nestor',
  'Mike Pinsky',
  'Patt Cannaday',
  'Thien An Nguyen'
);  -- 12 rows
