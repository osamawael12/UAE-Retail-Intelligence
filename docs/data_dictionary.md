# UAE Retail Intelligence Platform
## Data Dictionary

## 1. Standards

Database: `UAERetailAnalytics`

SQL Server schemas:

- core
- product
- customer
- sales
- inventory
- hr
- security
- analytics

General conventions:

- Surrogate primary keys use `INT IDENTITY(1,1)` unless stated otherwise.
- Monetary values use `DECIMAL(19,4)`.
- Rates and percentages use `DECIMAL(9,4)`.
- Probabilities and simulation scores use `DECIMAL(9,6)`.
- Quantities use `INT`.
- Business timestamps use `DATETIME2(0)`.
- Technical/audit timestamps use `DATETIME2(3)`.
- Dates use `DATE`.
- Flags use `BIT`.
- Unicode business text uses `NVARCHAR`.
- Codes use `VARCHAR` where values are controlled ASCII identifiers.
- Historical financial values are stored on transaction lines.
- UTC should be used for technical/security timestamps. Simulated retail transaction timestamps represent UAE local business time unless explicitly stated otherwise.


# 2. core Schema

## core.Emirate

| Column | Type | Null | Key / Constraint | Description |
|---|---|---:|---|---|
| EmirateId | INT IDENTITY | No | PK | Emirate identifier |
| EmirateCode | VARCHAR(10) | No | UNIQUE | Short business code |
| EmirateName | NVARCHAR(50) | No | UNIQUE | Emirate name |
| IsActive | BIT | No | DEFAULT 1 | Active flag |

Expected rows: 7.


## core.City

| Column | Type | Null | Key / Constraint | Description |
|---|---|---:|---|---|
| CityId | INT IDENTITY | No | PK | City identifier |
| EmirateId | INT | No | FK → core.Emirate | Parent emirate |
| CityName | NVARCHAR(100) | No | | City name |
| IsActive | BIT | No | DEFAULT 1 | Active flag |

Unique business key:

`(EmirateId, CityName)`


## core.Store

| Column | Type | Null | Key / Constraint | Description |
|---|---|---:|---|---|
| StoreId | INT IDENTITY | No | PK | Store identifier |
| CityId | INT | No | FK → core.City | Store city |
| StoreCode | VARCHAR(20) | No | UNIQUE | Store business code |
| StoreName | NVARCHAR(150) | No | | Store name |
| OpenDate | DATE | No | | Opening date |
| StoreType | VARCHAR(30) | No | CHECK | Store format/type |
| FloorAreaSqM | DECIMAL(10,2) | Yes | CHECK > 0 | Approximate floor area |
| IsActive | BIT | No | DEFAULT 1 | Active flag |


## core.DateDimension

`DateKey` uses integer format `YYYYMMDD`.

| Column | Type | Null | Key / Constraint | Description |
|---|---|---:|---|---|
| DateKey | INT | No | PK | Calendar key |
| FullDate | DATE | No | UNIQUE | Calendar date |
| DayNumber | TINYINT | No | | Day of month |
| DayName | VARCHAR(10) | No | | English day name |
| DayOfWeekNumber | TINYINT | No | CHECK 1–7 | ISO-style weekday number |
| WeekOfYear | TINYINT | No | | Week number |
| MonthNumber | TINYINT | No | CHECK 1–12 | Month number |
| MonthName | VARCHAR(10) | No | | English month name |
| QuarterNumber | TINYINT | No | CHECK 1–4 | Quarter |
| YearNumber | SMALLINT | No | | Calendar year |
| IsWeekend | BIT | No | | Weekend flag |
| IsRamadan | BIT | No | DEFAULT 0 | Ramadan flag |
| IsEidAlFitr | BIT | No | DEFAULT 0 | Eid Al Fitr flag |
| IsEidAlAdha | BIT | No | DEFAULT 0 | Eid Al Adha flag |
| IsWhiteFriday | BIT | No | DEFAULT 0 | White Friday period |
| IsEidAlEtihad | BIT | No | DEFAULT 0 | UAE National Day / Eid Al Etihad period |
| IsSummer | BIT | No | DEFAULT 0 | Summer period |
| IsYearEndSeason | BIT | No | DEFAULT 0 | Year-end retail period |


