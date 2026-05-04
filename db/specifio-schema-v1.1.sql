-- ============================================================================
-- SPECIFIO SCHEMA v1.1
-- Locked: 2026-05-03 (Sessions 1-3)
-- PostgreSQL 15+
-- 11 tables, 44 product fields
-- Ready for: psql -f specifio-schema-v1.1.sql
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "citext";     -- case-insensitive email

-- ============================================================================
-- 1. MANUFACTURERS
-- ============================================================================
CREATE TABLE manufacturers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(200) NOT NULL,
  slug VARCHAR(200) NOT NULL UNIQUE,
  country CHAR(2) NOT NULL,                  -- ISO 3166-1 alpha-2
  city VARCHAR(100),
  website VARCHAR(500),
  logo_url VARCHAR(500),
  description TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE manufacturers IS 'Phase 0a: SSP, MJ, Ornam only. Phase 0b: external manufacturers onboard.';

-- ============================================================================
-- 2. PRODUCTS (44 fields)
-- ============================================================================
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  manufacturer_id UUID NOT NULL REFERENCES manufacturers(id) ON DELETE CASCADE,

  -- IDENTITY
  sku VARCHAR(50) NOT NULL UNIQUE,           -- Required. Bespoke format: SSP-BF-001
  name VARCHAR(300) NOT NULL,
  slug VARCHAR(300) NOT NULL UNIQUE,          -- URL-safe
  category VARCHAR(50) NOT NULL,              -- App-layer validated, not ENUM
    -- Valid: wallcovering, surface_panel, acoustic_panel, ceiling_tile,
    -- ceiling_system, textile, mural, decorative_paint, liquid_metal,
    -- bespoke_finish, decorative_mesh, composite_surface
  subcategory VARCHAR(100),                   -- Free text refinement

  -- DESCRIPTION
  short_description VARCHAR(500) NOT NULL,    -- 1-2 sentences, specifier-facing
  long_description TEXT,

  -- MATERIAL
  primary_material VARCHAR(100) NOT NULL,
  secondary_material VARCHAR(100),
  finish_type VARCHAR(50),                    -- matte, satin, gloss, textured, raw, patinated
  colorway_name VARCHAR(100),
  colorway_count INTEGER,
  custom_colorway BOOLEAN DEFAULT FALSE,

  -- DIMENSIONS
  width_mm NUMERIC(10,2),
  height_mm NUMERIC(10,2),
  thickness_mm NUMERIC(10,2),
  weight_value NUMERIC(10,2),                 -- Numeric weight
  weight_unit VARCHAR(20),                    -- kg/m2, g/m2, kg/panel, kg/lm
  repeat_width_mm NUMERIC(10,2),              -- 0 if no repeat
  repeat_height_mm NUMERIC(10,2),             -- 0 if no repeat

  -- FIRE CLASSIFICATION (EN 13501-1, split into 3 fields)
  fire_class_eu VARCHAR(5),                   -- A1, A2, B, C, D, E, F
  fire_smoke_class_eu VARCHAR(5),             -- s1, s2, s3
  fire_droplet_class_eu VARCHAR(5),           -- d0, d1, d2
  fire_class_us VARCHAR(20),                  -- ASTM E84 Class A/B/C if tested

  -- ACOUSTIC
  nrc_value NUMERIC(4,2),                     -- 0.00 to 1.00
  acoustic_class CHAR(1),                     -- A, B, C, D, E per ISO 11654

  -- COMMERCIAL CLASSIFICATION
  commercial_grade TEXT[] NOT NULL DEFAULT '{}', -- Array: type_i, type_ii, type_iii,
    -- contract_grade, residential_grade, marine_grade, exterior_grade
  suitable_environments TEXT,                 -- Comma-separated: hospitality, residential, retail, etc.

  -- SUSTAINABILITY
  recycled_content_pct SMALLINT,              -- 0-100
  voc_class VARCHAR(5),                       -- A+, A, B, C per French VOC regulation

  -- PRICING
  price_visibility VARCHAR(20) NOT NULL DEFAULT 'on_request',
    -- public: visible to all
    -- on_request: contact for price
    -- trade_only: visible only to verified specifiers (exact trade pricing)
    -- registered: visible on login (indicative pricing)
  indicative_price_eur NUMERIC(10,2),
  price_unit VARCHAR(20),                     -- m2, lm, panel, piece, set
  moq INTEGER NOT NULL DEFAULT 1,             -- Minimum order quantity
  moq_unit VARCHAR(20),                       -- m2, lm, panel, piece

  -- LEAD TIME & AVAILABILITY
  lead_time_weeks_min SMALLINT NOT NULL,
  lead_time_weeks_max SMALLINT,
  sample_available BOOLEAN NOT NULL DEFAULT FALSE,
  sample_type VARCHAR(30),                    -- swatch, cutout, a4, full_panel
  made_to_order BOOLEAN DEFAULT TRUE,

  -- STATUS
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_featured BOOLEAN NOT NULL DEFAULT FALSE,

  -- TIMESTAMPS
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE products IS '44 fields. All justified by specifier workflow or Material Bank/Archiproducts export compatibility. No filler.';
COMMENT ON COLUMN products.category IS 'App-layer validated. 12 values: wallcovering, surface_panel, acoustic_panel, ceiling_tile, ceiling_system, textile, mural, decorative_paint, liquid_metal, bespoke_finish, decorative_mesh, composite_surface.';
COMMENT ON COLUMN products.commercial_grade IS 'TEXT[] array. One product can qualify for multiple grades: type_i, type_ii, type_iii, contract_grade, residential_grade, marine_grade, exterior_grade.';
COMMENT ON COLUMN products.price_visibility IS 'Two-tier access: registered = visible on login (indicative), trade_only = visible after verified flag (exact trade pricing).';

