-- =============================================================================
-- RiadBook Maroc — Seed Data Only (run after schema.sql)
-- =============================================================================

-- Cities
INSERT INTO cities (name, name_ar, name_en, slug, latitude, longitude) VALUES
    ('Marrakech',   'مراكش',         'Marrakech',   'marrakech',   31.628674, -7.992047),
    ('Fès',         'فاس',           'Fez',         'fes',         34.033333, -5.000000),
    ('Casablanca',  'الدار البيضاء', 'Casablanca',  'casablanca',  33.589886, -7.603869),
    ('Chefchaouen', 'شفشاون',        'Chefchaouen', 'chefchaouen', 35.168612, -5.269420),
    ('Agadir',      'أكادير',        'Agadir',      'agadir',      30.420000, -9.598106),
    ('Essaouira',   'الصويرة',       'Essaouira',   'essaouira',   31.513000, -9.770000),
    ('Rabat',       'الرباط',        'Rabat',       'rabat',       33.988610, -6.854167),
    ('Tanger',      'طنجة',          'Tangier',     'tanger',      35.780000, -5.810000),
    ('Meknès',      'مكناس',         'Meknes',      'meknes',      33.895000, -5.547000),
    ('Ouarzazate',  'ورزازات',       'Ouarzazate',  'ouarzazate',  30.920000, -6.893000);

-- Amenities
INSERT INTO amenities (name, name_ar, name_en, icon) VALUES
    ('Wi-Fi',              'واي فاي',        'Wi-Fi',            'icon-wifi'),
    ('Piscine',            'حمام السباحة',    'Swimming Pool',    'icon-pool'),
    ('Spa',                'سبا',            'Spa',              'icon-spa'),
    ('Hammam',             'حمام',           'Hammam',           'icon-hammam'),
    ('Parking',            'موقف السيارات',   'Parking',          'icon-parking'),
    ('Petit-déjeuner',     'إفطار',          'Breakfast',        'icon-breakfast'),
    ('Climatisation',      'تكييف الهواء',    'Air Conditioning', 'icon-ac'),
    ('Restaurant',         'مطعم',           'Restaurant',       'icon-restaurant'),
    ('Terrasse',           'تراس',           'Terrace',          'icon-terrace'),
    ('Transfert aéroport', 'نقل المطار',      'Airport Transfer', 'icon-transfer');

SELECT 'Cities inserted: ' || COUNT(*) FROM cities;
SELECT 'Amenities inserted: ' || COUNT(*) FROM amenities;
