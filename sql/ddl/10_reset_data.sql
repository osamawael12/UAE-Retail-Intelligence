/*
============================================================
 UAE Retail Intelligence Platform
 File: 10_reset_data.sql
 Purpose:
   Delete generated/test data while preserving database
   schemas, tables, keys, constraints and structure.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   SECURITY DATA
   ========================================================= */

DELETE FROM security.AuditLog;
DELETE FROM security.UserDataScope;
DELETE FROM security.RolePermission;
DELETE FROM security.UserRole;
DELETE FROM security.Permission;
DELETE FROM security.Role;
DELETE FROM security.AppUser;


/* =========================================================
   INVENTORY
   ========================================================= */

DELETE FROM inventory.InventoryMovement;
DELETE FROM inventory.StoreProductInventory;


/* =========================================================
   RETURNS / REFUNDS
   ========================================================= */

DELETE FROM sales.Refund;
DELETE FROM sales.ReturnItem;
DELETE FROM sales.[Return];


/* =========================================================
   PAYMENTS / SALES
   ========================================================= */

DELETE FROM sales.OrderPayment;
DELETE FROM sales.SalesOrderItem;
DELETE FROM sales.SalesOrder;


/* =========================================================
   TARGETS
   ========================================================= */

DELETE FROM sales.StoreMonthlyTarget;


/* =========================================================
   PROMOTIONS
   ========================================================= */

DELETE FROM sales.PromotionStore;
DELETE FROM sales.PromotionCategory;
DELETE FROM sales.PromotionProduct;
DELETE FROM sales.Promotion;


/* =========================================================
   CUSTOMER DATA
   ========================================================= */

DELETE FROM customer.CustomerSegmentHistory;
DELETE FROM customer.Customer;


/* =========================================================
   PRODUCT DATA
   ========================================================= */

DELETE FROM product.ProductSupplier;
DELETE FROM product.Product;
DELETE FROM product.Supplier;
DELETE FROM product.Brand;
DELETE FROM product.Subcategory;
DELETE FROM product.Category;


/* =========================================================
   CORE DATA
   ========================================================= */

DELETE FROM core.Employee;
DELETE FROM core.Store;
DELETE FROM core.City;
DELETE FROM core.Emirate;

DELETE FROM core.SalesChannel;
DELETE FROM core.PaymentMethod;
DELETE FROM core.DateDimension;


/* =========================================================
   RESET IDENTITY VALUES
   ========================================================= */

DBCC CHECKIDENT ('security.AuditLog', RESEED, 0);
DBCC CHECKIDENT ('security.UserDataScope', RESEED, 0);
DBCC CHECKIDENT ('security.Permission', RESEED, 0);
DBCC CHECKIDENT ('security.Role', RESEED, 0);
DBCC CHECKIDENT ('security.AppUser', RESEED, 0);

DBCC CHECKIDENT ('inventory.InventoryMovement', RESEED, 0);

DBCC CHECKIDENT ('sales.Refund', RESEED, 0);
DBCC CHECKIDENT ('sales.ReturnItem', RESEED, 0);
DBCC CHECKIDENT ('sales.Return', RESEED, 0);

DBCC CHECKIDENT ('sales.OrderPayment', RESEED, 0);
DBCC CHECKIDENT ('sales.SalesOrderItem', RESEED, 0);
DBCC CHECKIDENT ('sales.SalesOrder', RESEED, 0);

DBCC CHECKIDENT ('sales.StoreMonthlyTarget', RESEED, 0);

DBCC CHECKIDENT ('sales.Promotion', RESEED, 0);

DBCC CHECKIDENT ('customer.CustomerSegmentHistory', RESEED, 0);
DBCC CHECKIDENT ('customer.Customer', RESEED, 0);

DBCC CHECKIDENT ('product.Product', RESEED, 0);
DBCC CHECKIDENT ('product.Supplier', RESEED, 0);
DBCC CHECKIDENT ('product.Brand', RESEED, 0);
DBCC CHECKIDENT ('product.Subcategory', RESEED, 0);
DBCC CHECKIDENT ('product.Category', RESEED, 0);

DBCC CHECKIDENT ('core.Employee', RESEED, 0);
DBCC CHECKIDENT ('core.Store', RESEED, 0);
DBCC CHECKIDENT ('core.City', RESEED, 0);
DBCC CHECKIDENT ('core.Emirate', RESEED, 0);

DBCC CHECKIDENT ('core.SalesChannel', RESEED, 0);
DBCC CHECKIDENT ('core.PaymentMethod', RESEED, 0);

GO


/* =========================================================
   VALIDATION
   ========================================================= */

SELECT
    s.name AS SchemaName,
    t.name AS TableName,
    SUM(p.rows) 
FROM sys.tables t
INNER JOIN sys.schemas s
    ON t.schema_id = s.schema_id
INNER JOIN sys.partitions p
    ON t.object_id = p.object_id
WHERE
    p.index_id IN (0, 1)
    AND s.name IN
    (
        'core',
        'product',
        'customer',
        'sales',
        'inventory',
        'security'
    )
GROUP BY
    s.name,
    t.name
ORDER BY
    s.name,
    t.name;
GO