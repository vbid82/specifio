--
-- PostgreSQL database dump
--

\restrict 3AX0q2Zq1h3Ek1OXoDWUzATUJe3bxZtVgEjqqQFcZ27jehlTqDI9fnpCGGDwwwj

-- Dumped from database version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: citext; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;


--
-- Name: EXTENSION citext; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION citext IS 'data type for case-insensitive character strings';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: update_updated_at(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.events (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_type character varying(100) NOT NULL,
    specifier_id uuid,
    session_id character varying(64),
    product_id uuid,
    project_id uuid,
    manufacturer_id uuid,
    properties jsonb DEFAULT '{}'::jsonb,
    ip_address inet,
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.events OWNER TO postgres;

--
-- Name: TABLE events; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.events IS 'Behavioral data from day one. Cannot be backfilled. Feeds manufacturer pitch data story. JSONB properties means new event types ship with zero backend change.';


--
-- Name: magic_link_tokens; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.magic_link_tokens (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email character varying(320) NOT NULL,
    token_hash character varying(64) NOT NULL,
    intent character varying(20) NOT NULL,
    specifier_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    consumed_at timestamp with time zone,
    ip_address inet,
    user_agent text,
    CONSTRAINT magic_link_tokens_intent_check CHECK (((intent)::text = ANY ((ARRAY['register'::character varying, 'login'::character varying, 'verify_email'::character varying])::text[])))
);


ALTER TABLE public.magic_link_tokens OWNER TO postgres;

--
-- Name: TABLE magic_link_tokens; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.magic_link_tokens IS 'Stateful magic links in Postgres, not stateless JWT. SHA-256 hash lookup: WHERE token_hash = sha256(plaintext) AND consumed_at IS NULL AND expires_at > NOW().';


--
-- Name: manufacturers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.manufacturers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name character varying(200) NOT NULL,
    slug character varying(200) NOT NULL,
    country character(2) NOT NULL,
    city character varying(100),
    website character varying(500),
    logo_url character varying(500),
    description text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.manufacturers OWNER TO postgres;

--
-- Name: TABLE manufacturers; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.manufacturers IS 'Phase 0a: SSP, MJ, Ornam only. Phase 0b: external manufacturers onboard.';


--
-- Name: product_certifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_certifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    product_id uuid NOT NULL,
    certification_code character varying(50) NOT NULL,
    certification_name character varying(200),
    issued_by character varying(200),
    certificate_number character varying(100),
    valid_until date,
    document_url character varying(500),
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.product_certifications OWNER TO postgres;

--
-- Name: TABLE product_certifications; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.product_certifications IS 'One row per certification per product. CSV import validates certification_code against canonical list.';


--
-- Name: product_images; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product_images (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    product_id uuid NOT NULL,
    url character varying(1000) NOT NULL,
    alt_text character varying(300),
    sort_order smallint DEFAULT 0 NOT NULL,
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.product_images OWNER TO postgres;

--
-- Name: TABLE product_images; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.product_images IS 'Phase 0a: existing materialization.eu URLs via CSV import. No upload flow. Asset pipeline decision deferred.';


--
-- Name: products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.products (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    manufacturer_id uuid NOT NULL,
    sku character varying(50) NOT NULL,
    name character varying(300) NOT NULL,
    slug character varying(300) NOT NULL,
    category character varying(50) NOT NULL,
    subcategory character varying(100),
    short_description character varying(500) NOT NULL,
    long_description text,
    primary_material character varying(100) NOT NULL,
    secondary_material character varying(100),
    finish_type character varying(50),
    colorway_name character varying(100),
    colorway_count integer,
    custom_colorway boolean DEFAULT false,
    width_mm numeric(10,2),
    height_mm numeric(10,2),
    thickness_mm numeric(10,2),
    weight_value numeric(10,2),
    weight_unit character varying(20),
    repeat_width_mm numeric(10,2),
    repeat_height_mm numeric(10,2),
    fire_class_eu character varying(5),
    fire_smoke_class_eu character varying(5),
    fire_droplet_class_eu character varying(5),
    fire_class_us character varying(20),
    nrc_value numeric(4,2),
    acoustic_class character(1),
    commercial_grade text[] DEFAULT '{}'::text[] NOT NULL,
    suitable_environments text,
    recycled_content_pct smallint,
    voc_class character varying(5),
    price_visibility character varying(20) DEFAULT 'on_request'::character varying NOT NULL,
    indicative_price_eur numeric(10,2),
    price_unit character varying(20),
    moq integer DEFAULT 1 NOT NULL,
    moq_unit character varying(20),
    lead_time_weeks_min smallint NOT NULL,
    lead_time_weeks_max smallint,
    sample_available boolean DEFAULT false NOT NULL,
    sample_type character varying(30),
    made_to_order boolean DEFAULT true,
    is_active boolean DEFAULT true NOT NULL,
    is_featured boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.products OWNER TO postgres;

--
-- Name: TABLE products; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.products IS '44 fields. All justified by specifier workflow or Material Bank/Archiproducts export compatibility. No filler.';


--
-- Name: COLUMN products.category; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.products.category IS 'App-layer validated. 12 values: wallcovering, surface_panel, acoustic_panel, ceiling_tile, ceiling_system, textile, mural, decorative_paint, liquid_metal, bespoke_finish, decorative_mesh, composite_surface.';


--
-- Name: COLUMN products.commercial_grade; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.products.commercial_grade IS 'TEXT[] array. One product can qualify for multiple grades: type_i, type_ii, type_iii, contract_grade, residential_grade, marine_grade, exterior_grade.';


--
-- Name: COLUMN products.price_visibility; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.products.price_visibility IS 'Two-tier access: registered = visible on login (indicative), trade_only = visible after verified flag (exact trade pricing).';


--
-- Name: project_products; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_products (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id uuid NOT NULL,
    product_id uuid NOT NULL,
    notes text,
    sort_order smallint DEFAULT 0 NOT NULL,
    added_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.project_products OWNER TO postgres;

--
-- Name: projects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.projects (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    specifier_id uuid NOT NULL,
    name character varying(300) NOT NULL,
    description text,
    client_name character varying(300),
    project_type character varying(50),
    status character varying(30) DEFAULT 'active'::character varying NOT NULL,
    share_token character varying(64),
    is_shared boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT projects_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'archived'::character varying, 'completed'::character varying])::text[])))
);


