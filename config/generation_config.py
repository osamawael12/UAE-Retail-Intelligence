"""
Central configuration for the UAE Retail Intelligence
synthetic data generation pipeline.

All generators must import business-scale settings from
this module instead of hard-coding project-wide values.
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DATA_DIR = DATA_DIR / "generated"


@dataclass(frozen=True)
class GenerationConfig:
    # -----------------------------------------------------
    # Reproducibility
    # -----------------------------------------------------
    random_seed: int = 42

    # -----------------------------------------------------
    # Simulation period
    # -----------------------------------------------------
    start_date: date = date(2023, 1, 1)
    end_date: date = date(2025, 12, 31)

    # -----------------------------------------------------
    # Business scale
    # -----------------------------------------------------
    number_of_stores: int = 25
    number_of_categories: int = 8
    number_of_brands: int = 60
    number_of_products: int = 800
    number_of_customers: int = 25_000
    number_of_employees: int = 300
    number_of_suppliers: int = 50

    target_number_of_orders: int = 100_000

    # -----------------------------------------------------
    # Financial configuration
    # -----------------------------------------------------
    default_vat_rate: float = 0.05

    currency_code: str = "AED"

    # -----------------------------------------------------
    # Order behaviour
    # -----------------------------------------------------
    average_items_per_order: float = 3.0
    minimum_items_per_order: int = 1
    maximum_items_per_order: int = 8

    # -----------------------------------------------------
    # Customer age generation
    # -----------------------------------------------------
    minimum_customer_age: int = 18
    maximum_customer_age: int = 75

    # -----------------------------------------------------
    # Output
    # -----------------------------------------------------
    output_directory: Path = GENERATED_DATA_DIR


CONFIG = GenerationConfig()


def ensure_generation_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG.output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )


def validate_generation_config() -> None:
    if CONFIG.start_date >= CONFIG.end_date:
        raise ValueError(
            "start_date must be before end_date."
        )

    if CONFIG.number_of_stores != 25:
        raise ValueError(
            "This project requires exactly 25 stores."
        )

    if CONFIG.number_of_categories != 8:
        raise ValueError(
            "This project requires exactly 8 categories."
        )

    if CONFIG.number_of_brands != 60:
        raise ValueError(
            "This project requires exactly 60 brands."
        )

    if CONFIG.number_of_products != 800:
        raise ValueError(
            "This project requires exactly 800 products."
        )

    if CONFIG.number_of_customers != 25_000:
        raise ValueError(
            "This project requires exactly 25,000 customers."
        )

    if CONFIG.number_of_employees != 300:
        raise ValueError(
            "This project requires exactly 300 employees."
        )

    if CONFIG.number_of_suppliers != 50:
        raise ValueError(
            "This project requires exactly 50 suppliers."
        )

    if CONFIG.target_number_of_orders <= 0:
        raise ValueError(
            "target_number_of_orders must be positive."
        )

    if not 0 <= CONFIG.default_vat_rate <= 1:
        raise ValueError(
            "default_vat_rate must be between 0 and 1."
        )

    if (
        CONFIG.minimum_items_per_order
        > CONFIG.maximum_items_per_order
    ):
        raise ValueError(
            "Invalid order item limits."
        )

    if (
        CONFIG.minimum_customer_age
        >= CONFIG.maximum_customer_age
    ):
        raise ValueError(
            "Invalid customer age limits."
        )