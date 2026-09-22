# 🇦🇪 UAE Retail Intelligence Platform

> An end-to-end retail analytics, business intelligence, and decision-support platform built with Python, SQL Server, and Streamlit.

The **UAE Retail Intelligence Platform** is a comprehensive portfolio project designed to simulate and analyze the operations of a multi-store retail business operating across the United Arab Emirates.

The project covers the complete analytics lifecycle — from synthetic data generation and relational database design to data quality validation, advanced SQL analytics, exploratory data analysis, customer segmentation, inventory monitoring, promotion analysis, security controls, and an interactive Streamlit dashboard.

Rather than focusing only on visualization, this project demonstrates how a complete analytics solution can be designed across multiple layers:

- Data generation
- Data modeling
- Database engineering
- Data validation
- SQL analytics
- Exploratory data analysis
- Customer intelligence
- Product and store performance
- Inventory analytics
- Returns analysis
- Promotion analytics
- KPI tracking
- Row-level security
- Authentication
- Interactive BI dashboards

The goal is to provide a realistic analytical environment for answering retail business questions and supporting data-driven decision-making.

---

# 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [Business Objectives](#-business-objectives)
3. [Key Features](#-key-features)
4. [Technology Stack](#-technology-stack)
5. [Project Architecture](#-project-architecture)
6. [Repository Structure](#-repository-structure)
7. [Data Model](#-data-model)
8. [Synthetic Data Generation](#-synthetic-data-generation)
9. [Database Layer](#-database-layer)
10. [Data Quality Framework](#-data-quality-framework)
11. [SQL Analytics](#-sql-analytics)
12. [Exploratory Data Analysis](#-exploratory-data-analysis)
13. [Customer Analytics](#-customer-analytics)
14. [RFM Segmentation](#-rfm-segmentation)
15. [Cohort Analysis](#-cohort-analysis)
16. [Store Analytics](#-store-analytics)
17. [Product Analytics](#-product-analytics)
18. [Returns Analytics](#-returns-analytics)
19. [Inventory Analytics](#-inventory-analytics)
20. [Promotion Analytics](#-promotion-analytics)
21. [Target Analysis](#-target-analysis)
22. [Security Architecture](#-security-architecture)
23. [Streamlit Dashboard](#-streamlit-dashboard)
24. [Dashboard Pages](#-dashboard-pages)
25. [Installation](#-installation)
26. [Environment Configuration](#-environment-configuration)
27. [Running the Project](#-running-the-project)
28. [Running the Dashboard](#-running-the-dashboard)
29. [Reproducing the Data](#-reproducing-the-data)
30. [Documentation](#-documentation)
31. [Future Improvements](#-future-improvements)
32. [Author](#-author)

---

# 🎯 Project Overview

Retail organizations generate data across many operational areas:

- Orders
- Products
- Customers
- Stores
- Inventory
- Promotions
- Returns
- Payments
- Employees
- Sales channels
- Targets

However, raw transactional data alone does not provide business value.

The challenge is transforming these datasets into meaningful information that can answer questions such as:

- How is revenue changing over time?
- Which stores are driving the strongest performance?
- Which product categories contribute the most revenue and profit?
- Which customers generate the most value?
- How concentrated is revenue among top customers?
- Which customers are at risk of becoming inactive?
- How effective are promotional campaigns?
- Are discounts improving revenue at the expense of margin?
- Which products have unusually high return rates?
- Which inventory items are slow-moving?
- Which products may require replenishment?
- Which stores are meeting their sales targets?
- How does customer retention evolve after acquisition?
- Which products contribute the majority of revenue?
- Are there seasonal patterns in retail demand?

This project was designed to answer these questions through a structured analytics architecture.

---

# 💼 Business Objectives

The platform focuses on several core retail intelligence objectives.

### Revenue Performance

Monitor revenue trends across time, stores, products, categories, emirates, and sales channels.

### Profitability

Evaluate business performance beyond revenue by analyzing margins and the impact of discounts and returns.

### Customer Intelligence

Understand customer behavior through purchasing frequency, monetary value, recency, preferred channels, and geographical behavior.

### Customer Retention

Analyze customer retention using cohort analysis and identify engagement patterns over time.

### Product Performance

Identify high-performing products, brands, and categories while detecting products with weak performance or excessive discount dependency.

### Store Performance

Compare stores based on revenue, margin, returns, and other operational KPIs.

### Inventory Optimization

Monitor stock positions and identify:

- Reorder candidates
- Slow-moving products
- Inventory concentration
- Inventory value
- Stock risk

### Returns Management

Understand why products are returned and identify unusual return behavior across products, stores, and categories.

### Promotion Effectiveness

Evaluate whether promotional campaigns produce meaningful commercial impact.

### Target Monitoring

Compare actual business performance against predefined store targets.

### Secure Analytics Access

Demonstrate database and application-level security patterns including authentication, session context, and row-level security.

---

# 🚀 Key Features

The platform includes:

- Synthetic retail data generation
- UAE-specific geographic modeling
- SQL Server relational database
- Modular SQL DDL scripts
- Automated bulk loading
- Data quality validation
- Analytical database views
- Performance indexes
- Advanced SQL analysis
- Revenue KPI analysis
- Growth analysis
- Store performance analysis
- Product performance analysis
- Customer analytics
- Returns analysis
- Inventory analytics
- Target analysis
- RFM segmentation
- Cohort analysis
- Pareto / ABC analysis
- Basket analysis
- Promotion analysis
- Return anomaly detection
- Inventory risk analysis
- Authentication framework
- Session context management
- Row-level security
- Interactive Streamlit dashboard
- Global dashboard filters
- Reproducible analytics scripts

---

# 🛠 Technology Stack

## Programming

**Python**

Used for:

- Synthetic data generation
- ETL workflows
- Database loading
- Data validation
- Analytical transformations
- Exploratory data analysis
- Dashboard development

## Database

**Microsoft SQL Server**

Used for:

- Relational data modeling
- Data storage
- Analytical views
- SQL analytics
- Security
- Row-level access control
- Performance optimization

## Dashboard

**Streamlit**

Used to build the interactive business intelligence application.

## Data Analysis

Python libraries are used for:

- Data manipulation
- Statistical analysis
- Visualization
- Database connectivity

See:

```text
requirements.txt
for the project's Python dependencies.

Version Control
Git + GitHub

Used for source control, documentation, and project distribution.

🏗 Project Architecture
The project follows a layered architecture.

text

                    ┌──────────────────────────┐
                    │ Synthetic Data Generator │
                    │         Python           │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Generated Data      │
                    │           CSV            │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │       SQL Server         │
                    │   Relational Database    │
                    └────────────┬─────────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
               ▼                 ▼                 ▼
        Analytical Views      Security        Validation
               │
               ▼
        ┌─────────────────┐
        │ Analytics Layer │
        │     Python      │
        └────────┬────────┘
                 │
                 ▼
        ┌─────────────────┐
        │    Streamlit    │
        │   BI Dashboard  │
        └─────────────────┘
This separation makes the project easier to maintain and allows each layer to evolve independently.

📁 Repository Structure
text

UAE-Retail-Intelligence/
│
├── app/
│   ├── pages/
│   │   ├── customers.py
│   │   ├── executive.py
│   │   ├── inventory.py
│   │   ├── products.py
│   │   ├── promotions.py
│   │   ├── returns.py
│   │   ├── sales.py
│   │   ├── stores.py
│   │   └── targets.py
│   │
│   ├── components.py
│   ├── filters.py
│   ├── session.py
│   └── theme.py
│
├── assets/
│   └── eda/
│
├── config/
│   └── generation_config.py
│
├── data/
│   └── generated/
│
├── docs/
│   ├── business_requirements.md
│   ├── data_dictionary.md
│   ├── erd.md
│   └── kpi_definitions.md
│
├── scripts/
│
├── sql/
│   ├── analysis/
│   ├── ddl/
│   ├── indexes/
│   ├── security/
│   ├── validation/
│   └── views/
│
├── src/
│   ├── analytics/
│   ├── database/
│   ├── forecasting/
│   ├── generators/
│   ├── security/
│   └── validation/
│
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── streamlit_app.py
🗃 Data Model
The platform models multiple areas of a retail organization.

Core Domain
Includes entities such as:

Emirates
Cities
Stores
Employees
Payment methods
Sales channels
Date dimension
Product Domain
Includes:

Products
Categories
Subcategories
Brands
Suppliers
Product-supplier relationships
Customer Domain
Includes:

Customers
Customer segment history
Simulation profiles
Sales Domain
Includes:

Orders
Order items
Payments
Promotions Domain
Includes:

Promotions
Promotion-product relationships
Promotion-category relationships
Promotion-store relationships
Returns Domain
Includes:

Returns
Return items
Refunds
Inventory Domain
Includes:

Store-product inventory
Inventory movements
Performance Management
Includes:

Store monthly targets
The relational structure allows analytics to be performed across multiple dimensions while maintaining clear business entities.

Detailed information can be found in:

text

docs/data_dictionary.md
docs/erd.md
🧪 Synthetic Data Generation
One of the key characteristics of this project is that the dataset can be generated programmatically.

The generators are located in:

text

src/generators/
Generation scripts include:

text

01_generate_core.py
02_generate_products.py
03_generate_customers.py
04_generate_employees.py
05_generate_promotions.py
06_generate_sales.py
07_generate_returns.py
08_generate_inventory.py
09_generate_targets.py
The generator architecture makes the project reproducible without requiring proprietary retail data.

Configuration is managed through:

text

config/generation_config.py
The generated datasets are intentionally excluded from the Git repository to avoid storing large generated files in source control.

🗄 Database Layer
The SQL Server database is built using modular DDL scripts.

text

sql/ddl/
The database includes separate structures for:

Core entities
Products
Customers
Promotions
Sales
Returns
Inventory
Targets
Security
Database initialization begins with:

text

sql/00_create_database.sql
sql/01_create_schemas.sql
Followed by the domain-specific DDL scripts.

This modular structure makes database deployment easier to understand and maintain.

✅ Data Quality Framework
Data quality is a critical component of the project.

Validation logic is implemented in:

text

src/validation/data_quality.py
and executed through:

text

scripts/10_run_data_quality.py
Additional SQL validation is available under:

text

sql/validation/
The validation layer is designed to verify data integrity before analytics are performed.

Potential checks include:

Missing values
Invalid relationships
Duplicate records
Invalid dates
Unexpected numerical values
Referential integrity
Business-rule violations
📊 SQL Analytics
The project includes a dedicated SQL analytics layer:

text

sql/analysis/
Analytical scripts include:

text

01_sales_kpis.sql
02_growth_analysis.sql
03_store_analysis.sql
04_product_analysis.sql
05_customer_analysis.sql
06_returns_analysis.sql
07_inventory_analysis.sql
08_target_analysis.sql
09_rfm_analysis.sql
10_cohort_analysis.sql
11_pareto_abc_analysis.sql
12_basket_analysis.sql
This allows important business analysis to be performed directly inside the database in addition to the Python analytics layer.

🔍 Exploratory Data Analysis
EDA is organized into several business-focused stages.

text

assets/eda/
The analysis covers:

Overview
High-level investigation of:

Dataset characteristics
Revenue distribution
Product performance
Store performance
Temporal coverage
Sales and Time
Includes:

Daily revenue
Monthly revenue
Annual performance
Moving averages
Year-over-year behavior
Day-of-week patterns
Event-related revenue behavior
Revenue outlier detection
Example:

Monthly Revenue Trend

Store and Product
Includes:

Store performance
Category performance
Brand performance
Product concentration
Pareto analysis
Revenue and margin relationships
Return-rate relationships
Geographic performance
Example:

Revenue by Emirate

Customer Analysis
Includes:

Customer revenue distribution
Average order value
Purchase frequency
Recency
Customer activity
Revenue concentration
New vs returning customers
Example:

Customer Revenue Concentration

👥 Customer Analytics
Customer intelligence is an important part of the platform.

Analysis includes:

Total customer value
Average order value
Order frequency
Customer recency
Preferred sales channels
Preferred emirates
Revenue concentration
Return behavior
Customer activity over time
This provides a more complete understanding of customer behavior than simply measuring total sales.

🎯 RFM Segmentation
The project implements RFM analysis.

RFM stands for:

Recency

How recently did the customer purchase?

Frequency

How frequently does the customer purchase?

Monetary

How much value has the customer generated?

Customers can then be grouped based on their RFM characteristics to identify different behavioral profiles.

Analysis outputs include:

RFM customer scores
Segment sizes
Revenue by segment
Recency vs frequency
RF score matrices
Example:

RFM Segment Revenue

RFM segmentation can support:

Retention campaigns
Loyalty strategies
Customer prioritization
Reactivation campaigns
Marketing personalization
📅 Cohort Analysis
Cohort analysis is used to study customer retention over time.

Customers can be grouped according to their acquisition period and tracked across later periods.

Outputs include:

Cohort retention matrix
Retention heatmap
Retention curves
Cohort lifetime revenue
Example:

Cohort Retention Heatmap

This analysis helps answer:

Are customers continuing to purchase after their initial acquisition period?

🏬 Store Analytics
Store-level analysis evaluates retail performance across locations.

Metrics include:

Revenue
Margin
Return rates
Revenue per store
Geographic performance
Performance quadrants
Store comparison helps identify:

Strong stores
Underperforming stores
High-return locations
Differences between emirates
Potential operational issues
Example:

Store Revenue Margin Quadrant

📦 Product Analytics
Product analytics evaluates performance across:

Products
Brands
Categories
Subcategories
The analysis includes:

Product revenue
Product profitability
Return rates
Discount dependency
Revenue concentration
ABC classification
Pareto analysis
Example:

Product Pareto Curve

Pareto analysis helps investigate whether a relatively small portion of products contributes a large share of business revenue.

↩️ Returns Analytics
Returns directly affect profitability and customer experience.

The platform analyzes:

Return rates
Return reasons
Store return rates
Category return rates
Product return behavior
Return lag
Potential return anomalies
Example:

Return Reasons

The project also includes analytical logic for detecting unusual return patterns.

Example:

Product Return Anomalies

📦 Inventory Analytics
Inventory analytics focuses on understanding both stock availability and capital allocation.

Analysis includes:

Inventory value
Product velocity
Stock status
Reorder risk
Slow-moving inventory
Category inventory value
Inventory velocity/value positioning
Example:

Inventory Status

And:

Inventory Velocity Value Matrix

This analysis can help identify situations where capital is tied up in low-velocity products.

🏷 Promotion Analytics
The promotions module evaluates campaign performance and discount behavior.

Analysis includes:

Campaign revenue
Promotion types
Promotional vs non-promotional sales
Discount bands
Discount vs margin
Seasonal campaigns
Campaign-level business flags
Promotion trends
Example:

Discount vs Margin

Another important comparison is:

Promoted vs Non Promoted

This helps investigate whether promotions are increasing commercial performance while maintaining acceptable margins.

🎯 Target Analysis
Store targets provide a benchmark for evaluating operational performance.

The project includes monthly store targets and analytical logic for comparing:

text

Actual Performance
        vs
Target Performance
The Streamlit dashboard includes a dedicated target analysis page.

This allows management to monitor:

Target attainment
Store performance
Performance gaps
Period-based progress
🔐 Security Architecture
The project includes a dedicated security layer.

Python security modules are located in:

text

src/security/
Including:

text

authentication.py
passwords.py
session_context.py
SQL security logic is located in:

text

sql/security/
The platform explores concepts such as:

User authentication
Password handling
Database session context
Row-Level Security (RLS)
Access control
Security bypass testing
BI security validation
Dedicated security tests include:

text

24_test_authentication.py
25_test_session_context.py
26_test_rls.py
27_test_security_bypass.py
31_test_final_bi_security.py
This adds an important enterprise-oriented dimension to the project because analytics systems often need to ensure that different users can access only the data they are authorized to view.

📈 Streamlit Dashboard
The interactive business intelligence application is built with Streamlit.

Main application:

text

streamlit_app.py
Dashboard modules are organized under:

text

app/
Shared functionality includes:

text

components.py
filters.py
session.py
theme.py
The modular design separates dashboard presentation from the analytics and database layers.

🖥 Dashboard Pages
The application contains dedicated pages for major business domains.

Executive
Provides high-level management KPIs and business performance indicators.

text

app/pages/executive.py
Sales
Focuses on sales trends and revenue performance.

text

app/pages/sales.py
Stores
Analyzes performance across retail locations.

text

app/pages/stores.py
Products
Provides product, category, and brand-level analysis.

text

app/pages/products.py
Customers
Provides customer behavior and segmentation analytics.

text

app/pages/customers.py
Inventory
Monitors inventory status, value, movement, and risk.

text

app/pages/inventory.py
Returns
Analyzes return behavior and operational return KPIs.

text

app/pages/returns.py
Promotions
Evaluates campaign and discount performance.

text

app/pages/promotions.py
Targets
Compares actual performance against business targets.

text

app/pages/targets.py
⚙️ Installation
1. Clone the Repository
Bash

git clone https://github.com/osamawael12/UAE-Retail-Intelligence.git
Move into the project directory:

Bash

cd UAE-Retail-Intelligence
2. Create a Virtual Environment
Windows:

Bash

python -m venv .venv
Activate it:

Bash

.venv\Scripts\activate
Linux/macOS:

Bash

python3 -m venv .venv
source .venv/bin/activate
3. Install Dependencies
Bash

pip install -r requirements.txt
🔧 Environment Configuration
The repository includes:

text

.env.example
Create your local environment file:

text

.env
using .env.example as the template.

Do not commit the real .env file.

The .gitignore configuration excludes environment secrets from source control.

Database credentials and other sensitive configuration should always be supplied through environment variables or an appropriate secrets-management system.

🗄 SQL Server Setup
The application uses Microsoft SQL Server.

Start by creating the database:

text

sql/00_create_database.sql
Then create the required schemas:

text

sql/01_create_schemas.sql
Run the domain DDL scripts from:

text

sql/ddl/
The exact execution sequence should follow the numerical prefixes of the SQL files where dependencies apply.

▶️ Running the Project
The project provides scripts for each stage of the pipeline.

Generate core data:

Bash

python scripts/01_generate_core.py
Generate products:

Bash

python scripts/02_generate_products.py
Generate customers:

Bash

python scripts/03_generate_customers.py
Continue through the numbered generation scripts as required.

Run data-quality validation:

Bash

python scripts/10_run_data_quality.py
Load data into SQL Server:

Bash

python scripts/11_bulk_load_sql.py
Validate SQL data:

Bash

python scripts/12_validate_sql_data.py
Validate analytical views:

Bash

python scripts/13_validate_analytics_views.py
📊 Running EDA
EDA scripts are organized by analytical domain.

Overview:

Bash

python scripts/16_eda_overview.py
Sales and time:

Bash

python scripts/17_eda_sales_time.py
Stores and products:

Bash

python scripts/18_eda_store_product.py
Customers:

Bash

python scripts/19_eda_customer.py
RFM and cohort:

Bash

python scripts/20_eda_rfm_cohort.py
Returns and inventory:

Bash

python scripts/21_eda_returns_inventory.py
Promotions:

Bash

python scripts/22_eda_promotions.py
Generated analytical artifacts are stored under:

text

assets/eda/
🚀 Running the Dashboard
After configuring the database and environment variables:

Bash

streamlit run streamlit_app.py
Streamlit will start a local development server.

The application is normally available at:

text

http://localhost:8501
🔄 Reproducing the Data
Generated CSV datasets are intentionally not tracked by Git.

This keeps the repository lightweight and avoids committing generated artifacts.

The datasets can be reproduced using the scripts in:

text

scripts/
and the generator modules in:

text

src/generators/
This approach makes the data-generation process itself part of the project instead of treating the final generated dataset as a static dependency.

📚 Documentation
Additional documentation is available under:

text

docs/
Business Requirements
text

docs/business_requirements.md
Describes the business context, analytical objectives, and functional requirements.

Data Dictionary
text

docs/data_dictionary.md
Documents important entities, attributes, and data definitions.

Entity Relationship Diagram
text

docs/erd.md
Describes the relational database structure and relationships between entities.

KPI Definitions
text

docs/kpi_definitions.md
Provides standardized definitions for business metrics used throughout the platform.

Having centralized KPI definitions is important to ensure that different dashboard pages and analytical processes interpret business metrics consistently.

🔎 Analytical Areas Covered
The project demonstrates analytical techniques across several areas:

Area	Techniques
Sales	Revenue trends, YoY analysis, moving averages
Customers	AOV, frequency, recency, revenue concentration
Segmentation	RFM scoring
Retention	Cohort analysis
Products	Revenue, profit, return rate
Portfolio	Pareto and ABC analysis
Stores	Performance benchmarking
Geography	Emirate-level performance
Returns	Return reasons and anomaly detection
Inventory	Velocity, value, reorder risk
Promotions	Campaign and discount analysis
Targets	Actual vs target
Security	Authentication and Row-Level Security
💡 Business Questions Addressed
This project is designed to support questions such as:

Executive Management
What is the overall business performance?
How is revenue evolving?
Which areas require management attention?
Sales Management
Which periods generate the highest sales?
Is revenue growing year over year?
Are there recurring weekly or seasonal patterns?
Store Management
Which stores perform best?
Which stores have high return rates?
Which locations are below target?
Product Management
Which products generate the most revenue?
Which categories generate the strongest margins?
Which products depend heavily on discounting?
Which products have unusual return rates?
Customer Management
Who are the highest-value customers?
How concentrated is customer revenue?
Which customers are highly engaged?
How does retention evolve after acquisition?
Inventory Management
Which products may require replenishment?
Which items are slow-moving?
Where is inventory value concentrated?
Which products combine low velocity with high inventory value?
Marketing
Which promotions perform best?
How does promotional revenue compare with non-promotional revenue?
How do discounts affect margins?
Which campaign types generate the strongest performance?
🧩 Design Principles
Several principles guided the design of this project.

Reproducibility
Data generation and analysis are script-driven rather than dependent on manually prepared datasets.

Modularity
Database, analytics, dashboard, validation, and security logic are separated into dedicated modules.

Business Orientation
Analytics are organized around business questions rather than only technical outputs.

Data Quality
Validation is treated as a separate component of the analytics pipeline.

Security
Authentication and data-access restrictions are considered part of the analytical architecture.

Documentation
Business requirements, KPI definitions, data structures, and architecture are documented alongside the source code.

🗺 Development Workflow
A simplified workflow is:

text

Business Requirements
        ↓
Data Model Design
        ↓
Synthetic Data Generation
        ↓
Data Quality Validation
        ↓
SQL Server Loading
        ↓
Database Validation
        ↓
Analytical Views
        ↓
SQL Analysis
        ↓
Exploratory Data Analysis
        ↓
Analytics Layer
        ↓
Security Layer
        ↓
Streamlit Dashboard
        ↓
Business Insights
This workflow mirrors the structure of a real-world analytics project more closely than a dashboard-only implementation.

🔮 Future Improvements
Potential future enhancements include:

Cloud Deployment
Deploy the Streamlit application to a publicly accessible cloud environment.

Cloud Database
Migrate or replicate the analytical database to a cloud-hosted database service.

Forecasting
The repository already contains a dedicated:

text

src/forecasting/
module that can be expanded to include:

Revenue forecasting
Product demand forecasting
Inventory demand estimation
Store-level forecasts
Advanced Customer Analytics
Potential additions include:

Customer lifetime value
Churn prediction
Next-purchase prediction
Customer propensity models
Advanced Inventory Optimization
Future models could provide:

Safety-stock recommendations
Dynamic reorder points
Demand-based inventory optimization
Promotion Optimization
Future analysis could estimate:

Incremental campaign lift
Promotion profitability
Cannibalization
Discount elasticity
Automated Testing
Additional unit and integration tests could be added to create a more complete automated testing framework.

CI/CD
GitHub Actions could be introduced for:

Automated testing
Code-quality checks
Security checks
Deployment workflows
Containerization
Docker support could make the project easier to deploy consistently across environments.

🔒 Data & Security Notice
This repository is designed as an analytics portfolio and development project.

Generated datasets are excluded from version control.

Sensitive configuration values must not be committed to Git.

The following file is intentionally excluded:

text

.env
A template is provided through:

text

.env.example
Users should provide their own local database configuration.

📌 Project Status
The project currently includes:

✅ Data generation architecture
✅ Relational SQL Server model
✅ Data quality framework
✅ Database loading utilities
✅ Analytical SQL queries
✅ Analytical views
✅ Exploratory data analysis
✅ Customer analytics
✅ RFM segmentation
✅ Cohort analysis
✅ Store analytics
✅ Product analytics
✅ Returns analytics
✅ Inventory analytics
✅ Promotion analytics
✅ Target tracking
✅ Authentication components
✅ Row-Level Security implementation/testing
✅ Interactive Streamlit dashboard
✅ Project documentation

Additional forecasting and cloud-deployment capabilities can be added in future iterations.

👨‍💻 Author
Osama Wael
GitHub:

github.com/osamawael12

Repository:

UAE Retail Intelligence

⭐ Support
If you find this project useful or interesting, consider giving the repository a ⭐ on GitHub.

Feedback, suggestions, and contributions are welcome.

