-- =============================================================================
-- RiadBook Maroc — PostgreSQL Database Schema
-- Version: 1.0 | Generated from Django models
-- =============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";  -- for accent-insensitive search

-- =============================================================================
-- TABLE: users
-- Custom user model with role-based access control
-- =============================================================================
CREATE TABLE users (
    id                       BIGSERIAL PRIMARY KEY,
    email                    VARCHAR(254)  NOT NULL UNIQUE,
    password                 VARCHAR(128)  NOT NULL,              -- bcrypt hash
    first_name               VARCHAR(100)  NOT NULL,
    last_name                VARCHAR(100)  NOT NULL,
    phone                    VARCHAR(20)   NOT NULL DEFAULT '',
    avatar                   VARCHAR(100),                        -- file path
    role                     VARCHAR(10)   NOT NULL DEFAULT 'traveler'
                                 CHECK (role IN ('traveler','owner','admin')),
    preferred_language       VARCHAR(2)    NOT NULL DEFAULT 'fr'
                                 CHECK (preferred_language IN ('fr','ar','en')),
    is_active                BOOLEAN       NOT NULL DEFAULT TRUE,
    is_staff                 BOOLEAN       NOT NULL DEFAULT FALSE,
    is_superuser             BOOLEAN       NOT NULL DEFAULT FALSE,
    is_email_verified        BOOLEAN       NOT NULL DEFAULT FALSE,
    email_verification_token VARCHAR(64)   NOT NULL DEFAULT '',
    date_joined              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    last_login               TIMESTAMPTZ
);

CREATE INDEX idx_users_role    ON users(role);
CREATE INDEX idx_users_email   ON users(email);


-- =============================================================================
-- TABLE: cities
-- Moroccan cities covered by the platform
-- =============================================================================
CREATE TABLE cities (
    id         BIGSERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    name_ar    VARCHAR(100) NOT NULL DEFAULT '',
    name_en    VARCHAR(100) NOT NULL DEFAULT '',
    slug       VARCHAR(110) NOT NULL UNIQUE,
    latitude   NUMERIC(9,6) NOT NULL,
    longitude  NUMERIC(9,6) NOT NULL,
    is_active  BOOLEAN      NOT NULL DEFAULT TRUE,
    image      VARCHAR(100)                        -- cover photo path
);


-- =============================================================================
-- TABLE: amenities
-- Reusable tags: WiFi, Piscine, Spa, Hammam, Parking, Petit-déjeuner…
-- =============================================================================
CREATE TABLE amenities (
    id       BIGSERIAL PRIMARY KEY,
    name     VARCHAR(80)  NOT NULL UNIQUE,
    name_ar  VARCHAR(80)  NOT NULL DEFAULT '',
    name_en  VARCHAR(80)  NOT NULL DEFAULT '',
    icon     VARCHAR(50)  NOT NULL DEFAULT ''   -- CSS icon class
);


