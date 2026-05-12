import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Venue(Base):
    __tablename__ = "venues"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(150), nullable=False)
    slug = Column(String(150), unique=True, nullable=False, index=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    timezone = Column(String(64), nullable=False, default="America/Chicago")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    users = relationship("User", back_populates="venue", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="venue", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="venue", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="venue", cascade="all, delete-orphan")
    recipes = relationship("Recipe", back_populates="venue", cascade="all, delete-orphan")
    modifier_rules = relationship("ModifierRule", back_populates="venue", cascade="all, delete-orphan")
    inventory_sessions = relationship("InventorySession", back_populates="venue", cascade="all, delete-orphan")
    pos_imports = relationship("POSImport", back_populates="venue", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="venue", cascade="all, delete-orphan")
    event_scenarios = relationship("EventScenario", back_populates="venue", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="manager")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="users")
    inventory_sessions = relationship("InventorySession", back_populates="user")
    pos_imports = relationship("POSImport", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    is_drink = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="categories")
    products = relationship("Product", back_populates="category")


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    contact_name = Column(String(150), nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="vendors")
    products = relationship("Product", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")


class Product(Base):
    __tablename__ = "products"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    category_id = Column(PGUUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    vendor_id = Column(PGUUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    bottle_cost = Column(Numeric(10, 2), nullable=False, default=0)
    case_cost = Column(Numeric(10, 2), nullable=False, default=0)
    case_size = Column(Integer, nullable=False, default=0)
    bottle_size_ml = Column(Numeric(10, 2), nullable=False, default=0)
    keg_size_ml = Column(Numeric(12, 2), nullable=False, default=0)
    standard_pour_ml = Column(Numeric(10, 2), nullable=False, default=0)
    par_level = Column(Numeric(10, 2), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="products")
    category = relationship("Category", back_populates="products")
    vendor = relationship("Vendor", back_populates="products")
    recipe_ingredients = relationship("RecipeIngredient", back_populates="product")
    inventory_counts = relationship("InventoryCount", back_populates="product")
    purchases = relationship("Purchase", back_populates="product")
    adjustments = relationship("Adjustment", back_populates="product")
    variance_reports = relationship("VarianceReport", back_populates="product")
    scenario_pars = relationship("ScenarioPar", back_populates="product")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    sale_price = Column(Numeric(10, 2), nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="recipes")
    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(PGUUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False, index=True)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    amount_ml = Column(Numeric(10, 2), nullable=False, default=0)
    is_primary_spirit = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    recipe = relationship("Recipe", back_populates="ingredients")
    product = relationship("Product", back_populates="recipe_ingredients")


class ModifierRule(Base):
    __tablename__ = "modifier_rules"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    extra_ml = Column(Numeric(10, 2), nullable=False, default=0)
    applies_to_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="modifier_rules")


class InventorySession(Base):
    __tablename__ = "inventory_sessions"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="in_progress")
    total_inventory_value = Column(Numeric(12, 2), nullable=False, default=0)
    total_variance_value = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="inventory_sessions")
    user = relationship("User", back_populates="inventory_sessions")
    counts = relationship("InventoryCount", back_populates="session", cascade="all, delete-orphan")
    adjustments = relationship("Adjustment", back_populates="session", cascade="all, delete-orphan")
    variance_reports = relationship("VarianceReport", back_populates="session", cascade="all, delete-orphan")


class InventoryCount(Base):
    __tablename__ = "inventory_counts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("inventory_sessions.id"), nullable=False, index=True)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    count_750ml = Column(Numeric(10, 2), nullable=False, default=0)
    count_1L = Column(Numeric(10, 2), nullable=False, default=0)
    count_1_75L = Column(Numeric(10, 2), nullable=False, default=0)
    count_draft_tenths = Column(Numeric(10, 2), nullable=False, default=0)
    total_ml = Column(Numeric(12, 2), nullable=False, default=0)
    total_value = Column(Numeric(12, 2), nullable=False, default=0)
    previous_total_ml = Column(Numeric(12, 2), nullable=False, default=0)
    previous_total_value = Column(Numeric(12, 2), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    session = relationship("InventorySession", back_populates="counts")
    product = relationship("Product", back_populates="inventory_counts")


class POSImport(Base):
    __tablename__ = "pos_imports"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    import_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    date_from = Column(Date, nullable=True)
    date_to = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="pending")
    records_processed = Column(Integer, nullable=False, default=0)
    records_matched = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="pos_imports")
    user = relationship("User", back_populates="pos_imports")
    sales = relationship("POSSale", back_populates="pos_import", cascade="all, delete-orphan")
    modifiers = relationship("POSModifier", back_populates="pos_import", cascade="all, delete-orphan")