-- Product indexes
CREATE INDEX idx_products_manufacturer ON products(manufacturer_id);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_fire_class ON products(fire_class_eu);
CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_products_featured ON products(is_featured) WHERE is_featured = TRUE;
CREATE INDEX idx_products_slug ON products(slug);
CREATE GIN INDEX idx_products_commercial_grade ON products USING GIN (commercial_grade);
CREATE INDEX idx_products_category_fire_manufacturer ON products(category, fire_class_eu, manufacturer_id);

COMMENT ON INDEX idx_products_commercial_grade IS 'GIN index for array containment queries: WHERE commercial_grade @> ARRAY[''type_ii'']';
COMMENT ON INDEX idx_products_category_fire_manufacturer IS 'Composite index for the most common catalog filter pattern.';

-- ============================================================================
-- 3. PRODUCT_CERTIFICATIONS
-- ============================================================================
CREATE TABLE product_certifications (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  certification_code VARCHAR(50) NOT NULL,    -- Canonical codes: EUROCLASS_A1, EUROCLASS_B,
    -- EUROCLASS_B_S1, EUROCLASS_B_S1_D0, EUROCLASS_B_S2_D0,
    -- FSC, PEFC, OEKO_TEX_100, OEKO_TEX_STEP,
    -- GREENGUARD, GREENGUARD_GOLD, CRADLE_TO_CRADLE,
    -- EPD, CE_MARKING, IMO_MED
  certification_name VARCHAR(200),            -- Human-readable
  issued_by VARCHAR(200),                     -- Issuing body
  certificate_number VARCHAR(100),
  valid_until DATE,                           -- NULL if perpetual
  document_url VARCHAR(500),                  -- URL to certificate PDF
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_certifications_product ON product_certifications(product_id);
CREATE INDEX idx_certifications_code ON product_certifications(certification_code);

COMMENT ON TABLE product_certifications IS 'One row per certification per product. CSV import validates certification_code against canonical list.';

-- ============================================================================
-- 4. PRODUCT_IMAGES
-- ============================================================================
CREATE TABLE product_images (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  url VARCHAR(1000) NOT NULL,                 -- Phase 0a: materialization.eu URLs directly
  alt_text VARCHAR(300),
  sort_order SMALLINT NOT NULL DEFAULT 0,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_images_product ON product_images(product_id);
CREATE INDEX idx_images_primary ON product_images(product_id, is_primary) WHERE is_primary = TRUE;

COMMENT ON TABLE product_images IS 'Phase 0a: existing materialization.eu URLs via CSV import. No upload flow. Asset pipeline decision deferred.';

-- ============================================================================
-- 5. SPECIFIERS
-- ============================================================================
CREATE TABLE specifiers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email CITEXT NOT NULL UNIQUE,               -- Case-insensitive via citext extension
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  firm_name VARCHAR(300) NOT NULL,
  role VARCHAR(100),                          -- Free text: Interior Designer, Architect, FF&E Manager
  country CHAR(2),                            -- ISO 3166-1 alpha-2
  phone VARCHAR(30),
  specialization VARCHAR(200),                -- Free text: hospitality, residential, retail
  firm_website VARCHAR(500),                  -- Required for verification path A
  linkedin_url VARCHAR(500),                  -- Required for verification path B

  -- VERIFICATION
  verified BOOLEAN NOT NULL DEFAULT FALSE,    -- Phase 0a: binary, manual flip
  verified_at TIMESTAMPTZ,                    -- When verification was granted
  verified_by_admin_id UUID REFERENCES specifiers(id), -- Which admin verified
  verification_notes TEXT,                    -- Admin notes on verification decision

  -- AUTH
  role_type VARCHAR(20) NOT NULL DEFAULT 'specifier' CHECK (role_type IN ('specifier', 'admin')),
  last_login_at TIMESTAMPTZ,
  email_send_failed BOOLEAN NOT NULL DEFAULT FALSE, -- Surfaced in admin dashboard

  -- HUBSPOT
  hubspot_contact_id VARCHAR(50),             -- Written on magic link send, before click

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_specifiers_email ON specifiers(email);
CREATE INDEX idx_specifiers_verified ON specifiers(verified);
CREATE INDEX idx_specifiers_role_type ON specifiers(role_type) WHERE role_type = 'admin';

COMMENT ON TABLE specifiers IS 'Email-first identity. Admin = specifier with role_type=admin, no separate table. Verification is manual Phase 0a.';
COMMENT ON COLUMN specifiers.verified IS 'Binary flag. Trade prices gated on verified=TRUE, not just registered. Domain whitelist trigger: queue > 30 pending OR avg response > 24hr.';
COMMENT ON COLUMN specifiers.verified_at IS 'Audit trail: when verification was granted.';
COMMENT ON COLUMN specifiers.verified_by_admin_id IS 'Audit trail: which admin performed verification.';
COMMENT ON COLUMN specifiers.email_send_failed IS 'Set TRUE on final email send failure. Surfaced in admin dashboard for manual follow-up.';

-- ============================================================================
-- 6. MAGIC_LINK_TOKENS
-- ============================================================================
CREATE TABLE magic_link_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(320) NOT NULL,
  token_hash VARCHAR(64) NOT NULL UNIQUE,     -- SHA-256, hex-encoded. Bcrypt rejected.
  intent VARCHAR(20) NOT NULL CHECK (intent IN ('register', 'login', 'verify_email')),
  specifier_id UUID REFERENCES specifiers(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  consumed_at TIMESTAMPTZ,
  ip_address INET,
  user_agent TEXT
);

CREATE INDEX idx_magic_link_tokens_email ON magic_link_tokens(email);
CREATE INDEX idx_magic_link_tokens_token_hash ON magic_link_tokens(token_hash);
CREATE INDEX idx_magic_link_tokens_expires_at ON magic_link_tokens(expires_at) WHERE consumed_at IS NULL;

COMMENT ON TABLE magic_link_tokens IS 'Stateful magic links in Postgres, not stateless JWT. SHA-256 hash lookup: WHERE token_hash = sha256(plaintext) AND consumed_at IS NULL AND expires_at > NOW().';

-- ============================================================================
-- 7. PROJECTS
-- ============================================================================
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  specifier_id UUID NOT NULL REFERENCES specifiers(id) ON DELETE CASCADE,
  name VARCHAR(300) NOT NULL,
  description TEXT,
  client_name VARCHAR(300),                   -- End client for the project
  project_type VARCHAR(50),                   -- hospitality, residential, retail, office, healthcare, marine
  status VARCHAR(30) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'completed')),

  -- SHARING
  share_token VARCHAR(64) UNIQUE,             -- Read-only public link token
  is_shared BOOLEAN NOT NULL DEFAULT FALSE,   -- DELETE /api/projects/{id}/share sets FALSE, nulls share_token

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_specifier ON projects(specifier_id);
CREATE INDEX idx_projects_share_token ON projects(share_token) WHERE share_token IS NOT NULL;