-- =============================================================================
-- TABLE: properties
-- Riads, Hotels, and Guest Houses
-- =============================================================================
CREATE TABLE properties (
    id                BIGSERIAL PRIMARY KEY,
    owner_id          BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    city_id           BIGINT       NOT NULL REFERENCES cities(id) ON DELETE RESTRICT,
    name              VARCHAR(200) NOT NULL,
    slug              VARCHAR(220) NOT NULL UNIQUE,
    description       TEXT         NOT NULL,
    description_ar    TEXT         NOT NULL DEFAULT '',
    description_en    TEXT         NOT NULL DEFAULT '',
    property_type     VARCHAR(15)  NOT NULL
                          CHECK (property_type IN ('hotel','riad','guesthouse')),
    style             VARCHAR(15)  NOT NULL DEFAULT 'traditional'
                          CHECK (style IN ('traditional','modern','luxury','budget')),
    address           VARCHAR(300) NOT NULL,
    latitude          NUMERIC(9,6),
    longitude         NUMERIC(9,6),
    is_authentic_riad BOOLEAN      NOT NULL DEFAULT FALSE,
    free_cancellation BOOLEAN      NOT NULL DEFAULT FALSE,
    status            VARCHAR(12)  NOT NULL DEFAULT 'pending'
                          CHECK (status IN ('pending','approved','rejected','suspended')),
    avg_rating        NUMERIC(3,2) NOT NULL DEFAULT 0,   -- cached, updated by trigger
    review_count      INTEGER      NOT NULL DEFAULT 0,   -- cached, updated by trigger
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_properties_owner       ON properties(owner_id);
CREATE INDEX idx_properties_city_type   ON properties(city_id, property_type);
CREATE INDEX idx_properties_status      ON properties(status);
CREATE INDEX idx_properties_avg_rating  ON properties(avg_rating DESC);
CREATE INDEX idx_properties_location    ON properties(latitude, longitude);


-- =============================================================================
-- TABLE: property_amenities  (M2M join)
-- =============================================================================
CREATE TABLE property_amenities (
    property_id  BIGINT NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    amenity_id   BIGINT NOT NULL REFERENCES amenities(id)  ON DELETE CASCADE,
    PRIMARY KEY (property_id, amenity_id)
);


-- =============================================================================
-- TABLE: property_photos
-- =============================================================================
CREATE TABLE property_photos (
    id          BIGSERIAL PRIMARY KEY,
    property_id BIGINT       NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    image       VARCHAR(200) NOT NULL,                -- relative file path
    caption     VARCHAR(200) NOT NULL DEFAULT '',
    is_cover    BOOLEAN      NOT NULL DEFAULT FALSE,
    "order"     SMALLINT     NOT NULL DEFAULT 0,
    is_approved BOOLEAN      NOT NULL DEFAULT TRUE,
    uploaded_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_property_photos_property ON property_photos(property_id, "order");


-- =============================================================================
-- TABLE: rooms
-- Individual room types within a property
-- =============================================================================
CREATE TABLE rooms (
    id                    BIGSERIAL PRIMARY KEY,
    property_id           BIGINT       NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    name                  VARCHAR(150) NOT NULL,
    description           TEXT         NOT NULL DEFAULT '',
    bed_type              VARCHAR(10)  NOT NULL DEFAULT 'double'
                              CHECK (bed_type IN ('single','double','twin','suite','dorm')),
    capacity              SMALLINT     NOT NULL DEFAULT 2 CHECK (capacity >= 1),
    price_per_night       NUMERIC(8,2) NOT NULL CHECK (price_per_night >= 0),
    free_cancellation     BOOLEAN      NOT NULL DEFAULT FALSE,
    cancellation_deadline SMALLINT     NOT NULL DEFAULT 0,  -- hours before check-in
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_rooms_property ON rooms(property_id);
CREATE INDEX idx_rooms_price    ON rooms(price_per_night);


-- =============================================================================
-- TABLE: room_photos
-- =============================================================================
CREATE TABLE room_photos (
    id      BIGSERIAL PRIMARY KEY,
    room_id BIGINT       NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    image   VARCHAR(200) NOT NULL,
    "order" SMALLINT     NOT NULL DEFAULT 0
);


-- =============================================================================
-- TABLE: availability
-- Per-room, per-day availability calendar
-- Missing rows = available. Present with is_available=FALSE = blocked.
-- =============================================================================
CREATE TABLE availability (
    id           BIGSERIAL PRIMARY KEY,
    room_id      BIGINT  NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    date         DATE    NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    note         VARCHAR(100) NOT NULL DEFAULT '',
    UNIQUE (room_id, date)
);

CREATE INDEX idx_availability_room_date ON availability(room_id, date);


-- =============================================================================
-- TABLE: bookings
-- =============================================================================
CREATE TABLE bookings (
    id                  BIGSERIAL PRIMARY KEY,
    reference           VARCHAR(12)  NOT NULL UNIQUE,           -- e.g. RB3F9A1C2D
    traveler_id         BIGINT       NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    room_id             BIGINT       NOT NULL REFERENCES rooms(id) ON DELETE RESTRICT,
    check_in            DATE         NOT NULL,
    check_out           DATE         NOT NULL,
    num_nights          SMALLINT     NOT NULL,
    num_adults          SMALLINT     NOT NULL DEFAULT 1 CHECK (num_adults >= 1),
    num_children        SMALLINT     NOT NULL DEFAULT 0,
    -- Pricing snapshot
    price_per_night     NUMERIC(8,2) NOT NULL,
    total_price         NUMERIC(10,2) NOT NULL,
    taxes               NUMERIC(8,2)  NOT NULL DEFAULT 0,
    grand_total         NUMERIC(10,2) NOT NULL,
    -- Guest snapshot (in case user changes their profile)
    guest_first_name    VARCHAR(100) NOT NULL,
    guest_last_name     VARCHAR(100) NOT NULL,
    guest_email         VARCHAR(254) NOT NULL,
    guest_phone         VARCHAR(20)  NOT NULL DEFAULT '',
    special_requests    TEXT         NOT NULL DEFAULT '',
    -- Status
    status              VARCHAR(12)  NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending','confirmed','cancelled','completed','no_show')),
    cancellation_reason TEXT         NOT NULL DEFAULT '',
    cancelled_at        TIMESTAMPTZ,
    cancelled_by_id     BIGINT       REFERENCES users(id) ON DELETE SET NULL,
    -- Email tracking
    confirmation_sent   BOOLEAN      NOT NULL DEFAULT FALSE,
    voucher_sent        BOOLEAN      NOT NULL DEFAULT FALSE,
    -- Timestamps
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    -- Constraints
    CONSTRAINT chk_dates CHECK (check_out > check_in)
);

CREATE INDEX idx_bookings_traveler_status ON bookings(traveler_id, status);
CREATE INDEX idx_bookings_room_dates      ON bookings(room_id, check_in, check_out);
CREATE INDEX idx_bookings_reference       ON bookings(reference);
CREATE INDEX idx_bookings_status          ON bookings(status);


-- =============================================================================
-- TABLE: favorites
-- Traveler's saved properties
-- =============================================================================
CREATE TABLE favorites (
    id          BIGSERIAL PRIMARY KEY,
    traveler_id BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    property_id BIGINT      NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (traveler_id, property_id)
);


-- =============================================================================
-- TABLE: reviews
-- =============================================================================
CREATE TABLE reviews (
    id                  BIGSERIAL PRIMARY KEY,
    property_id         BIGINT      NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    author_id           BIGINT      NOT NULL REFERENCES users(id)      ON DELETE CASCADE,
    booking_id          BIGINT      UNIQUE REFERENCES bookings(id)     ON DELETE SET NULL,
    -- Ratings
    rating_overall      SMALLINT    NOT NULL CHECK (rating_overall    BETWEEN 1 AND 5),
    rating_cleanliness  SMALLINT             CHECK (rating_cleanliness BETWEEN 1 AND 5),
    rating_location     SMALLINT             CHECK (rating_location    BETWEEN 1 AND 5),
    rating_value        SMALLINT             CHECK (rating_value       BETWEEN 1 AND 5),
    rating_service      SMALLINT             CHECK (rating_service     BETWEEN 1 AND 5),
    -- Content
    title       VARCHAR(150) NOT NULL DEFAULT '',
    comment     TEXT         NOT NULL,
    -- Verification
    is_verified BOOLEAN      NOT NULL DEFAULT FALSE,
    status      VARCHAR(10)  NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','approved','rejected')),
    moderation_note TEXT     NOT NULL DEFAULT '',
    -- Timestamps
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    -- One review per property per user
    UNIQUE (property_id, author_id)
);

CREATE INDEX idx_reviews_property_status ON reviews(property_id, status);
CREATE INDEX idx_reviews_author          ON reviews(author_id);


-- =============================================================================
-- TABLE: owner_replies
-- Hotel owner's public response to a review
-- =============================================================================
CREATE TABLE owner_replies (
    id         BIGSERIAL PRIMARY KEY,
    review_id  BIGINT      NOT NULL UNIQUE REFERENCES reviews(id) ON DELETE CASCADE,
    author_id  BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    comment    TEXT        NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- =============================================================================
-- TABLE: conversations
-- Message threads between traveler and admin
-- =============================================================================
CREATE TABLE conversations (
    id                   BIGSERIAL PRIMARY KEY,
    traveler_id          BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    property_id          BIGINT       REFERENCES properties(id) ON DELETE SET NULL,
    subject              VARCHAR(200) NOT NULL,
    status               VARCHAR(10)  NOT NULL DEFAULT 'open'
                             CHECK (status IN ('open','closed','pending')),
    last_message_at      TIMESTAMPTZ,
    unread_by_admin      SMALLINT     NOT NULL DEFAULT 0,
    unread_by_traveler   SMALLINT     NOT NULL DEFAULT 0,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_traveler ON conversations(traveler_id);
CREATE INDEX idx_conversations_last_msg ON conversations(last_message_at DESC);


-- =============================================================================
-- TABLE: messages
-- Individual messages within a conversation
-- =============================================================================
CREATE TABLE messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT       NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id       BIGINT       REFERENCES users(id) ON DELETE SET NULL,
    sender_type     VARCHAR(10)  NOT NULL CHECK (sender_type IN ('traveler','admin')),
    body            TEXT         NOT NULL,
    is_read         BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);


-- =============================================================================
-- TABLE: notifications
-- In-app notification feed per user
-- =============================================================================
CREATE TABLE notifications (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT       NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notif_type  VARCHAR(25)  NOT NULL,
    title       VARCHAR(150) NOT NULL,
    body        TEXT         NOT NULL DEFAULT '',
    link        VARCHAR(300) NOT NULL DEFAULT '',
    is_read     BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX idx_notifications_created   ON notifications(created_at DESC);


-- =============================================================================
-- TRIGGER: auto-update properties.avg_rating and review_count on review changes
-- =============================================================================
CREATE OR REPLACE FUNCTION update_property_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE properties
    SET
        avg_rating   = COALESCE((
            SELECT ROUND(AVG(rating_overall)::NUMERIC, 2)
            FROM reviews
            WHERE property_id = COALESCE(NEW.property_id, OLD.property_id)
              AND status = 'approved'
        ), 0),
        review_count = (
            SELECT COUNT(*)
            FROM reviews
            WHERE property_id = COALESCE(NEW.property_id, OLD.property_id)
              AND status = 'approved'
        )
    WHERE id = COALESCE(NEW.property_id, OLD.property_id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_property_rating
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_property_rating();


-- =============================================================================
-- TRIGGER: auto-block availability dates on booking confirmation
-- =============================================================================
CREATE OR REPLACE FUNCTION sync_availability_on_booking()
RETURNS TRIGGER AS $$
DECLARE
    d DATE;
BEGIN
    -- When a booking is confirmed: block all dates in range
    IF NEW.status = 'confirmed' AND (OLD.status IS NULL OR OLD.status <> 'confirmed') THEN
        d := NEW.check_in;
        WHILE d < NEW.check_out LOOP
            INSERT INTO availability (room_id, date, is_available, note)
            VALUES (NEW.room_id, d, FALSE, 'Booking ' || NEW.reference)
            ON CONFLICT (room_id, date) DO UPDATE SET is_available = FALSE, note = EXCLUDED.note;
            d := d + INTERVAL '1 day';
        END LOOP;
    END IF;
    -- When a booking is cancelled: restore availability
    IF NEW.status = 'cancelled' AND OLD.status = 'confirmed' THEN
        DELETE FROM availability
        WHERE room_id = NEW.room_id AND date >= NEW.check_in AND date < NEW.check_out;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_availability
AFTER INSERT OR UPDATE OF status ON bookings
FOR EACH ROW EXECUTE FUNCTION sync_availability_on_booking();


-- =============================================================================
-- SEED DATA: Moroccan cities
-- =============================================================================
INSERT INTO cities (name, name_ar, name_en, slug, latitude, longitude) VALUES
    ('Marrakech',   'مراكش',     'Marrakech',   'marrakech',   31.628674, -7.992047),
    ('Fès',         'فاس',       'Fez',         'fes',         34.033333,  5.000000),
    ('Casablanca',  'الدار البيضاء', 'Casablanca', 'casablanca', 33.589886, -7.603869),
    ('Chefchaouen', 'شفشاون',    'Chefchaouen', 'chefchaouen', 35.168612, -5.269420),
    ('Agadir',      'أكادير',    'Agadir',      'agadir',      30.420000, -9.598106),
    ('Essaouira',   'الصويرة',   'Essaouira',   'essaouira',   31.513000, -9.770000),
    ('Rabat',       'الرباط',    'Rabat',       'rabat',       33.988610, -6.854167),
    ('Tanger',      'طنجة',      'Tangier',     'tanger',      35.780000, -5.810000),
    ('Meknès',      'مكناس',     'Meknes',      'meknes',      33.895000, -5.547000),
    ('Ouarzazate',  'ورزازات',   'Ouarzazate',  'ouarzazate',  30.920000, -6.893000);

-- =============================================================================
-- SEED DATA: Amenities
-- =============================================================================
INSERT INTO amenities (name, name_ar, name_en, icon) VALUES
    ('Wi-Fi',              'واي فاي',           'Wi-Fi',             'icon-wifi'),
    ('Piscine',            'حمام السباحة',       'Swimming Pool',     'icon-pool'),
    ('Spa',                'سبا',               'Spa',               'icon-spa'),
    ('Hammam',             'حمام',              'Hammam',            'icon-hammam'),
    ('Parking',            'موقف السيارات',      'Parking',           'icon-parking'),
    ('Petit-déjeuner',     'إفطار',             'Breakfast',         'icon-breakfast'),
    ('Climatisation',      'تكييف الهواء',       'Air Conditioning',  'icon-ac'),
    ('Restaurant',         'مطعم',              'Restaurant',        'icon-restaurant'),
    ('Terrasse',           'تراس',              'Terrace',           'icon-terrace'),
    ('Transfert aéroport', 'نقل المطار',         'Airport Transfer',  'icon-transfer');