ALTER TABLE public.projects OWNER TO postgres;

--
-- Name: TABLE projects; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.projects IS 'Project as named object. Samples/shortlists/specs attached. share_token enables read-only public link without collaboration auth.';


--
-- Name: COLUMN projects.share_token; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.projects.share_token IS 'Permanent until manually revoked. Old URL returns 404 after revocation.';


--
-- Name: quote_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.quote_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    specifier_id uuid NOT NULL,
    product_id uuid NOT NULL,
    project_id uuid,
    quantity numeric(10,2) NOT NULL,
    quantity_unit character varying(20) NOT NULL,
    specifications text,
    notes text,
    status character varying(30) DEFAULT 'pending'::character varying NOT NULL,
    quoted_price numeric(10,2),
    quoted_currency character(3) DEFAULT 'EUR'::bpchar NOT NULL,
    lead_time_weeks integer,
    terms_notes text,
    quoted_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT quote_requests_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'quoted'::character varying, 'accepted'::character varying, 'rejected'::character varying, 'expired'::character varying])::text[])))
);


ALTER TABLE public.quote_requests OWNER TO postgres;

--
-- Name: TABLE quote_requests; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.quote_requests IS 'Admin-mediated Phase 0a. Manufacturer dashboard trigger: monthly quote volume > 20.';


--
-- Name: COLUMN quote_requests.quoted_currency; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.quote_requests.quoted_currency IS 'CHAR(3) ISO 4217. Default EUR. App-layer validates against allowed set (EUR, GBP, USD).';


--
-- Name: sample_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sample_requests (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    specifier_id uuid NOT NULL,
    product_id uuid NOT NULL,
    project_id uuid,
    status character varying(30) DEFAULT 'pending'::character varying NOT NULL,
    shipping_address text,
    notes text,
    tracking_number character varying(100),
    shipped_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT sample_requests_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'shipped'::character varying, 'delivered'::character varying, 'cancelled'::character varying])::text[])))
);


