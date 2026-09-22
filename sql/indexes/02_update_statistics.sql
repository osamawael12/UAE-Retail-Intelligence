/*
============================================================
 UAE Retail Intelligence Platform
 Update SQL Server statistics after bulk loading and indexing.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO

UPDATE STATISTICS
    sales.SalesOrder
WITH FULLSCAN;
GO

UPDATE STATISTICS
    sales.SalesOrderItem
WITH FULLSCAN;
GO

UPDATE STATISTICS
    sales.[Return]
WITH FULLSCAN;
GO

UPDATE STATISTICS
    sales.ReturnItem
WITH FULLSCAN;
GO

UPDATE STATISTICS
    inventory.InventoryMovement
WITH FULLSCAN;
GO

UPDATE STATISTICS
    inventory.StoreProductInventory
WITH FULLSCAN;
GO

UPDATE STATISTICS
    customer.Customer
WITH FULLSCAN;
GO

UPDATE STATISTICS
    sales.StoreMonthlyTarget
WITH FULLSCAN;
GO