## core.SalesChannel

| Column | Type | Null | Key / Constraint | Description |
|---|---|---:|---|---|
| SalesChannelId | SMALLINT IDENTITY | No | PK | Channel identifier |
| ChannelCode | VARCHAR(20) | No | UNIQUE | Controlled code |
| ChannelName | NVARCHAR(50) | No | UNIQUE | Display name |
| IsActive | BIT | No | DEFAULT 1 | Active flag |


## core.PaymentMethod

| Column | Type | Null | Key / Constraint | Description |
|---|---|---:|---|---|
| PaymentMethodId | SMALLINT IDENTITY | No | PK | Payment method identifier |
| PaymentMethodCode | VARCHAR(30) | No | UNIQUE | Controlled code |
| PaymentMethodName | NVARCHAR(50) | No | UNIQUE | Display name |
| IsActive | BIT | No | DEFAULT 1 | Active flag |


# 3. product Schema

## product.Category

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| CategoryId | INT IDENTITY | No | PK |
| CategoryName | NVARCHAR(100) | No | UNIQUE |
| IsActive | BIT | No | DEFAULT 1 |


## product.Subcategory

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| SubcategoryId | INT IDENTITY | No | PK |
| CategoryId | INT | No | FK → product.Category |
| SubcategoryName | NVARCHAR(100) | No | |
| IsActive | BIT | No | DEFAULT 1 |

Unique business key:

`(CategoryId, SubcategoryName)`


## product.Brand

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| BrandId | INT IDENTITY | No | PK |
| BrandName | NVARCHAR(100) | No | UNIQUE |
| IsActive | BIT | No | DEFAULT 1 |


## product.Supplier

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| SupplierId | INT IDENTITY | No | PK |
| SupplierCode | VARCHAR(20) | No | UNIQUE |
| SupplierName | NVARCHAR(150) | No | |
| ContactEmail | NVARCHAR(254) | Yes | |
| ContactPhone | VARCHAR(30) | Yes | |
| IsActive | BIT | No | DEFAULT 1 |


## product.Product

| Column | Type | Null | Key / Constraint | Description |
|---|---|---:|---|---|
| ProductId | INT IDENTITY | No | PK | Product identifier |
| SubcategoryId | INT | No | FK → product.Subcategory | Product hierarchy |
| BrandId | INT | No | FK → product.Brand | Product brand |
| SKU | VARCHAR(30) | No | UNIQUE | Stock keeping unit |
| ProductName | NVARCHAR(200) | No | | Product name |
| BaseSellingPrice | DECIMAL(19,4) | No | CHECK >= 0 | Current/base price |
| StandardCost | DECIMAL(19,4) | No | CHECK >= 0 | Current standard cost |
| DefaultVATRate | DECIMAL(9,6) | No | CHECK 0–1 | Default rate, e.g. 0.05 |
| PopularityScore | DECIMAL(9,6) | No | CHECK 0–1 | Simulation attribute |
| SeasonalityProfile | VARCHAR(30) | No | | Simulation profile |
| BaseReturnProbability | DECIMAL(9,6) | No | CHECK 0–1 | Simulation probability |
| LaunchDate | DATE | No | | Product launch |
| DiscontinuedDate | DATE | Yes | CHECK >= LaunchDate | End date |
| IsActive | BIT | No | DEFAULT 1 | Active flag |


## product.ProductSupplier

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| ProductId | INT | No | PK, FK → product.Product |
| SupplierId | INT | No | PK, FK → product.Supplier |
| SupplierProductCode | VARCHAR(50) | Yes | |
| SupplierCost | DECIMAL(19,4) | No | CHECK >= 0 |
| LeadTimeDays | SMALLINT | No | CHECK >= 0 |
| IsPrimarySupplier | BIT | No | DEFAULT 0 |
| IsActive | BIT | No | DEFAULT 1 |

