# UAE Retail Intelligence Platform
## Business Requirements Document

## 1. Project Overview

UAE Retail Intelligence Platform is an end-to-end retail analytics platform built for a fictional retail company operating across the seven emirates of the United Arab Emirates.

The platform simulates retail operations from January 2023 through December 2025 and provides management with a centralized system for analyzing sales, profitability, customers, products, stores, returns, inventory, promotions, targets, and future sales forecasts.

The project covers the complete analytics lifecycle:

- Synthetic data generation
- Data validation
- SQL Server database design
- Data loading and transformation
- SQL business analysis
- Python exploratory data analysis
- Authentication and authorization
- SQL Server Row-Level Security
- Interactive dashboards
- Customer analytics
- Inventory analytics
- Forecasting
- Automated business insights


## 2. Business Scenario

The fictional company operates a network of 25 physical retail stores distributed across all seven UAE emirates.

The company sells products across multiple categories and brands and serves customers through both physical stores and digital sales channels.

Management requires a centralized analytics platform to monitor business performance and identify opportunities and operational problems.

The simulated historical period is:

2023-01-01 to 2025-12-31


## 3. Business Scale

The initial simulated environment will contain approximately:

- 7 Emirates
- 25 Stores
- Multiple cities
- 8 Product Categories
- Multiple Subcategories
- 60 Brands
- 800 Products
- 25,000 Customers
- 300 Employees
- 50 Suppliers
- Approximately 100,000 Orders
- Approximately 3 Order Items per Order
- Promotions
- Returns
- Inventory Movements
- Monthly Store Targets

These values are project targets and may be adjusted during data generation when necessary to preserve realistic business behavior.


## 4. Geographic Coverage

The business operates across all seven UAE emirates:

- Abu Dhabi
- Dubai
- Sharjah
- Ajman
- Umm Al Quwain
- Ras Al Khaimah
- Fujairah

Stores will be distributed across cities within these emirates.

Store performance and demand will vary according to location rather than all stores having identical behavior.


## 5. Sales Channels

The simulated company supports multiple sales channels.

Initial channels:

- Physical Store
- Online

The data model should allow additional channels to be introduced in the future without redesigning the entire database.


## 6. Product Structure

Products follow the hierarchy:

Category
→ Subcategory
→ Brand
→ Product

Products will contain business attributes including:

- Selling Price
- Cost
- Brand
- Category
- Subcategory
- Supplier
- Popularity
- Margin characteristics
- Seasonal characteristics
- Return probability
- Active / Inactive status

Product demand must not be uniformly random.

Different products will have different popularity, profitability, seasonality, promotion response, and return behavior.


## 7. Customer Model

The platform will simulate approximately 25,000 customers.

Customers may have different behavioral profiles such as:

- VIP
- Loyal
- Regular
- Discount Seeker
- At Risk

Customer behavior will influence:

- Purchase frequency
- Average order value
- Product preferences
- Promotion response
- Return probability

Customer behavior must be sufficiently realistic to support later RFM, cohort, retention, and segmentation analysis.


## 8. Sales Simulation

Approximately 100,000 orders will be generated across the three-year period.

Sales must not be generated using independent random values only.

Order demand will be influenced by factors including:

- Date
- Store
- Emirate
- Product popularity
- Customer behavior
- Sales channel
- Seasonality
- Promotions
- UAE events
- Business growth
- Random noise

Conceptually:

Demand =
Base Demand
× Store Effect
× Product Effect
× Customer Effect
× Seasonality
× Promotion Effect
× Trend
× Noise


## 9. UAE Seasonality

The simulation must reflect important UAE retail periods.

Examples include:

- Ramadan
- Eid Al Fitr
- Eid Al Adha
- Summer
- White Friday
- Eid Al Etihad
- Year End

The exact dates of date-dependent events should be stored by calendar year rather than assumed to occur on the same Gregorian dates every year.

These events may affect:

- Sales volume
- Product demand
- Discounts
- Customer traffic
- Sales channels


## 10. Promotions

The business will run promotional campaigns.

Promotion examples include:

- Percentage discounts
- Seasonal campaigns
- Product promotions
- Category promotions
- Store promotions

Each promotion can have:

- Start Date
- End Date
- Promotion Type
- Discount Value
- Applicable Product / Category
- Applicable Store
- Active Status

Promotions must influence simulated demand and not exist only as descriptive records.


## 11. Financial Rules

All monetary calculations must use fixed-precision decimal values.

FLOAT must not be used for financial amounts.

Each sales line should support calculation of:

Gross Sales

Gross Sales - Discount
= Net Sales Before VAT

VAT
= Applicable VAT Rate × Taxable Amount

Customer Total
= Net Sales Before VAT + VAT

Gross Profit
= Net Sales Before VAT - Cost of Goods Sold

Gross Margin %
= Gross Profit / Net Sales Before VAT × 100

For project reporting, VAT is not treated as revenue.

