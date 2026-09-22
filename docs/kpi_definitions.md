# UAE Retail Intelligence Platform
## KPI Definitions

## 1. Purpose

This document defines the official business metrics used throughout the UAE Retail Intelligence Platform.

The same KPI definitions must be used consistently across:

- SQL Analytics
- Python EDA
- Analytics Views
- Streamlit Dashboards
- Forecasting inputs
- Business Insights
- Automated Tests

Financial amounts are reported in AED unless otherwise stated.

VAT is excluded from Revenue and Gross Profit calculations.

Valid completed sales are included unless a KPI explicitly states otherwise.


# 2. Sales Financial Model

For each Order Item:

Gross Sales
= Unit Price × Quantity

Discount Amount
= Applied discount on the sales line

Net Sales Before VAT
= Gross Sales - Discount Amount

VAT Amount
= Net Sales Before VAT × Applied VAT Rate

Customer Total
= Net Sales Before VAT + VAT Amount

COGS
= Unit Cost × Quantity

Gross Profit
= Net Sales Before VAT - COGS

Gross Margin %
= Gross Profit / Net Sales Before VAT × 100


# 3. Gross Sales

Definition:

Total sales value before discounts, VAT, and returns.

Formula:

Gross Sales
= SUM(Unit Price × Quantity)

Unit:

AED

VAT Included:

No


# 4. Discount Amount

Definition:

Total discount granted to customers.

Formula:

Discount Amount
= SUM(Line Discount Amount)

Unit:

AED


# 5. Discount Rate

Definition:

Percentage of Gross Sales removed through discounts.

Formula:

Discount Rate %
= Discount Amount / Gross Sales × 100

If Gross Sales = 0:

Discount Rate = 0


# 6. Net Sales

Definition:

Sales value after discounts and before VAT.

Formula:

Net Sales
= Gross Sales - Discount Amount

Throughout this project, Net Sales is the base sales revenue measure before considering returns.


# 7. Revenue

Definition:

Net earned sales after discounts and valid returned merchandise, excluding VAT.

Formula:

Revenue
= Net Sales - Returned Net Sales

VAT must never be counted as Revenue.

For analyses explicitly labeled "Gross/Pre-Return Revenue", Net Sales may be shown separately.


# 8. VAT Amount

Definition:

VAT charged on taxable sales.

Formula:

VAT Amount
= Taxable Amount × Applied VAT Rate

The default simulated VAT rate is:

5%

The actual rate applied must be stored with the transaction.

VAT is not:

- Revenue
- Gross Profit
- Discount


# 9. Customer Total

Definition:

Total amount charged to the customer for a sales transaction before subsequent refunds.

Formula:

Customer Total
= Net Sales + VAT Amount


# 10. Cost of Goods Sold — COGS

Definition:

Cost attributable to net merchandise sold.

For a sales line before returns:

Sales COGS
= Unit Cost × Quantity Sold

For net reporting:

COGS
= Sales COGS - Cost Reversed for Valid Returns

Unit:

AED


# 11. Gross Profit

Definition:

Profit after product cost and valid merchandise returns, excluding operating expenses and VAT.

Formula:

Gross Profit
= Revenue - COGS


# 12. Gross Margin

Definition:

Percentage of Revenue remaining after COGS.

Formula:

Gross Margin %
= Gross Profit / Revenue × 100

If Revenue = 0:

Gross Margin % = 0


# 13. Orders

Definition:

Number of distinct valid completed orders.

Formula:

Orders
= COUNT(DISTINCT OrderId)

Cancelled or invalid orders are excluded.


# 14. Units Sold

Two unit measures may be used.

Gross Units Sold:

SUM(Sales Quantity)

Net Units Sold:

Gross Units Sold - Returned Quantity

The default executive KPI will use Net Units Sold unless explicitly labeled Gross Units Sold.


# 15. Average Order Value — AOV

Definition:

Average Revenue generated per valid completed order.

Formula:

AOV
= Revenue / Number of Orders

If Orders = 0:

AOV = 0

VAT is excluded.


# 16. Customers

Definition:

Number of unique customers who completed at least one valid purchase during the selected period.

Formula:

Customers
= COUNT(DISTINCT CustomerId)

Guest/anonymous transactions, if introduced later, must be reported separately and must not be treated as identified customers.


# 17. Revenue per Customer

Definition:

Average Revenue generated per purchasing customer.

Formula:

Revenue per Customer
= Revenue / Active Purchasing Customers


# 18. New Customer

Definition:

A customer whose first-ever valid purchase occurs during the selected analysis period.

The classification must use the customer's complete available purchase history, not only filtered rows visible after the selected start date.


# 19. Returning Customer

Definition:

A customer who makes a purchase during the selected period and had at least one valid purchase before the purchase being evaluated.

At period-level reporting, a customer is considered Returning if they purchased during the period and their first-ever purchase occurred before that period.


# 20. Repeat Customer

Definition:

A customer who has completed at least two valid orders within the defined analysis scope.

For lifetime customer segmentation:

Repeat Customer
= Customer with Lifetime Orders >= 2


# 21. Repeat Customer Rate

Definition:

Percentage of purchasing customers who qualify as repeat customers.

Formula:

Repeat Customer Rate %
= Repeat Customers / Purchasing Customers × 100

The dashboard must clearly indicate whether the calculation uses lifetime or selected-period behavior.


# 22. Purchase Frequency

Definition:

Average number of valid orders per purchasing customer.

Formula:

Purchase Frequency
= Orders / Purchasing Customers


# 23. Return Quantity

Definition:

Number of merchandise units validly returned.

Formula:

Returned Units
= SUM(Return Quantity)


# 24. Return Rate

The platform will retain more than one return metric to avoid ambiguity.

Unit Return Rate:

Returned Units / Gross Units Sold × 100

Sales Value Return Rate:

Returned Net Sales / Net Sales Before Returns × 100

The default Returns Dashboard KPI will use Unit Return Rate and will label the metric explicitly.


# 25. Refund Amount

Definition:

Amount refunded to customers for valid returns.

Refund Amount may include:

- Returned merchandise value
- Reversed VAT where applicable

For revenue analysis, only the returned net sales amount excluding VAT reduces Revenue.

VAT refunds must be tracked separately from Revenue.


# 26. Revenue Growth

Definition:

Percentage change in Revenue between two comparable periods.

Formula:

Growth %
= (Current Revenue - Previous Revenue)
  / Previous Revenue × 100

If Previous Revenue = 0:

Growth % should be reported as NULL / N/A rather than an artificial percentage.


# 27. Month-over-Month Growth — MoM

Definition:

Revenue growth compared with the immediately previous calendar month.

Formula:

MoM %
= (Current Month Revenue - Previous Month Revenue)
  / Previous Month Revenue × 100


# 28. Year-over-Year Growth — YoY

Definition:

Revenue growth compared with the equivalent period one year earlier.

Formula:

YoY %
= (Current Period Revenue - Same Period Previous Year Revenue)
  / Same Period Previous Year Revenue × 100


# 29. Revenue Contribution

Definition:

Percentage of total Revenue contributed by an entity such as Store, Emirate, Category, Brand, or Product.

Formula:

Revenue Contribution %
= Entity Revenue / Total Revenue × 100


# 30. Target Achievement

Revenue Achievement:

Revenue Achievement %
= Actual Revenue / Revenue Target × 100

Profit Achievement:

Profit Achievement %
= Actual Gross Profit / Gross Profit Target × 100

Orders Achievement:

Orders Achievement %
= Actual Orders / Orders Target × 100

If Target = 0:

Achievement % = NULL / N/A


# 31. Target Variance

Revenue Variance:

Revenue Variance
= Actual Revenue - Revenue Target

Profit Variance:

Profit Variance
= Actual Gross Profit - Gross Profit Target

Orders Variance:

Orders Variance
= Actual Orders - Orders Target

Positive variance indicates performance above target.

Negative variance indicates performance below target.


# 32. Inventory Stock on Hand

Definition:

Current physical quantity available for a Product × Store combination according to inventory movements.

Conceptual Formula:

Stock on Hand =
Purchases
+ Transfer In
+ Restockable Returns
+ Positive Adjustments
- Sales
- Transfer Out
- Damaged Units
- Negative Adjustments


# 33. Inventory Value

Definition:

Estimated cost value of current stock.

Formula:

Inventory Value
= Stock on Hand × Inventory Unit Cost

The costing method used for inventory valuation must be documented when the inventory engine is implemented.


# 34. Stockout

Definition:

A Product × Store combination with no available inventory.

Basic Rule:

Stock on Hand <= 0

A stockout event/rate over time should be measured from inventory state snapshots or movement-derived availability, not merely from the current final balance.


# 35. Low Stock

Definition:

Product inventory below its defined reorder threshold.

Rule:

Stock on Hand <= Reorder Point

and

Stock on Hand > 0


# 36. Fast-Moving Product

Definition:

A product with relatively high sales velocity compared with an appropriate peer group.

The final classification threshold will be defined during inventory analysis.

Possible measures include:

Units Sold / Active Selling Days

or

Units Sold / Time Period


# 37. Slow-Moving Product

Definition:

A product with low sales velocity over a defined period.

The exact threshold will be configured during inventory analysis and must consider product lifecycle and availability.


# 38. Stockout Rate

Definition:

Percentage of eligible product-store availability observations that are in stockout status.

Conceptual Formula:

Stockout Rate %
= Stockout Observations / Eligible Inventory Observations × 100

The final observation grain (for example Product × Store × Day) will be fixed during inventory design.


# 39. RFM Metrics

RFM stands for:

Recency
Frequency
Monetary


## Recency

Number of days between the analysis reference date and the customer's most recent valid purchase.

Lower Recency indicates more recent activity.


## Frequency

Number of valid completed orders made by the customer during the defined RFM observation window.


## Monetary

Total Revenue generated by the customer during the defined RFM observation window.


# 40. RFM Segments

Customers may be classified into segments including:

- Champions
- Loyal
- Potential Loyalists
- New Customers
- At Risk
- Lost

Exact scoring thresholds will be defined during the RFM implementation phase and documented before dashboard use.


# 41. Customer Cohort

Definition:

Customers grouped according to the calendar month of their first valid purchase.

Example:

Customer First Purchase:
2024-03-16

Cohort:
2024-03


# 42. Cohort Retention Rate

Definition:

Percentage of customers from an acquisition cohort who make a valid purchase in a later cohort period.

Formula:

Retention %
= Active Cohort Customers in Period N
  / Original Cohort Customers
  × 100


# 43. Promotion Revenue Lift

Definition:

Estimated Revenue change associated with promotional activity.

A simple exploratory comparison may use:

Revenue Lift %
= (Promotion Period Revenue - Baseline Revenue)
  / Baseline Revenue × 100

This metric represents association unless the analysis design supports causal inference.

Seasonality and other demand factors should be considered when interpreting promotion performance.


# 44. Promotion Unit Lift

Definition:

Change in units sold during promotional activity compared with an appropriate baseline.

Formula:

Unit Lift %
= (Promotion Units - Baseline Units)
  / Baseline Units × 100


# 45. Discount Dependency

Definition:

Degree to which a product's sales depend on discounted transactions.

Possible measure:

Discount Dependency %
= Revenue generated from discounted sales
  / Total Product Revenue
  × 100

Additional measures may compare units and order frequency between promoted and non-promoted periods.


# 46. Product Return Rate

Definition:

Percentage of gross units sold for a product that were later validly returned.

Formula:

Product Return Rate %
= Product Returned Units
  / Product Gross Units Sold
  × 100


# 47. Pareto Revenue Analysis

Purpose:

Identify the proportion of products responsible for the majority of Revenue.

Method:

1. Calculate Revenue per Product.
2. Sort products from highest to lowest Revenue.
3. Calculate cumulative Revenue.
4. Calculate cumulative Revenue percentage.
5. Identify products contributing to approximately 80% of Revenue.

The observed product share must be reported rather than assuming that exactly 20% of products generate 80% of Revenue.


# 48. Forecast Accuracy

Forecasting models will be evaluated using time-based validation.

Potential metrics include:

- MAE
- RMSE
- WAPE
- MAPE when mathematically appropriate


## MAE

Mean Absolute Error.


## RMSE

Root Mean Squared Error.


## WAPE

Weighted Absolute Percentage Error.

Formula:

WAPE
= SUM(ABS(Actual - Forecast))
  / SUM(ABS(Actual))
  × 100


## MAPE

Mean Absolute Percentage Error.

MAPE should not be used when actual observations contain zero or near-zero values that make the metric misleading.


# 49. KPI Filtering Rules

Unless explicitly stated otherwise, KPIs must respect:

- Selected Date Range
- Authorized User Scope
- Emirate Filter
- City Filter
- Store Filter
- Channel Filter
- Category Filter
- Subcategory Filter
- Brand Filter
- Customer Segment Filter

Security restrictions are applied before business analytics are returned to the application.


# 50. KPI Consistency Rule

A KPI must not have independent undocumented formulas across SQL, Python, and Streamlit.

The authoritative definition originates from this document.

Implementation should follow:

KPI Definition
→ SQL / Python Calculation
→ Automated Test
→ Analytics View
→ Dashboard

Any future change to a KPI definition must be documented before implementation is changed.