A filtered unique index will later ensure a product has at most one active primary supplier.


# 4. customer Schema

## customer.Customer

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| CustomerId | INT IDENTITY | No | PK |
| CustomerCode | VARCHAR(30) | No | UNIQUE |
| FirstName | NVARCHAR(100) | No | |
| LastName | NVARCHAR(100) | No | |
| Gender | VARCHAR(20) | Yes | |
| DateOfBirth | DATE | Yes | |
| Email | NVARCHAR(254) | Yes | |
| Phone | VARCHAR(30) | Yes | |
| Nationality | NVARCHAR(100) | Yes | |
| RegistrationDate | DATE | No | |
| PreferredEmirateId | INT | Yes | FK → core.Emirate |
| PreferredChannelId | SMALLINT | Yes | FK → core.SalesChannel |
| IsActive | BIT | No | DEFAULT 1 |


## customer.CustomerSegmentHistory

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| CustomerSegmentHistoryId | BIGINT IDENTITY | No | PK |
| CustomerId | INT | No | FK → customer.Customer |
| SegmentName | VARCHAR(50) | No | |
| EffectiveFrom | DATE | No | |
| EffectiveTo | DATE | Yes | CHECK >= EffectiveFrom |
| IsCurrent | BIT | No | DEFAULT 0 |

A filtered unique index will later allow at most one `IsCurrent = 1` row per customer.


# 5. hr Schema

## hr.Employee

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| EmployeeId | INT IDENTITY | No | PK |
| StoreId | INT | Yes | FK → core.Store |
| EmployeeCode | VARCHAR(20) | No | UNIQUE |
| FirstName | NVARCHAR(100) | No | |
| LastName | NVARCHAR(100) | No | |
| JobTitle | NVARCHAR(100) | No | |
| HireDate | DATE | No | |
| TerminationDate | DATE | Yes | CHECK >= HireDate |
| Email | NVARCHAR(254) | Yes | |
| IsActive | BIT | No | DEFAULT 1 |


# 6. sales Schema — Promotions

## sales.Promotion

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| PromotionId | INT IDENTITY | No | PK |
| PromotionCode | VARCHAR(30) | No | UNIQUE |
| PromotionName | NVARCHAR(150) | No | |
| PromotionType | VARCHAR(30) | No | CHECK |
| DiscountType | VARCHAR(20) | No | CHECK |
| DiscountValue | DECIMAL(19,4) | No | CHECK >= 0 |
| StartDate | DATE | No | |
| EndDate | DATE | No | CHECK >= StartDate |
| IsActive | BIT | No | DEFAULT 1 |

For percentage discounts, additional DDL validation will ensure the configured value is within the selected representation's valid range.


## sales.PromotionProduct

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| PromotionId | INT | No | PK, FK → sales.Promotion |
| ProductId | INT | No | PK, FK → product.Product |


## sales.PromotionCategory

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| PromotionId | INT | No | PK, FK → sales.Promotion |
| CategoryId | INT | No | PK, FK → product.Category |


## sales.PromotionStore

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| PromotionId | INT | No | PK, FK → sales.Promotion |
| StoreId | INT | No | PK, FK → core.Store |


# 7. sales Schema — Orders

## sales.SalesOrder

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| OrderId | BIGINT IDENTITY | No | PK |
| OrderNumber | VARCHAR(30) | No | UNIQUE |
| CustomerId | INT | No | FK → customer.Customer |
| StoreId | INT | No | FK → core.Store |
| SalesChannelId | SMALLINT | No | FK → core.SalesChannel |
| DateKey | INT | No | FK → core.DateDimension |
| OrderDateTime | DATETIME2(0) | No | |
| OrderStatus | VARCHAR(20) | No | CHECK |
| GrossAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| DiscountAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| NetAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| VATAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| CustomerTotal | DECIMAL(19,4) | No | CHECK >= 0 |
| CreatedAt | DATETIME2(3) | No | DEFAULT SYSUTCDATETIME() |

Header totals must reconcile to item totals within the project's decimal rounding rules.