class POSSale(Base):
    __tablename__ = "pos_sales"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pos_import_id = Column(PGUUID(as_uuid=True), ForeignKey("pos_imports.id"), nullable=False, index=True)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    menu_item_name = Column(String(200), nullable=False, index=True)
    avg_price = Column(Numeric(10, 2), nullable=False, default=0)
    net_amount = Column(Numeric(12, 2), nullable=False, default=0)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    theoretical_ml = Column(Numeric(12, 2), nullable=False, default=0)
    sale_date = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    pos_import = relationship("POSImport", back_populates="sales")


class POSModifier(Base):
    __tablename__ = "pos_modifiers"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pos_import_id = Column(PGUUID(as_uuid=True), ForeignKey("pos_imports.id"), nullable=False, index=True)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    modifier_name = Column(String(200), nullable=False, index=True)
    parent_menu_item = Column(String(200), nullable=True, index=True)
    quantity = Column(Numeric(10, 2), nullable=False, default=0)
    extra_ml = Column(Numeric(12, 2), nullable=False, default=0)
    sale_date = Column(Date, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    pos_import = relationship("POSImport", back_populates="modifiers")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    vendor_id = Column(PGUUID(as_uuid=True), ForeignKey("vendors.id"), nullable=True, index=True)
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(Date, nullable=True)
    subtotal = Column(Numeric(12, 2), nullable=False, default=0)
    tax = Column(Numeric(12, 2), nullable=False, default=0)
    total = Column(Numeric(12, 2), nullable=False, default=0)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    purchases = relationship("Purchase", back_populates="invoice", cascade="all, delete-orphan")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(PGUUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    quantity_cases = Column(Numeric(10, 2), nullable=False, default=0)
    quantity_bottles = Column(Numeric(10, 2), nullable=False, default=0)
    unit_cost = Column(Numeric(10, 2), nullable=False, default=0)
    total_cost = Column(Numeric(12, 2), nullable=False, default=0)
    received_ml = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    invoice = relationship("Invoice", back_populates="purchases")
    product = relationship("Product", back_populates="purchases")


class Adjustment(Base):
    __tablename__ = "adjustments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("inventory_sessions.id"), nullable=False, index=True)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    adjustment_type = Column(String(50), nullable=False)
    amount_ml = Column(Numeric(12, 2), nullable=False, default=0)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    session = relationship("InventorySession", back_populates="adjustments")
    product = relationship("Product", back_populates="adjustments")


class VarianceReport(Base):
    __tablename__ = "variance_reports"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(PGUUID(as_uuid=True), ForeignKey("inventory_sessions.id"), nullable=False, index=True)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    current_ml = Column(Numeric(12, 2), nullable=False, default=0)
    previous_ml = Column(Numeric(12, 2), nullable=False, default=0)
    purchases_ml = Column(Numeric(12, 2), nullable=False, default=0)
    theoretical_usage_ml = Column(Numeric(12, 2), nullable=False, default=0)
    adjustments_ml = Column(Numeric(12, 2), nullable=False, default=0)
    variance_ml = Column(Numeric(12, 2), nullable=False, default=0)
    variance_value = Column(Numeric(12, 2), nullable=False, default=0)
    accuracy_pct = Column(Numeric(8, 2), nullable=False, default=0)
    is_flagged = Column(Boolean, nullable=False, default=False)
    flag_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    session = relationship("InventorySession", back_populates="variance_reports")
    product = relationship("Product", back_populates="variance_reports")


class EventScenario(Base):
    __tablename__ = "event_scenarios"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(PGUUID(as_uuid=True), ForeignKey("venues.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    slug = Column(String(150), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    expected_revenue_min = Column(Numeric(12, 2), nullable=False, default=0)
    expected_revenue_max = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    venue = relationship("Venue", back_populates="event_scenarios")
    scenario_pars = relationship("ScenarioPar", back_populates="scenario", cascade="all, delete-orphan")


class ScenarioPar(Base):
    __tablename__ = "scenario_pars"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(PGUUID(as_uuid=True), ForeignKey("event_scenarios.id"), nullable=False, index=True)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    par_multiplier = Column(Numeric(10, 2), nullable=False, default=1)
    par_absolute = Column(Numeric(12, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    scenario = relationship("EventScenario", back_populates="scenario_pars")
    product = relationship("Product", back_populates="scenario_pars")