ALTER TABLE public.sample_requests OWNER TO postgres;

--
-- Name: TABLE sample_requests; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.sample_requests IS 'SLA: under-promise at 5 business days. Status transitions managed by admin Phase 0a.';


--
-- Name: specifiers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.specifiers (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    email public.citext NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    firm_name character varying(300) NOT NULL,
    role character varying(100),
    country character(2),
    phone character varying(30),
    specialization character varying(200),
    firm_website character varying(500),
    linkedin_url character varying(500),
    verified boolean DEFAULT false NOT NULL,
    verified_at timestamp with time zone,
    verified_by_admin_id uuid,
    verification_notes text,
    role_type character varying(20) DEFAULT 'specifier'::character varying NOT NULL,
    last_login_at timestamp with time zone,
    email_send_failed boolean DEFAULT false NOT NULL,
    hubspot_contact_id character varying(50),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT specifiers_role_type_check CHECK (((role_type)::text = ANY ((ARRAY['specifier'::character varying, 'admin'::character varying])::text[])))
);


ALTER TABLE public.specifiers OWNER TO postgres;

--
-- Name: TABLE specifiers; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.specifiers IS 'Email-first identity. Admin = specifier with role_type=admin, no separate table. Verification is manual Phase 0a.';


--
-- Name: COLUMN specifiers.verified; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.specifiers.verified IS 'Binary flag. Trade prices gated on verified=TRUE, not just registered. Domain whitelist trigger: queue > 30 pending OR avg response > 24hr.';


--
-- Name: COLUMN specifiers.verified_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.specifiers.verified_at IS 'Audit trail: when verification was granted.';


--
-- Name: COLUMN specifiers.verified_by_admin_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.specifiers.verified_by_admin_id IS 'Audit trail: which admin performed verification.';


--
-- Name: COLUMN specifiers.email_send_failed; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.specifiers.email_send_failed IS 'Set TRUE on final email send failure. Surfaced in admin dashboard for manual follow-up.';


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (id);


--
-- Name: magic_link_tokens magic_link_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.magic_link_tokens
    ADD CONSTRAINT magic_link_tokens_pkey PRIMARY KEY (id);


--
-- Name: magic_link_tokens magic_link_tokens_token_hash_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.magic_link_tokens
    ADD CONSTRAINT magic_link_tokens_token_hash_key UNIQUE (token_hash);


--
-- Name: manufacturers manufacturers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manufacturers
    ADD CONSTRAINT manufacturers_pkey PRIMARY KEY (id);


--
-- Name: manufacturers manufacturers_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.manufacturers
    ADD CONSTRAINT manufacturers_slug_key UNIQUE (slug);


--
-- Name: product_certifications product_certifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_certifications
    ADD CONSTRAINT product_certifications_pkey PRIMARY KEY (id);


--
-- Name: product_images product_images_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_images
    ADD CONSTRAINT product_images_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: products products_sku_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_sku_key UNIQUE (sku);


--
-- Name: products products_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_slug_key UNIQUE (slug);


--
-- Name: project_products project_products_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_products
    ADD CONSTRAINT project_products_pkey PRIMARY KEY (id);