## sales.SalesOrderItem

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| OrderItemId | BIGINT IDENTITY | No | PK |
| OrderId | BIGINT | No | FK → sales.SalesOrder |
| ProductId | INT | No | FK → product.Product |
| PromotionId | INT | Yes | FK → sales.Promotion |
| Quantity | SMALLINT | No | CHECK > 0 |
| UnitPrice | DECIMAL(19,4) | No | CHECK >= 0 |
| UnitCost | DECIMAL(19,4) | No | CHECK >= 0 |
| GrossAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| DiscountAmount | DECIMAL(19,4) | No | CHECK >= 0 AND <= GrossAmount |
| NetAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| VATRate | DECIMAL(9,6) | No | CHECK 0–1 |
| VATAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| CustomerTotal | DECIMAL(19,4) | No | CHECK >= 0 |
| LineCOGS | DECIMAL(19,4) | No | CHECK >= 0 |

Expected rules:

`GrossAmount = UnitPrice × Quantity`

`NetAmount = GrossAmount - DiscountAmount`

`VATAmount = NetAmount × VATRate`

`CustomerTotal = NetAmount + VATAmount`

`LineCOGS = UnitCost × Quantity`

Exact reconciliation uses documented monetary rounding.


## sales.OrderPayment

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| OrderPaymentId | BIGINT IDENTITY | No | PK |
| OrderId | BIGINT | No | FK → sales.SalesOrder |
| PaymentMethodId | SMALLINT | No | FK → core.PaymentMethod |
| PaymentAmount | DECIMAL(19,4) | No | CHECK > 0 |
| PaymentDateTime | DATETIME2(0) | No | |
| PaymentReference | VARCHAR(100) | Yes | |


# 8. sales Schema — Returns

## sales.Return

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| ReturnId | BIGINT IDENTITY | No | PK |
| ReturnNumber | VARCHAR(30) | No | UNIQUE |
| OrderId | BIGINT | No | FK → sales.SalesOrder |
| StoreId | INT | No | FK → core.Store |
| DateKey | INT | No | FK → core.DateDimension |
| ReturnDateTime | DATETIME2(0) | No | |
| ReturnStatus | VARCHAR(20) | No | CHECK |
| TotalReturnNetAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| TotalVATReversed | DECIMAL(19,4) | No | CHECK >= 0 |
| TotalRefundAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| CreatedAt | DATETIME2(3) | No | DEFAULT SYSUTCDATETIME() |

Cross-table validation must ensure return time is not before original order time.


## sales.ReturnItem

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| ReturnItemId | BIGINT IDENTITY | No | PK |
| ReturnId | BIGINT | No | FK → sales.Return |
| OrderItemId | BIGINT | No | FK → sales.SalesOrderItem |
| ReturnQuantity | SMALLINT | No | CHECK > 0 |
| ReturnReason | VARCHAR(50) | No | CHECK |
| ReturnedNetAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| VATReversed | DECIMAL(19,4) | No | CHECK >= 0 |
| RefundAmount | DECIMAL(19,4) | No | CHECK >= 0 |
| IsRestockable | BIT | No | DEFAULT 1 |

Cross-row validation must ensure cumulative returned quantity never exceeds the original sold quantity.


## sales.Refund

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| RefundId | BIGINT IDENTITY | No | PK |
| ReturnId | BIGINT | No | FK → sales.Return |
| PaymentMethodId | SMALLINT | No | FK → core.PaymentMethod |
| RefundAmount | DECIMAL(19,4) | No | CHECK > 0 |
| RefundDateTime | DATETIME2(0) | No | |
| RefundReference | VARCHAR(100) | Yes | |
| RefundStatus | VARCHAR(20) | No | CHECK |


# 9. sales Schema — Targets

## sales.StoreMonthlyTarget

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| StoreMonthlyTargetId | BIGINT IDENTITY | No | PK |
| StoreId | INT | No | FK → core.Store |
| TargetYear | SMALLINT | No | CHECK |
| TargetMonth | TINYINT | No | CHECK 1–12 |
| RevenueTarget | DECIMAL(19,4) | No | CHECK >= 0 |
| GrossProfitTarget | DECIMAL(19,4) | No | CHECK >= 0 |
| OrdersTarget | INT | No | CHECK >= 0 |
| CreatedAt | DATETIME2(3) | No | DEFAULT SYSUTCDATETIME() |

