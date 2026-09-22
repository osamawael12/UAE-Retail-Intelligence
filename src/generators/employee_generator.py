"""
Synthetic employee generator.

Generates 300 employees across the 25 retail stores.

Business rules:
- Every employee belongs to a valid store.
- Every store has exactly one Store Manager.
- Store staffing levels vary according to store floor area.
- Hire dates never occur after the simulation end date.
- A small percentage of historical employees may be terminated.
- Employee codes and emails are unique.

This module does not connect to SQL Server.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from config.generation_config import CONFIG


FIRST_NAMES_MALE = [
    "Ahmed",
    "Mohammed",
    "Omar",
    "Ali",
    "Youssef",
    "Khalid",
    "Saeed",
    "Hassan",
    "Ibrahim",
    "Adam",
    "Daniel",
    "John",
    "Arjun",
    "Rahul",
    "Ravi",
    "Imran",
    "Bilal",
    "Samir",
    "Karim",
    "Faisal",
]


FIRST_NAMES_FEMALE = [
    "Fatima",
    "Aisha",
    "Mariam",
    "Sara",
    "Noor",
    "Layla",
    "Huda",
    "Amal",
    "Reem",
    "Hana",
    "Anna",
    "Maria",
    "Priya",
    "Ananya",
    "Meera",
    "Nadia",
    "Rania",
    "Dina",
    "Lina",
    "Zainab",
]


LAST_NAMES = [
    "Al Mansoori",
    "Al Mazrouei",
    "Al Nuaimi",
    "Al Shamsi",
    "Al Hammadi",
    "Khan",
    "Ahmed",
    "Ali",
    "Hassan",
    "Sharma",
    "Patel",
    "Singh",
    "Thomas",
    "George",
    "Rahman",
    "Santos",
    "Garcia",
    "Smith",
    "Brown",
    "Wilson",
]


NON_MANAGER_ROLES = [
    "Assistant Store Manager",
    "Sales Associate",
    "Senior Sales Associate",
    "Cashier",
    "Inventory Specialist",
    "Customer Service Associate",
]


NON_MANAGER_ROLE_WEIGHTS = [
    0.08,
    0.34,
    0.14,
    0.20,
    0.12,
    0.12,
]


def _random_date(
    rng: np.random.Generator,
    start_date: date,
    end_date: date,
) -> date:
    """
    Generate an inclusive random date.
    """

    if start_date > end_date:
        raise ValueError(
            "start_date cannot be after end_date."
        )

    number_of_days = (
        end_date - start_date
    ).days

    offset = int(
        rng.integers(
            0,
            number_of_days + 1,
        )
    )

    return (
        start_date
        + timedelta(days=offset)
    )


def _allocate_employee_counts(
    stores: pd.DataFrame,
) -> dict[int, int]:
    """
    Allocate the configured employee total across stores.

    Every store first receives one employee for its manager.
    Remaining employees are allocated according to floor area.
    """

    number_of_stores = len(stores)

    if number_of_stores != CONFIG.number_of_stores:
        raise ValueError(
            f"Expected {CONFIG.number_of_stores} stores, "
            f"found {number_of_stores}."
        )

    if CONFIG.number_of_employees < number_of_stores:
        raise ValueError(
            "Employee count must be at least "
            "the number of stores."
        )

    allocation = {
        int(store_id): 1
        for store_id in stores["StoreId"]
    }

    remaining_employees = (
        CONFIG.number_of_employees
        - number_of_stores
    )

    floor_area = (
        stores["FloorAreaSqM"]
        .astype(float)
        .to_numpy()
    )

    if (floor_area <= 0).any():
        raise ValueError(
            "All stores must have positive floor area."
        )

    weights = (
        floor_area
        / floor_area.sum()
    )

    raw_allocation = (
        weights
        * remaining_employees
    )

    base_allocation = (
        np.floor(raw_allocation)
        .astype(int)
    )

    for index, store_id in enumerate(
        stores["StoreId"]
    ):
        allocation[int(store_id)] += int(
            base_allocation[index]
        )

    allocated = int(
        base_allocation.sum()
    )

    employees_left = (
        remaining_employees
        - allocated
    )

    fractional_parts = (
        raw_allocation
        - base_allocation
    )

    priority_indices = (
        np.argsort(
            -fractional_parts
        )
    )

    for index in (
        priority_indices[
            :employees_left
        ]
    ):
        store_id = int(
            stores.iloc[index][
                "StoreId"
            ]
        )

        allocation[store_id] += 1

    if (
        sum(allocation.values())
        != CONFIG.number_of_employees
    ):
        raise ValueError(
            "Employee allocation does not "
            "match configured total."
        )

    return allocation


def generate_employees(
    stores: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate the employee master dataset.
    """

    rng = np.random.default_rng(
        CONFIG.random_seed + 500
    )

    stores = (
        stores
        .sort_values("StoreId")
        .reset_index(drop=True)
    )

    allocation = (
        _allocate_employee_counts(
            stores=stores,
        )
    )

    employee_rows = []

    employee_id = 1

    for store in stores.itertuples(
        index=False
    ):
        store_id = int(
            store.StoreId
        )

        store_open_date = (
            pd.to_datetime(
                store.OpenDate
            ).date()
        )

        employee_count = allocation[
            store_id
        ]

        for position in range(
            employee_count
        ):
            if position == 0:
                job_title = (
                    "Store Manager"
                )
            else:
                job_title = str(
                    rng.choice(
                        NON_MANAGER_ROLES,
                        p=(
                            NON_MANAGER_ROLE_WEIGHTS
                        ),
                    )
                )

            gender_for_name = str(
                rng.choice(
                    [
                        "MALE",
                        "FEMALE",
                    ],
                    p=[
                        0.52,
                        0.48,
                    ],
                )
            )

            if (
                gender_for_name
                == "MALE"
            ):
                first_name = str(
                    rng.choice(
                        FIRST_NAMES_MALE
                    )
                )
            else:
                first_name = str(
                    rng.choice(
                        FIRST_NAMES_FEMALE
                    )
                )

            last_name = str(
                rng.choice(
                    LAST_NAMES
                )
            )

            earliest_hire_date = max(
                store_open_date,
                date(
                    2015,
                    1,
                    1,
                ),
            )

            latest_hire_date = (
                CONFIG.end_date
            )

            hire_date = (
                _random_date(
                    rng=rng,
                    start_date=(
                        earliest_hire_date
                    ),
                    end_date=(
                        latest_hire_date
                    ),
                )
            )

            termination_date = None
            is_active = 1

            # Store managers stay active in the simulation
            # so each store always retains its manager.
            if (
                job_title
                != "Store Manager"
                and hire_date
                <= date(
                    2025,
                    6,
                    30,
                )
                and rng.random()
                < 0.06
            ):
                minimum_termination = (
                    hire_date
                    + timedelta(
                        days=90
                    )
                )

                if (
                    minimum_termination
                    <= CONFIG.end_date
                ):
                    termination_date = (
                        _random_date(
                            rng=rng,
                            start_date=(
                                minimum_termination
                            ),
                            end_date=(
                                CONFIG.end_date
                            ),
                        )
                    )

                    is_active = 0

            employee_code = (
                f"EMP"
                f"{employee_id:05d}"
            )

            email = (
                f"employee"
                f"{employee_id:05d}"
                "@synthetic-retail.ae"
            )

            employee_rows.append(
                {
                    "EmployeeId": (
                        employee_id
                    ),
                    "StoreId": (
                        store_id
                    ),
                    "EmployeeCode": (
                        employee_code
                    ),
                    "FirstName": (
                        first_name
                    ),
                    "LastName": (
                        last_name
                    ),
                    "JobTitle": (
                        job_title
                    ),
                    "HireDate": (
                        hire_date
                    ),
                    "TerminationDate": (
                        termination_date
                    ),
                    "Email": email,
                    "IsActive": (
                        is_active
                    ),
                }
            )

            employee_id += 1

    employees = pd.DataFrame(
        employee_rows
    )

    validate_employee_data(
        employees=employees,
        stores=stores,
    )

    return employees