--
-- Name: project_products project_products_project_id_product_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_products
    ADD CONSTRAINT project_products_project_id_product_id_key UNIQUE (project_id, product_id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: projects projects_share_token_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_share_token_key UNIQUE (share_token);


--
-- Name: quote_requests quote_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quote_requests
    ADD CONSTRAINT quote_requests_pkey PRIMARY KEY (id);


--
-- Name: sample_requests sample_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sample_requests
    ADD CONSTRAINT sample_requests_pkey PRIMARY KEY (id);


--
-- Name: specifiers specifiers_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.specifiers
    ADD CONSTRAINT specifiers_email_key UNIQUE (email);


--
-- Name: specifiers specifiers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.specifiers
    ADD CONSTRAINT specifiers_pkey PRIMARY KEY (id);


--
-- Name: idx_certifications_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_certifications_code ON public.product_certifications USING btree (certification_code);


--
-- Name: idx_certifications_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_certifications_product ON public.product_certifications USING btree (product_id);


--
-- Name: idx_events_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_created ON public.events USING btree (created_at);


--
-- Name: idx_events_manufacturer; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_manufacturer ON public.events USING btree (manufacturer_id);


--
-- Name: idx_events_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_product ON public.events USING btree (product_id);


--
-- Name: idx_events_properties; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_properties ON public.events USING gin (properties);


--
-- Name: idx_events_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_session ON public.events USING btree (session_id);


--
-- Name: idx_events_specifier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_specifier ON public.events USING btree (specifier_id);


--
-- Name: idx_events_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_events_type ON public.events USING btree (event_type);


--
-- Name: idx_images_primary; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_images_primary ON public.product_images USING btree (product_id, is_primary) WHERE (is_primary = true);


--
-- Name: idx_images_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_images_product ON public.product_images USING btree (product_id);


--
-- Name: idx_magic_link_tokens_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_magic_link_tokens_email ON public.magic_link_tokens USING btree (email);


--
-- Name: idx_magic_link_tokens_expires_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_magic_link_tokens_expires_at ON public.magic_link_tokens USING btree (expires_at) WHERE (consumed_at IS NULL);


--
-- Name: idx_magic_link_tokens_token_hash; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_magic_link_tokens_token_hash ON public.magic_link_tokens USING btree (token_hash);


--
-- Name: idx_products_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_active ON public.products USING btree (is_active) WHERE (is_active = true);


--
-- Name: idx_products_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_category ON public.products USING btree (category);


--
-- Name: idx_products_category_fire_manufacturer; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_category_fire_manufacturer ON public.products USING btree (category, fire_class_eu, manufacturer_id);


--
-- Name: INDEX idx_products_category_fire_manufacturer; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON INDEX public.idx_products_category_fire_manufacturer IS 'Composite index for the most common catalog filter pattern.';


--
-- Name: idx_products_featured; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_featured ON public.products USING btree (is_featured) WHERE (is_featured = true);


--
-- Name: idx_products_fire_class; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_fire_class ON public.products USING btree (fire_class_eu);


--
-- Name: idx_products_manufacturer; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_manufacturer ON public.products USING btree (manufacturer_id);


--
-- Name: idx_products_slug; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_products_slug ON public.products USING btree (slug);


--
-- Name: idx_project_products_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_project_products_product ON public.project_products USING btree (product_id);


--
-- Name: idx_project_products_project; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_project_products_project ON public.project_products USING btree (project_id);


--
-- Name: idx_projects_share_token; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_projects_share_token ON public.projects USING btree (share_token) WHERE (share_token IS NOT NULL);


--
-- Name: idx_projects_specifier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_projects_specifier ON public.projects USING btree (specifier_id);


--
-- Name: idx_quote_requests_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quote_requests_product ON public.quote_requests USING btree (product_id);


--
-- Name: idx_quote_requests_specifier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quote_requests_specifier ON public.quote_requests USING btree (specifier_id);


--
-- Name: idx_quote_requests_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_quote_requests_status ON public.quote_requests USING btree (status);


--
-- Name: idx_sample_requests_product; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sample_requests_product ON public.sample_requests USING btree (product_id);


--
-- Name: idx_sample_requests_specifier; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sample_requests_specifier ON public.sample_requests USING btree (specifier_id);


--
-- Name: idx_sample_requests_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_sample_requests_status ON public.sample_requests USING btree (status);


--
-- Name: idx_specifiers_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_specifiers_email ON public.specifiers USING btree (email);


--
-- Name: idx_specifiers_role_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_specifiers_role_type ON public.specifiers USING btree (role_type) WHERE ((role_type)::text = 'admin'::text);


--
-- Name: idx_specifiers_verified; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_specifiers_verified ON public.specifiers USING btree (verified);


--
-- Name: manufacturers trg_manufacturers_updated; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_manufacturers_updated BEFORE UPDATE ON public.manufacturers FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: products trg_products_updated; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_products_updated BEFORE UPDATE ON public.products FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: projects trg_projects_updated; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_projects_updated BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: quote_requests trg_quote_requests_updated; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_quote_requests_updated BEFORE UPDATE ON public.quote_requests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: sample_requests trg_sample_requests_updated; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_sample_requests_updated BEFORE UPDATE ON public.sample_requests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: specifiers trg_specifiers_updated; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_specifiers_updated BEFORE UPDATE ON public.specifiers FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();


--
-- Name: events events_manufacturer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_manufacturer_id_fkey FOREIGN KEY (manufacturer_id) REFERENCES public.manufacturers(id) ON DELETE SET NULL;


--
-- Name: events events_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE SET NULL;


--
-- Name: events events_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: events events_specifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_specifier_id_fkey FOREIGN KEY (specifier_id) REFERENCES public.specifiers(id) ON DELETE SET NULL;


--
-- Name: magic_link_tokens magic_link_tokens_specifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.magic_link_tokens
    ADD CONSTRAINT magic_link_tokens_specifier_id_fkey FOREIGN KEY (specifier_id) REFERENCES public.specifiers(id) ON DELETE CASCADE;


--
-- Name: product_certifications product_certifications_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_certifications
    ADD CONSTRAINT product_certifications_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: product_images product_images_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product_images
    ADD CONSTRAINT product_images_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: products products_manufacturer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_manufacturer_id_fkey FOREIGN KEY (manufacturer_id) REFERENCES public.manufacturers(id) ON DELETE CASCADE;


--
-- Name: project_products project_products_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_products
    ADD CONSTRAINT project_products_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: project_products project_products_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_products
    ADD CONSTRAINT project_products_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: projects projects_specifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_specifier_id_fkey FOREIGN KEY (specifier_id) REFERENCES public.specifiers(id) ON DELETE CASCADE;


--
-- Name: quote_requests quote_requests_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quote_requests
    ADD CONSTRAINT quote_requests_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: quote_requests quote_requests_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quote_requests
    ADD CONSTRAINT quote_requests_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: quote_requests quote_requests_specifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.quote_requests
    ADD CONSTRAINT quote_requests_specifier_id_fkey FOREIGN KEY (specifier_id) REFERENCES public.specifiers(id) ON DELETE CASCADE;


--
-- Name: sample_requests sample_requests_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sample_requests
    ADD CONSTRAINT sample_requests_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE CASCADE;


--
-- Name: sample_requests sample_requests_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sample_requests
    ADD CONSTRAINT sample_requests_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;


--
-- Name: sample_requests sample_requests_specifier_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sample_requests
    ADD CONSTRAINT sample_requests_specifier_id_fkey FOREIGN KEY (specifier_id) REFERENCES public.specifiers(id) ON DELETE CASCADE;


--
-- Name: specifiers specifiers_verified_by_admin_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.specifiers
    ADD CONSTRAINT specifiers_verified_by_admin_id_fkey FOREIGN KEY (verified_by_admin_id) REFERENCES public.specifiers(id);


--
-- Name: TABLE events; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.events TO specifio_user;


--
-- Name: TABLE magic_link_tokens; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.magic_link_tokens TO specifio_user;


--
-- Name: TABLE manufacturers; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.manufacturers TO specifio_user;


--
-- Name: TABLE product_certifications; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.product_certifications TO specifio_user;


--
-- Name: TABLE product_images; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.product_images TO specifio_user;


--
-- Name: TABLE products; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.products TO specifio_user;


--
-- Name: TABLE project_products; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.project_products TO specifio_user;


--
-- Name: TABLE projects; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.projects TO specifio_user;


--
-- Name: TABLE quote_requests; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.quote_requests TO specifio_user;


--
-- Name: TABLE sample_requests; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.sample_requests TO specifio_user;


--
-- Name: TABLE specifiers; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.specifiers TO specifio_user;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO specifio_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO specifio_user;


--
-- PostgreSQL database dump complete
--

\unrestrict 3AX0q2Zq1h3Ek1OXoDWUzATUJe3bxZtVgEjqqQFcZ27jehlTqDI9fnpCGGDwwwj