Unique constraint:

`(StoreId, TargetYear, TargetMonth)`


# 10. inventory Schema

## inventory.StoreProductInventory

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| StoreId | INT | No | PK, FK → core.Store |
| ProductId | INT | No | PK, FK → product.Product |
| ReorderPoint | INT | No | CHECK >= 0 |
| ReorderQuantity | INT | No | CHECK > 0 |
| CurrentStock | INT | No | |
| LastUpdatedAt | DATETIME2(3) | No | |

Whether negative operational stock is allowed will be fixed in inventory business rules. The initial simulation should normally prevent inventory from falling below zero.


## inventory.InventoryMovement

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| InventoryMovementId | BIGINT IDENTITY | No | PK |
| StoreId | INT | No | FK → core.Store |
| ProductId | INT | No | FK → product.Product |
| OrderItemId | BIGINT | Yes | FK → sales.SalesOrderItem |
| ReturnItemId | BIGINT | Yes | FK → sales.ReturnItem |
| MovementDateTime | DATETIME2(0) | No | |
| MovementType | VARCHAR(20) | No | CHECK |
| QuantityChange | INT | No | CHECK <> 0 |
| UnitCost | DECIMAL(19,4) | No | CHECK >= 0 |
| ReferenceNumber | VARCHAR(100) | Yes | |
| Notes | NVARCHAR(500) | Yes | |

Movement sign convention:

- PURCHASE → positive
- SALE → negative
- RETURN → positive
- TRANSFER_IN → positive
- TRANSFER_OUT → negative
- DAMAGED → negative
- ADJUSTMENT → positive or negative

DDL/database validation should enforce valid sign/type combinations where practical.


# 11. security Schema

## security.AppUser

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| UserId | INT IDENTITY | No | PK |
| Username | NVARCHAR(100) | No | UNIQUE |
| Email | NVARCHAR(254) | No | UNIQUE |
| PasswordHash | NVARCHAR(500) | No | |
| IsActive | BIT | No | DEFAULT 1 |
| FailedLoginCount | INT | No | DEFAULT 0, CHECK >= 0 |
| LastLoginAt | DATETIME2(3) | Yes | |
| CreatedAt | DATETIME2(3) | No | DEFAULT SYSUTCDATETIME() |
| UpdatedAt | DATETIME2(3) | No | DEFAULT SYSUTCDATETIME() |


## security.Role

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| RoleId | INT IDENTITY | No | PK |
| RoleName | NVARCHAR(100) | No | UNIQUE |
| Description | NVARCHAR(500) | Yes | |


## security.Permission

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| PermissionId | INT IDENTITY | No | PK |
| PermissionCode | VARCHAR(100) | No | UNIQUE |
| PermissionName | NVARCHAR(150) | No | |
| Description | NVARCHAR(500) | Yes | |


## security.UserRole

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| UserId | INT | No | PK, FK → security.AppUser |
| RoleId | INT | No | PK, FK → security.Role |


## security.RolePermission

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| RoleId | INT | No | PK, FK → security.Role |
| PermissionId | INT | No | PK, FK → security.Permission |


## security.UserDataScope

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| UserDataScopeId | INT IDENTITY | No | PK |
| UserId | INT | No | FK → security.AppUser |
| ScopeType | VARCHAR(20) | No | CHECK ALL / EMIRATE / STORE |
| EmirateId | INT | Yes | FK → core.Emirate |
| StoreId | INT | Yes | FK → core.Store |
| IsActive | BIT | No | DEFAULT 1 |

Scope consistency rules:

- ALL → EmirateId NULL and StoreId NULL
- EMIRATE → EmirateId required and StoreId NULL
- STORE → StoreId required and EmirateId NULL

A user may have multiple active scopes if future business requirements require it.