The standard simulated VAT rate for taxable transactions is 5%.

The data model should retain the VAT rate applied to the transaction so historical calculations do not depend on a hard-coded application value.


## 12. Returns

Customers may return eligible products after purchase.

Return behavior may depend on:

- Product
- Category
- Customer
- Store
- Product quality
- Return probability

Return records must always reference valid previous sales.

A return cannot occur before the original sale.

Return reasons may include:

- Defective Product
- Wrong Item
- Size / Fit Issue
- Changed Mind
- Damaged Product
- Other

Some controlled synthetic anomalies will intentionally be introduced into business behavior so they can later be detected through analysis.

These anomalies must remain valid from a database and accounting perspective.


## 13. Inventory

Inventory will be tracked through stock movements.

Supported movement types include:

- PURCHASE
- SALE
- RETURN
- TRANSFER_IN
- TRANSFER_OUT
- DAMAGED
- ADJUSTMENT

A product sale generates an inventory SALE movement.

A restockable return generates an inventory RETURN movement.

Inventory analysis should support:

- Stock on Hand
- Inventory Value
- Low Stock
- Stockouts
- Fast-Moving Products
- Slow-Moving Products
- Reorder Risk


## 14. Store Targets

Each store will receive monthly business targets.

Target measures include:

- Revenue Target
- Gross Profit Target
- Orders Target

Targets should be generated from historical performance, seasonality, and expected growth rather than independent random values.

The platform must compare actual performance with these targets.


## 15. Core Business Questions

The platform should answer questions such as:

- How much revenue is the company generating?
- How profitable is the business?
- Is revenue growing year over year?
- Which emirates generate the most revenue?
- Which stores are outperforming or underperforming?
- Which stores are meeting their targets?
- Which product categories generate the most revenue and profit?
- Which products have unusually high return rates?
- How dependent are products on discounts?
- Which customers generate the highest value?
- How many customers are new versus returning?
- What is the repeat purchase rate?
- Which customers are at risk of becoming inactive?
- What is customer retention by acquisition cohort?
- Which products are frequently purchased together?
- Which products are slow-moving?
- Which products are at risk of stockout?
- Which promotions increase demand?
- Are promotions improving revenue at the expense of profit?
- What business anomalies require management attention?
- What sales levels are expected during the next 30 and 90 days?


## 16. Analytics Requirements

The platform will support the following analytical areas:

### Executive Analytics

- Revenue
- Gross Profit
- Gross Margin
- Orders
- Units Sold
- Customers
- Average Order Value
- Return Rate
- Target Achievement
- YoY Growth

### Sales Analytics

- Daily Sales
- Weekly Sales
- Monthly Sales
- Year-over-Year Growth
- Month-over-Month Growth
- Channel Performance
- Payment Method Analysis
- Day-of-Week Analysis
- Seasonal Analysis

### Store Analytics

- Emirate Performance
- City Performance
- Store Performance
- Store Ranking
- Store Profitability
- Store Growth
- Target Achievement

### Product Analytics

- Category Performance
- Subcategory Performance
- Brand Performance
- Product Performance
- Top / Bottom Products
- Product Profitability
- Margin Analysis
- Discount Dependency
- Pareto Analysis
- Return Rate

### Customer Analytics

- Active Customers
- New Customers
- Returning Customers
- Repeat Rate
- Customer Revenue
- Purchase Frequency
- Average Order Value
- RFM Segmentation
- Cohort Retention

### Returns Analytics

- Return Rate
- Refund Amount
- Return Reasons
- Product Return Analysis
- Store Return Analysis
- Return Anomalies

### Inventory Analytics

- Stock on Hand
- Inventory Value
- Stockouts
- Low Stock
- Slow Movers
- Fast Movers
- Reorder Risk

### Target Analytics

- Actual vs Target
- Revenue Variance
- Profit Variance
- Orders Variance
- Target Achievement %

### Forecasting

The system should generate:

- 30-Day Sales Forecast
- 90-Day Sales Forecast

Forecasting models must be evaluated against baseline approaches before selecting the final model.


## 17. SQL Analytics Requirements

SQL Server will perform the primary relational processing and business aggregation.

SQL analysis should demonstrate:

- JOINs
- Aggregations
- CTEs
- CASE expressions
- Subqueries where appropriate
- Window Functions
- ROW_NUMBER
- RANK
- DENSE_RANK
- LAG
- LEAD
- Running Totals
- Moving Averages
- MoM Analysis
- YoY Analysis
- Customer Analysis
- RFM Analysis
- Cohort Analysis
- Pareto Analysis
- Product Rankings
- Store Rankings

Complex reusable analytics should be exposed through analytics views where appropriate.


## 18. Python EDA Requirements

Python will be used for exploratory and statistical analysis.

EDA areas include:

- Data distributions
- Missing values
- Duplicate analysis
- Outliers
- Sales distributions
- Customer behavior
- Product behavior
- Store behavior
- Correlation analysis where statistically appropriate
- Promotion analysis
- Seasonal patterns
- Time-series exploration
- Returns analysis
- Inventory behavior
- RFM analysis
- Cohort analysis
- Anomaly exploration

Python EDA should focus on discovering and explaining patterns rather than reproducing every SQL query.


## 19. User Roles

Initial application roles include:

### CEO

Access to company-wide analytics across all emirates and stores.

### Emirate Manager

Access limited to the manager's assigned emirate.

Example:

Dubai Manager
→ Dubai data only

### Store Manager

Access limited to the manager's assigned store.

### Sales Analyst

Access to permitted sales and commercial analytics according to assigned data scope.

### Inventory Analyst

Access to inventory-related functionality according to assigned data scope.

### Administrator

Access to administrative functionality such as user and permission management.

Administrative access does not automatically imply unrestricted business-data access unless explicitly granted.


## 20. Security Requirements

The platform must implement multiple security layers.

### Authentication

- Username / Email login
- Secure password hashing
- Disabled-user support
- Failed login handling
- Login / Logout tracking

Passwords must never be stored as plain text.

### Role-Based Access Control

RBAC controls application functionality and page access.

Examples:

CEO
→ Executive Analytics

Inventory Analyst
→ Inventory Analytics

Admin
→ User Management

### Row-Level Security

SQL Server Row-Level Security controls which business rows a user may access.

After authentication, the Python application will place the authenticated user context into SQL Server SESSION_CONTEXT.

SQL Server will enforce the permitted data scope.

Example:

CEO
→ All stores

Dubai Manager
→ Dubai stores only

Store Manager
→ Assigned store only

Application filters alone must never be considered a security boundary.


## 21. Global Filters

The analytical application should support cascading filters including:

- Date
- Emirate
- City
- Store
- Channel
- Category
- Subcategory
- Brand
- Customer Segment

Filter values must respect SQL Server Row-Level Security.


## 22. Data Quality Requirements

Critical validation should run before generated data is loaded.

Checks include:

- Duplicate Primary Keys
- Orphan Foreign Keys
- Invalid Prices
- Invalid Quantities
- Invalid Dates
- Invalid Financial Calculations
- Returns Before Sales
- Invalid Promotion Dates
- Invalid Inventory Movements

Critical validation failures must stop the loading pipeline.


## 23. Performance Requirements

SQL Server should perform major filtering, joins, and aggregations before data reaches the application whenever practical.

Indexes will be designed based on actual query patterns.

The project should avoid:

- Loading unnecessary raw data into Pandas
- Indexing every database column
- Repeating complex joins throughout the UI
- Sharing cached results between unauthorized user scopes


## 24. Audit Requirements

The system should record security-sensitive actions including:

- Successful Login
- Failed Login
- Logout
- Data Export
- Administrative Changes

Exports must respect the same data-access restrictions as dashboards.


## 25. Technology Stack

The planned technology stack includes:

Database:
- Microsoft SQL Server

Programming:
- Python

Database Connectivity:
- SQLAlchemy
- pyodbc

Data Analysis:
- Pandas
- NumPy

EDA / Statistical Analysis:
- Pandas
- NumPy
- Matplotlib
- Seaborn
- SciPy
- Plotly

Application:
- Streamlit

Visualization:
- Plotly

Security:
- Argon2 password hashing
- Application RBAC
- SQL Server Row-Level Security
- SESSION_CONTEXT

Testing:
- pytest

Forecasting:
- Python time-series libraries selected during the forecasting phase based on model requirements


## 26. Expected Final Deliverable

The final system should support the following flow:

User
→ Login
→ Authentication
→ RBAC
→ SQL SESSION_CONTEXT
→ SQL Server Row-Level Security
→ Analytics Queries
→ Global Filters
→ Streamlit Dashboards
→ Advanced Analytics
→ Forecasting
→ Secure Export / Audit


## 27. Primary Security Demonstration

The final project demonstration should include multiple accounts.

CEO
→ Can view all UAE operations.

Dubai Manager
→ Can view Dubai operations only.

Store Manager
→ Can view one assigned store only.

Inventory Analyst
→ Can access permitted inventory functionality within the assigned scope.

Attempts to retrieve unauthorized rows should be rejected by the database security layer rather than merely hidden by the user interface.


## 28. Project Success Criteria

The project will be considered successful when:

- Synthetic data reflects meaningful retail patterns.
- Database relationships maintain referential integrity.
- Financial calculations are consistent.
- Data quality checks pass.
- SQL analytics answer the defined business questions.
- Python EDA identifies meaningful patterns and anomalies.
- RLS prevents unauthorized row access.
- Application permissions correctly enforce functionality.
- Dashboards provide consistent KPI definitions.
- Forecasting is evaluated using time-aware validation.
- Performance remains acceptable for the simulated data scale.
- Tests cover critical financial, data-quality, analytics, and security logic.
- Documentation allows another developer to understand and run the project.