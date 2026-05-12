BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_inventory_ml(
    count_750ml NUMERIC,
    count_1l NUMERIC,
    count_1_75l NUMERIC,
    count_draft_tenths NUMERIC,
    bottle_size_ml NUMERIC,
    keg_size_ml NUMERIC
)
RETURNS NUMERIC AS $$
BEGIN
    RETURN COALESCE(count_750ml, 0) * 750
         + COALESCE(count_1l, 0) * 1000
         + COALESCE(count_1_75l, 0) * 1750
         + COALESCE(count_draft_tenths, 0) * COALESCE(keg_size_ml, 0) / 10;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_variance(
    current_ml NUMERIC,
    previous_ml NUMERIC,
    purchases_ml NUMERIC,
    usage_ml NUMERIC,
    adjustments_ml NUMERIC
)
RETURNS NUMERIC AS $$
BEGIN
    RETURN COALESCE(current_ml, 0) - ((COALESCE(previous_ml, 0) + COALESCE(purchases_ml, 0)) - COALESCE(usage_ml, 0)) + COALESCE(adjustments_ml, 0);
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS venues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(150) UNIQUE NOT NULL,
    city VARCHAR(100),
    state VARCHAR(50),
    timezone VARCHAR(64) NOT NULL DEFAULT 'America/Chicago',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'manager',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID REFERENCES venues(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_drink BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vendors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    contact_name VARCHAR(150),
    phone VARCHAR(50),
    email VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    vendor_id UUID REFERENCES vendors(id) ON DELETE SET NULL,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(50) NOT NULL,
    bottle_cost NUMERIC(10,2) NOT NULL DEFAULT 0,
    case_cost NUMERIC(10,2) NOT NULL DEFAULT 0,
    case_size INTEGER NOT NULL DEFAULT 0,
    bottle_size_ml NUMERIC(10,2) NOT NULL DEFAULT 0,
    keg_size_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    standard_pour_ml NUMERIC(10,2) NOT NULL DEFAULT 0,
    par_level NUMERIC(10,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    sale_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    amount_ml NUMERIC(10,2) NOT NULL DEFAULT 0,
    is_primary_spirit BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS modifier_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    extra_ml NUMERIC(10,2) NOT NULL DEFAULT 0,
    applies_to_type VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    session_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress',
    total_inventory_value NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_variance_value NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS inventory_counts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES inventory_sessions(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    count_750ml NUMERIC(10,2) NOT NULL DEFAULT 0,
    count_1l NUMERIC(10,2) NOT NULL DEFAULT 0,
    count_1_75l NUMERIC(10,2) NOT NULL DEFAULT 0,
    count_draft_tenths NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_value NUMERIC(12,2) NOT NULL DEFAULT 0,
    previous_total_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    previous_total_value NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pos_imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    import_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    date_from DATE,
    date_to DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    records_processed INTEGER NOT NULL DEFAULT 0,
    records_matched INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pos_sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pos_import_id UUID NOT NULL REFERENCES pos_imports(id) ON DELETE CASCADE,
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    menu_item_name VARCHAR(200) NOT NULL,
    avg_price NUMERIC(10,2) NOT NULL DEFAULT 0,
    net_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
    theoretical_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    sale_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pos_modifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pos_import_id UUID NOT NULL REFERENCES pos_imports(id) ON DELETE CASCADE,
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    modifier_name VARCHAR(200) NOT NULL,
    parent_menu_item VARCHAR(200),
    quantity NUMERIC(10,2) NOT NULL DEFAULT 0,
    extra_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    sale_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID NOT NULL REFERENCES venues(id) ON DELETE CASCADE,
    vendor_id UUID REFERENCES vendors(id) ON DELETE SET NULL,
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date DATE,
    subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
    tax NUMERIC(12,2) NOT NULL DEFAULT 0,
    total NUMERIC(12,2) NOT NULL DEFAULT 0,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity_cases NUMERIC(10,2) NOT NULL DEFAULT 0,
    quantity_bottles NUMERIC(10,2) NOT NULL DEFAULT 0,
    unit_cost NUMERIC(10,2) NOT NULL DEFAULT 0,
    total_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    received_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS adjustments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES inventory_sessions(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    adjustment_type VARCHAR(50) NOT NULL,
    amount_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS variance_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES inventory_sessions(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    current_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    previous_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    purchases_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    theoretical_usage_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    adjustments_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    variance_ml NUMERIC(12,2) NOT NULL DEFAULT 0,
    variance_value NUMERIC(12,2) NOT NULL DEFAULT 0,
    accuracy_pct NUMERIC(8,2) NOT NULL DEFAULT 0,
    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    flag_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS event_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    venue_id UUID REFERENCES venues(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(150) NOT NULL,
    category VARCHAR(100),
    expected_revenue_min NUMERIC(12,2) NOT NULL DEFAULT 0,
    expected_revenue_max NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scenario_pars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id UUID NOT NULL REFERENCES event_scenarios(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    par_multiplier NUMERIC(10,2) NOT NULL DEFAULT 1,
    par_absolute NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_venue_id ON users(venue_id);
CREATE INDEX IF NOT EXISTS idx_categories_venue_id ON categories(venue_id);
CREATE INDEX IF NOT EXISTS idx_products_venue_id ON products(venue_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_inventory_counts_session_id ON inventory_counts(session_id);
CREATE INDEX IF NOT EXISTS idx_inventory_counts_product_id ON inventory_counts(product_id);
CREATE INDEX IF NOT EXISTS idx_pos_sales_venue_id ON pos_sales(venue_id);
CREATE INDEX IF NOT EXISTS idx_pos_modifiers_venue_id ON pos_modifiers(venue_id);
CREATE INDEX IF NOT EXISTS idx_variance_reports_session_id ON variance_reports(session_id);

INSERT INTO categories (venue_id, name, sort_order, is_drink)
VALUES
    (NULL, 'Bottle/Can', 1, TRUE),
    (NULL, 'Draft', 2, TRUE),
    (NULL, 'Spirit', 3, TRUE),
    (NULL, 'Wine', 4, TRUE),
    (NULL, 'N/A BEV', 5, TRUE),
    (NULL, 'Cognac', 6, TRUE),
    (NULL, 'Gin', 7, TRUE),
    (NULL, 'Liqueurs', 8, TRUE),
    (NULL, 'Mezcal', 9, TRUE),
    (NULL, 'Rum', 10, TRUE),
    (NULL, 'Scotch', 11, TRUE),
    (NULL, 'Seltzers', 12, TRUE),
    (NULL, 'Tequila', 13, TRUE),
    (NULL, 'Whiskey', 14, TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO event_scenarios (venue_id, name, slug, category, expected_revenue_min, expected_revenue_max)
VALUES
    (NULL, 'Slow Season Week', 'slow-season-week', 'Seasonality', 0, 0),
    (NULL, 'Busy Season Week', 'busy-season-week', 'Seasonality', 0, 0),
    (NULL, 'Popular Fight Night', 'popular-fight-night', 'Event', 0, 0),
    (NULL, 'HH <50', 'hh-less-than-50', 'Happy Hour', 0, 0),
    (NULL, 'HH 100', 'hh-100', 'Happy Hour', 0, 0),
    (NULL, 'HH 150', 'hh-150', 'Happy Hour', 0, 0),
    (NULL, 'HH 200', 'hh-200', 'Happy Hour', 0, 0),
    (NULL, 'HH 200-250', 'hh-200-250', 'Happy Hour', 0, 0),
    (NULL, 'HH 250-300', 'hh-250-300', 'Happy Hour', 0, 0),
    (NULL, 'HH 300-350', 'hh-300-350', 'Happy Hour', 0, 0),
    (NULL, 'XMAS Pop Up', 'xmas-pop-up', 'Holiday', 0, 0),
    (NULL, 'Slow Fight Night', 'slow-fight-night', 'Event', 0, 0),
    (NULL, 'New Years Eve/Day', 'new-years-eve-day', 'Holiday', 0, 0),
    (NULL, 'Valentines', 'valentines', 'Holiday', 0, 0),
    (NULL, 'HLSR Normal 75', 'hlsr-normal-75', 'Rodeo', 0, 0),
    (NULL, 'HLSR Busy 150+', 'hlsr-busy-150', 'Rodeo', 0, 0),
    (NULL, 'Mothers Day', 'mothers-day', 'Holiday', 0, 0),
    (NULL, 'Large Football Group', 'large-football-group', 'Sports', 0, 0),
    (NULL, 'Fathers Days', 'fathers-days', 'Holiday', 0, 0),
    (NULL, 'Astros Regular', 'astros-regular', 'Sports', 0, 0),
    (NULL, 'Astros Playoff', 'astros-playoff', 'Sports', 0, 0),
    (NULL, '4th of July', '4th-of-july', 'Holiday', 0, 0),
    (NULL, 'Labor Day', 'labor-day', 'Holiday', 0, 0),
    (NULL, 'Memorial Day', 'memorial-day', 'Holiday', 0, 0),
    (NULL, 'Back to School', 'back-to-school', 'Seasonality', 0, 0),
    (NULL, 'Halloween', 'halloween', 'Holiday', 0, 0),
    (NULL, 'Thanksgiving/BF', 'thanksgiving-bf', 'Holiday', 0, 0),
    (NULL, 'Football Popular Team', 'football-popular-team', 'Sports', 0, 0),
    (NULL, 'Football Not Popular', 'football-not-popular', 'Sports', 0, 0),
    (NULL, 'Basketball UofH', 'basketball-uofh', 'Sports', 0, 0),
    (NULL, 'Basketball Rockets Good', 'basketball-rockets-good', 'Sports', 0, 0),
    (NULL, 'Basketball Playoff', 'basketball-playoff', 'Sports', 0, 0),
    (NULL, 'College Crowd', 'college-crowd', 'Demographic', 0, 0)
ON CONFLICT DO NOTHING;

COMMIT;