COMMENT ON TABLE projects IS 'Project as named object. Samples/shortlists/specs attached. share_token enables read-only public link without collaboration auth.';
COMMENT ON COLUMN projects.share_token IS 'Permanent until manually revoked. Old URL returns 404 after revocation.';

-- ============================================================================
-- 8. PROJECT_PRODUCTS (join table)
-- ============================================================================
CREATE TABLE project_products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  notes TEXT,                                 -- Specifier notes on this product in context
  sort_order SMALLINT NOT NULL DEFAULT 0,
  added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  UNIQUE(project_id, product_id)              -- No duplicates in same project
);

CREATE INDEX idx_project_products_project ON project_products(project_id);
CREATE INDEX idx_project_products_product ON project_products(product_id);

-- ============================================================================
-- 9. SAMPLE_REQUESTS
-- ============================================================================
CREATE TABLE sample_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  specifier_id UUID NOT NULL REFERENCES specifiers(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,  -- Optional project context

  status VARCHAR(30) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'shipped', 'delivered', 'cancelled')),
  shipping_address TEXT,
  notes TEXT,                                 -- Specifier notes with request

  -- ADMIN RESPONSE
  tracking_number VARCHAR(100),
  shipped_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sample_requests_specifier ON sample_requests(specifier_id);
CREATE INDEX idx_sample_requests_product ON sample_requests(product_id);
CREATE INDEX idx_sample_requests_status ON sample_requests(status);

