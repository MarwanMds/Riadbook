# RiadBook Maroc

A full-stack web platform for searching and booking riads and hotels in Morocco. Built with Django, PostgreSQL, TailwindCSS, and Leaflet.js.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [User Roles](#user-roles)
- [Internationalization](#internationalization)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Running the Project](#running-the-project)
- [Deployment](#deployment)
- [Security](#security)
- [License](#license)

---

## Overview

RiadBook Maroc is a 100% Moroccan booking platform that connects travelers with riads and hotels across Morocco. It provides a digital showcase for traditional Moroccan hospitality, a streamlined 2-step booking process without online payment, and a multilingual interface supporting French, Arabic (RTL), and English.

---

## Features

### For Travelers
- Search by city, dates, number of guests, price range, and property type
- Filter by rating, amenities (Wi-Fi, Spa, Hammam, Pool, Parking, Breakfast), style, and free cancellation
- Complete a booking in under 3 minutes — no payment required online
- Email confirmation with a booking voucher
- Personal dashboard: upcoming stays, past bookings, favorites, reviews, messaging
- Leave verified reviews after a completed stay

### For Hotel and Riad Owners
- Create and manage property listings with photos
- Manage room types, pricing, and cancellation policies
- Availability calendar per room
- Receive and process bookings
- Respond to guest reviews
- Messaging with travelers

### For Administrators
- Back-office dashboard with global statistics
- Validate and moderate property listings
- Moderate reviews and photos
- User management
- Messaging with all users

### Platform
- Interactive map of properties using Leaflet.js
- "Authentic Riad" certification label
- Multilingual: French (default), Arabic (RTL), English
- Responsive design for desktop and mobile
- Email notifications via SMTP

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.x (Python 3.11+) |
| Database | PostgreSQL 14+ |
| Frontend | Django Templates + TailwindCSS |
| Maps | Leaflet.js |
| Authentication | Session-based (secure cookies) |
| Password hashing | bcrypt (BCryptSHA256PasswordHasher) |
| Email | SMTP (Gmail / Mailtrap) |
| Media storage | Local filesystem |
| i18n | Django i18n + gettext |

---

## Project Structure

```
RiadBook/
├── accounts/           # Custom user model, authentication, registration
├── backoffice/         # Admin dashboard, moderation, stats
├── bookings/           # Booking logic, availability, favorites
├── config/             # Django settings, URLs, WSGI, context processors
├── locale/             # Translation files (.po / .mo)
│   ├── fr/LC_MESSAGES/
│   ├── ar/LC_MESSAGES/
│   └── en/LC_MESSAGES/
├── media/              # Uploaded files (photos, avatars)
├── messaging/          # Conversations, messages, notifications
├── owner/              # Owner dashboard, property and room management
├── properties/         # Property, room, city, amenity models and views
│   └── templatetags/   # Custom template tags (translated_name, status_label)
├── public/             # Public pages: home, search, riad showcase
├── reviews/            # Review system with moderation and owner replies
├── static/             # Static assets (CSS, JS, images)
├── templates/          # All HTML templates
│   ├── accounts/
│   ├── backoffice/
│   ├── bookings/
│   ├── messaging/
│   ├── owner/
│   ├── partials/       # navbar, footer
│   ├── properties/
│   ├── public/
│   ├── reviews/
│   └── traveler/
├── traveler/           # Traveler dashboard, reservations, favorites, reviews
├── compile_messages.sh # Script to compile translations
├── manage.py
├── riadbook_schema.sql # Full PostgreSQL schema
├── schema.sql          # Simplified schema
└── seed_data.sql       # Sample data for development
```

---

## Database Schema

The main tables are:

| Table | Description |
|---|---|
| `users` | Custom user model with role (traveler, owner, admin) |
| `cities` | Moroccan cities with multilingual names |
| `properties` | Hotels and riads with type, style, status |
| `amenities` | Tags such as Wi-Fi, Spa, Hammam — with multilingual names |
| `rooms` | Rooms per property with bed type, capacity, price |
| `availability` | Per-room date availability calendar |
| `bookings` | Reservations with status, pricing snapshot, guest details |
| `favorites` | Traveler-saved properties |
| `reviews` | Guest reviews with sub-ratings and moderation status |
| `owner_replies` | Owner public responses to reviews |
| `conversations` | Message threads between users |
| `messages` | Individual messages within a conversation |
| `notifications` | In-app notifications for key events |
| `property_photos` | Photos per property |
| `room_photos` | Photos per room |

The full schema is available in `riadbook_schema.sql`.

---

## User Roles

The platform defines three roles with distinct permissions:

**Traveler** — registers with email, searches and books properties, manages reservations, leaves reviews, uses messaging and favorites.

**Owner** — validated professional account, manages property listings and rooms, handles availability calendar, receives and processes bookings, responds to reviews.

**Admin** — full back-office access, validates listings, moderates reviews and photos, views global statistics, manages users, handles all messaging.

---

## Internationalization

The platform supports three languages:

| Code | Language | Direction |
|---|---|---|
| `fr` | Français | LTR (default) |
| `ar` | Arabic | RTL |
| `en` | English | LTR |

### How it works

- `LocaleMiddleware` detects the active language from the session cookie `django_language`
- The language is stored per-user session and persists across pages
- RTL layout is applied automatically when Arabic is active via the `html_direction` context processor
- All model `TextChoices` labels use `gettext_lazy` for runtime translation
- City and amenity names stored in the database have `name_ar` and `name_en` fields; the custom template tag `translated_name` returns the correct one based on the active language

### Switching language

The language switcher is in the navbar on every page. Selecting a language posts to `/i18n/set_language/` and redirects back to the current page.

### Adding or modifying translations

Edit the `.po` files in `locale/fr/`, `locale/ar/`, or `locale/en/`, then compile:

```bash
./compile_messages.sh
```

To extract new strings from templates and Python files:

```bash
./compile_messages.sh --update
```

See `TRANSLATIONS.md` for the full translation guide.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- pip
- gettext (for compiling translations)

On Ubuntu/Debian:
```bash
sudo apt install python3 python3-pip postgresql gettext
```

On macOS with Homebrew:
```bash
brew install python postgresql gettext
```

### Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/riadbook-maroc.git
cd riadbook-maroc
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate       # Linux / macOS
.venv\Scripts\activate          # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create the PostgreSQL database:

```bash
psql -U postgres -c "CREATE DATABASE riadbook;"
```

5. Copy and configure the environment file:

```bash
cp .env.example .env
# Edit .env with your database credentials and secret key
```

6. Apply migrations:

```bash
python manage.py migrate
```

7. Compile translations:

```bash
./compile_messages.sh
# or on Windows:
python manage.py compilemessages
```

8. Load sample data (optional):

```bash
psql -U postgres -d riadbook -f seed_data.sql
```

9. Create a superuser:

```bash
python manage.py createsuperuser
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `dev-secret-change-in-production` | Django secret key — change in production |
| `DEBUG` | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | `localhost 127.0.0.1` | Space-separated list of allowed hosts |
| `DB_NAME` | `riadbook` | PostgreSQL database name |
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `0000` | PostgreSQL password |
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port |
| `EMAIL_BACKEND` | `console` | Use `smtp` in production |
| `EMAIL_HOST` | `smtp.gmail.com` | SMTP server |
| `EMAIL_PORT` | `587` | SMTP port |
| `EMAIL_HOST_USER` | — | SMTP login email |
| `EMAIL_HOST_PASSWORD` | — | SMTP password or app password |
| `SITE_URL` | `https://www.riadbook.ma` | Base URL used in email links |

---

## Running the Project

```bash
python manage.py runserver
```

The application is available at `http://127.0.0.1:8000`.

### URL map

| Path | Description |
|---|---|
| `/` | Home page |
| `/search/` | Search results with map |
| `/riads/` | Riad showcase |
| `/property/<slug>/` | Property detail page |
| `/book/<room_id>/` | Booking form |
| `/accounts/register/` | Traveler or owner registration |
| `/accounts/login/` | Login |
| `/dashboard/` | Traveler dashboard |
| `/owner/` | Owner dashboard |
| `/admin-dashboard/` | Admin back-office |
| `/django-admin/` | Django admin panel |

---

## Deployment

### Production checklist

1. Set `DEBUG=False` in your environment.

2. Set a strong `DJANGO_SECRET_KEY`.

3. Add your domain to `ALLOWED_HOSTS`.

4. Collect static files:

```bash
python manage.py collectstatic
```

5. Enable HTTPS — the application enforces `SECURE_REFERRER_POLICY` and secure session cookies. Add these to your settings for full HTTPS enforcement:

```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

6. Configure a production SMTP provider for emails.

7. Set up daily automated database backups.

8. Use a process manager such as Gunicorn with Nginx as reverse proxy:

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Recommended stack

- Server: Ubuntu 22.04
- Web server: Nginx
- Application server: Gunicorn
- Database: PostgreSQL 14+ (managed or self-hosted)
- SSL: Let's Encrypt via Certbot
- Media storage: local or S3-compatible (for scale)

---

## Security

- Passwords hashed with bcrypt (`BCryptSHA256PasswordHasher`)
- All database queries use Django ORM — no raw SQL injection vectors
- CSRF protection enabled on all forms
- Session cookies are HttpOnly and SameSite=Lax
- HTTPS enforced in production
- Compliant with Moroccan law n°09-08 on personal data protection and GDPR principles
- Admin routes protected by role-based access control

---

## License

This project is proprietary software developed for RiadBook Maroc.
All rights reserved. 2026.