## security.AuditLog

| Column | Type | Null | Key / Constraint |
|---|---|---:|---|
| AuditLogId | BIGINT IDENTITY | No | PK |
| UserId | INT | Yes | FK → security.AppUser |
| EventType | VARCHAR(50) | No | |
| EventDateTime | DATETIME2(3) | No | DEFAULT SYSUTCDATETIME() |
| Success | BIT | No | |
| IPAddress | VARCHAR(45) | Yes | |
| Details | NVARCHAR(2000) | Yes | |


# 12. analytics Schema

The analytics schema will primarily contain views.

Planned objects:

- analytics.vw_SalesDetail
- analytics.vw_DailySales
- analytics.vw_StorePerformance
- analytics.vw_ProductPerformance
- analytics.vw_Customer360
- analytics.vw_ReturnAnalysis
- analytics.vw_InventoryStatus
- analytics.vw_TargetPerformance

These views will be designed after transactional data and query patterns have been validated.


# 13. Controlled Values

Exact SQL CHECK constraints will be created in DDL.

Initial controlled values include:

### OrderStatus

- COMPLETED
- CANCELLED

### ReturnStatus

- COMPLETED
- REJECTED

### RefundStatus

- COMPLETED
- PENDING
- FAILED

### MovementType

- PURCHASE
- SALE
- RETURN
- TRANSFER_IN
- TRANSFER_OUT
- DAMAGED
- ADJUSTMENT

### DiscountType

- PERCENTAGE
- FIXED_AMOUNT

### ScopeType

- ALL
- EMIRATE
- STORE


# 14. Financial Precision

The canonical calculation order is:

```text
GrossAmount
= UnitPrice × Quantity

DiscountAmount
= calculated discount

NetAmount
= GrossAmount - DiscountAmount

VATAmount
= NetAmount × VATRate

CustomerTotal
= NetAmount + VATAmount

LineCOGS
= UnitCost × Quantity
```

Calculated monetary outputs are rounded according to one centrally defined Python/SQL rounding policy before persistence.

VAT is not Revenue.


# 15. Cross-Table Rules

Some business rules cannot be reliably implemented using a simple SQL Server CHECK constraint because CHECK constraints cannot enforce arbitrary cross-row/cross-table logic.

These rules require generator validation, database loading logic, procedures where appropriate, and automated tests.

Examples:

1. ReturnDateTime must be on or after the original OrderDateTime.

2. Total returned quantity for an OrderItem must not exceed sold Quantity.

3. SalesOrder header totals must equal the corresponding line totals.

4. Return header totals must equal ReturnItem totals.

5. Completed payment totals must reconcile with the amount expected for the order under the selected payment model.

6. Refund totals must not exceed the refundable amount.

7. SALE inventory movements must correspond to valid sales lines.

8. Restockable returns must generate appropriate RETURN inventory movements.

9. Product sales cannot occur before Product.LaunchDate.

10. Customer purchases cannot occur before Customer.RegistrationDate.


# 16. Expected Initial Data Volume

Approximate project targets:

| Entity | Approximate Rows |
|---|---:|
| Emirate | 7 |
| City | 15–30 |
| Store | 25 |
| Category | 8 |
| Subcategory | 30–50 |
| Brand | 60 |
| Product | 800 |
| Supplier | 50 |
| ProductSupplier | 800–1,500 |
| Customer | 25,000 |
| Employee | 300 |
| SalesOrder | ~100,000 |
| SalesOrderItem | ~300,000 |
| Return / ReturnItem | Generated from behavior |
| InventoryMovement | Several hundred thousand |
| StoreMonthlyTarget | ~900 |

Exact transactional counts depend on the synthetic business simulation.


# 17. Source of Truth

This data dictionary is the design specification for SQL DDL.

Implementation flow:

```text
Business Requirements
        ↓
KPI Definitions
        ↓
ERD
        ↓
Data Dictionary
        ↓
SQL DDL
        ↓
Synthetic Data Generator
        ↓
Validation
        ↓
Bulk Load
```

Any structural database change should be reflected in this document.