/*
============================================================
 UAE Retail Intelligence Platform
 Schema Initialization
============================================================
*/

USE UAERetailAnalytics;
GO


-- Core
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'core'
)
BEGIN
    EXEC(N'CREATE SCHEMA core');
END;
GO


-- Product
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'product'
)
BEGIN
    EXEC(N'CREATE SCHEMA product');
END;
GO


-- Customer
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'customer'
)
BEGIN
    EXEC(N'CREATE SCHEMA customer');
END;
GO


-- Sales
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'sales'
)
BEGIN
    EXEC(N'CREATE SCHEMA sales');
END;
GO


-- Inventory
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'inventory'
)
BEGIN
    EXEC(N'CREATE SCHEMA inventory');
END;
GO


-- Security
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'security'
)
BEGIN
    EXEC(N'CREATE SCHEMA security');
END;
GO


-- Analytics
IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = N'analytics'
)
BEGIN
    EXEC(N'CREATE SCHEMA analytics');
END;
GO

USE UAERetailAnalytics;
GO

SELECT
    name AS SchemaName
FROM sys.schemas
WHERE name IN (
    'core',
    'product',
    'customer',
    'sales',
    'inventory',
    'security',
    'analytics'
)
ORDER BY name;