def validate_employee_data(
    employees: pd.DataFrame,
    stores: pd.DataFrame,
) -> None:
    """
    Validate employee business rules.
    """

    if (
        len(employees)
        != CONFIG.number_of_employees
    ):
        raise ValueError(
            "Incorrect number of employees. "
            f"Expected "
            f"{CONFIG.number_of_employees}, "
            f"found {len(employees)}."
        )

    unique_columns = [
        "EmployeeId",
        "EmployeeCode",
        "Email",
    ]

    for column in unique_columns:
        if not employees[
            column
        ].is_unique:
            raise ValueError(
                f"Duplicate employee "
                f"{column} detected."
            )

    if employees[
        "EmployeeId"
    ].isna().any():
        raise ValueError(
            "EmployeeId contains nulls."
        )

    if employees[
        "StoreId"
    ].isna().any():
        raise ValueError(
            "StoreId contains nulls."
        )

    if not employees[
        "StoreId"
    ].isin(
        stores[
            "StoreId"
        ]
    ).all():
        raise ValueError(
            "Employee references an "
            "invalid StoreId."
        )

    if employees[
        "HireDate"
    ].isna().any():
        raise ValueError(
            "HireDate contains nulls."
        )

    hire_dates = pd.to_datetime(
        employees["HireDate"]
    )

    termination_dates = (
        pd.to_datetime(
            employees[
                "TerminationDate"
            ],
            errors="coerce",
        )
    )

    invalid_termination = (
        termination_dates.notna()
        & (
            termination_dates
            < hire_dates
        )
    )

    if invalid_termination.any():
        raise ValueError(
            "TerminationDate before "
            "HireDate detected."
        )

    if (
        hire_dates.dt.date
        > CONFIG.end_date
    ).any():
        raise ValueError(
            "Employee hired after "
            "simulation period."
        )

    active_with_termination = (
        (
            employees["IsActive"]
            == 1
        )
        & termination_dates.notna()
    )

    if active_with_termination.any():
        raise ValueError(
            "Active employee has a "
            "TerminationDate."
        )

    inactive_without_termination = (
        (
            employees["IsActive"]
            == 0
        )
        & termination_dates.isna()
    )

    if inactive_without_termination.any():
        raise ValueError(
            "Inactive employee is missing "
            "TerminationDate."
        )

    if not employees[
        "IsActive"
    ].isin(
        [0, 1]
    ).all():
        raise ValueError(
            "Invalid IsActive value."
        )

    manager_counts = (
        employees.loc[
            employees["JobTitle"]
            == "Store Manager"
        ]
        .groupby("StoreId")
        .size()
    )

    all_store_ids = set(
        stores["StoreId"]
        .astype(int)
    )

    manager_store_ids = set(
        manager_counts.index
        .astype(int)
    )

    if (
        manager_store_ids
        != all_store_ids
    ):
        raise ValueError(
            "Every store must have "
            "a Store Manager."
        )

    if not (
        manager_counts == 1
    ).all():
        raise ValueError(
            "Every store must have "
            "exactly one Store Manager."
        )

    employees_per_store = (
        employees
        .groupby("StoreId")
        .size()
    )

    if (
        employees_per_store
        <= 0
    ).any():
        raise ValueError(
            "A store has no employees."
        )