COMMENT ON TABLE sample_requests IS 'SLA: under-promise at 5 business days. Status transitions managed by admin Phase 0a.';

-- ============================================================================
-- 10. QUOTE_REQUESTS
-- ============================================================================
CREATE TABLE quote_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  specifier_id UUID NOT NULL REFERENCES specifiers(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

  -- REQUEST
  quantity NUMERIC(10,2) NOT NULL,
  quantity_unit VARCHAR(20) NOT NULL,          -- m2, lm, panel, piece
  specifications TEXT,                        -- Custom requirements, colorway, substrate, dimensions
  notes TEXT,

  status VARCHAR(30) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'quoted', 'accepted', 'rejected', 'expired')),

  -- ADMIN RESPONSE (A9 validation rules)
  quoted_price NUMERIC(10,2),                 -- Min 0, max 1,000,000 (app-layer validated)
  quoted_currency CHAR(3) NOT NULL DEFAULT 'EUR',  -- EUR, GBP, USD (app-layer ENUM)
  lead_time_weeks INTEGER,                    -- Min 1, max 52 (app-layer validated)
  terms_notes TEXT,                           -- Max 2000 chars (app-layer validated)
  quoted_at TIMESTAMPTZ,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_quote_requests_specifier ON quote_requests(specifier_id);
CREATE INDEX idx_quote_requests_product ON quote_requests(product_id);
CREATE INDEX idx_quote_requests_status ON quote_requests(status);

COMMENT ON TABLE quote_requests IS 'Admin-mediated Phase 0a. Manufacturer dashboard trigger: monthly quote volume > 20.';
COMMENT ON COLUMN quote_requests.quoted_currency IS 'CHAR(3) ISO 4217. Default EUR. App-layer validates against allowed set (EUR, GBP, USD).';

-- ============================================================================
-- 11. EVENTS (behavioral data, non-deferrable)
-- ============================================================================
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type VARCHAR(100) NOT NULL,           -- product_viewed, product_added_to_project,
    -- sample_requested, quote_requested, catalog_filtered,
    -- project_created, project_shared, specifier_registered,
    -- specifier_verified, search_performed
  specifier_id UUID REFERENCES specifiers(id) ON DELETE SET NULL,  -- NULL for anonymous
  session_id VARCHAR(64),                     -- Anonymous localStorage ID, 90-day TTL
  product_id UUID REFERENCES products(id) ON DELETE SET NULL,
  project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
  manufacturer_id UUID REFERENCES manufacturers(id) ON DELETE SET NULL,
  properties JSONB DEFAULT '{}',              -- Flexible event-specific data. New event types
    -- ship in a frontend deploy with zero backend or schema change.
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_specifier ON events(specifier_id);
CREATE INDEX idx_events_product ON events(product_id);
CREATE INDEX idx_events_manufacturer ON events(manufacturer_id);
CREATE INDEX idx_events_created ON events(created_at);
CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_properties ON events USING GIN (properties);

COMMENT ON TABLE events IS 'Behavioral data from day one. Cannot be backfilled. Feeds manufacturer pitch data story. JSONB properties means new event types ship with zero backend change.';
-- PARTITION NOTE: Consider range partitioning on created_at when row count exceeds 1M.
-- ALTER TABLE events RENAME TO events_old;
-- CREATE TABLE events (...) PARTITION BY RANGE (created_at);
-- Then create monthly partitions. Not needed Phase 0a.

-- ============================================================================
-- TRIGGERS: updated_at auto-refresh
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_manufacturers_updated BEFORE UPDATE ON manufacturers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_products_updated BEFORE UPDATE ON products
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_specifiers_updated BEFORE UPDATE ON specifiers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_projects_updated BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_sample_requests_updated BEFORE UPDATE ON sample_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_quote_requests_updated BEFORE UPDATE ON quote_requests
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- SEED DATA: Phase 0a manufacturers
-- ============================================================================
INSERT INTO manufacturers (name, slug, country, city, website, description, is_active) VALUES
  ('Studio Saint-Pierre', 'studio-saint-pierre', 'FR', 'Thonon-les-Bains', 'https://www.materialization.eu/ssp/', 'Custom architectural surfaces. Béton fluid, liquid metal, decorative panels, bespoke finishes.', TRUE),
  ('Maison Jacquard', 'maison-jacquard', 'FR', 'Thonon-les-Bains', 'https://www.materialization.eu/maisonjacquard/', 'Bespoke woven wallcoverings. Jacquard textiles for hospitality and high-end residential.', TRUE),
  ('Ornam', 'ornam', 'FR', 'Thonon-les-Bains', 'https://orfrancaise.fr/', 'Premium wallcoverings curated for architects and interior designers.', TRUE);

-- ============================================================================
-- EXPORT MAPPINGS (reference, not enforced in SQL)
-- ============================================================================

-- MATERIAL BANK EXPORT MAPPING
-- ┌─────────────────────────┬──────────────────────────────────┐
-- │ Material Bank Field     │ Specifio Source                   │
-- ├─────────────────────────┼──────────────────────────────────┤
-- │ Product Name            │ products.name                    │
-- │ Brand                   │ manufacturers.name               │
-- │ SKU / Item Number       │ products.sku                     │
-- │ Category                │ products.category (mapped)       │
-- │ Description             │ products.short_description       │
-- │ Material                │ products.primary_material        │
-- │ Dimensions (W x H)      │ products.width_mm, height_mm     │
-- │ Color / Finish          │ products.colorway_name           │
-- │ Fire Rating             │ products.fire_class_eu + smoke + droplet │
-- │ Sustainability Certs    │ product_certifications (filtered) │
-- │ Lead Time               │ products.lead_time_weeks_min/max │
-- │ Sample Available        │ products.sample_available        │
-- │ Image                   │ product_images.url (is_primary)  │
-- │ Country of Origin       │ manufacturers.country            │
-- └─────────────────────────┴──────────────────────────────────┘

-- ARCHIPRODUCTS EXPORT MAPPING
-- ┌─────────────────────────┬──────────────────────────────────┐
-- │ Archiproducts Field     │ Specifio Source                   │
-- ├─────────────────────────┼──────────────────────────────────┤
-- │ Product Name            │ products.name                    │
-- │ Brand                   │ manufacturers.name               │
-- │ Reference Code          │ products.sku                     │
-- │ Category (multi-lang)   │ products.category (mapped, i18n Phase 1) │
-- │ Short Description       │ products.short_description       │
-- │ Long Description        │ products.long_description        │
-- │ Materials               │ products.primary_material + secondary │
-- │ Dimensions              │ products.width_mm, height_mm, thickness_mm │
-- │ Weight                  │ products.weight_value + weight_unit │
-- │ Finishes / Colors       │ products.finish_type, colorway_name │
-- │ Certifications          │ product_certifications (all)     │
-- │ Environmental (EPD etc) │ product_certifications (filtered) │
-- │ Gallery Images          │ product_images (all, sorted)     │
-- │ Country of Manufacture  │ manufacturers.country            │
-- │ Custom / Bespoke Flag   │ products.made_to_order           │
-- │ MOQ                     │ products.moq + moq_unit          │
-- └─────────────────────────┴──────────────────────────────────┘

-- ============================================================================
-- QUERY CONSTRAINTS (app-layer, documented here for reference)
-- ============================================================================
-- Catalog query timeout: 2 seconds
-- Catalog result limit: 100 per page, pagination required
-- Registration rate limit: 5 new specifier rows per IP per day
-- Magic link send rate limit: separate, TBD at build time
-- Quote response validation:
--   quoted_price: NUMERIC(10,2), min 0, max 1,000,000
--   quoted_currency: ENUM('EUR','GBP','USD'), default EUR
--   lead_time_weeks: INTEGER, min 1, max 52
--   terms_notes: TEXT, max 2000 chars
--   All four required to submit status = 'quoted'

-- ============================================================================
-- END SCHEMA v1.1
-- ============================================================================
