/*
============================================================
 UAE Retail Intelligence Platform
 File: 01_analytics_indexes.sql

 Purpose:
 Performance indexes for tested analytics workloads.

 Notes:
 - PK / UNIQUE indexes are not duplicated.
 - Indexes target actual filtering, joining and aggregation.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   1. SALES ORDER
   Date-driven analytics:
   Year / Month / Daily trends / Forecasting
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_SalesOrder_OrderDateTime'
        AND object_id
            = OBJECT_ID(
                'sales.SalesOrder'
            )
)
BEGIN

    CREATE INDEX
        IX_SalesOrder_OrderDateTime

    ON sales.SalesOrder
    (
        OrderDateTime
    )

    INCLUDE
    (
        OrderId,
        StoreId,
        CustomerId,
        SalesChannelId,
        DateKey,
        OrderStatus
    );

END;
GO


/* =========================================================
   2. SALES ORDER
   Store + Date
   Supports store dashboards and RLS-style filtering.
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_SalesOrder_Store_Date'
        AND object_id
            = OBJECT_ID(
                'sales.SalesOrder'
            )
)
BEGIN

    CREATE INDEX
        IX_SalesOrder_Store_Date

    ON sales.SalesOrder
    (
        StoreId,
        OrderDateTime
    )

    INCLUDE
    (
        OrderId,
        CustomerId,
        SalesChannelId,
        OrderStatus,
        NetAmount
    );

END;
GO


/* =========================================================
   3. SALES ORDER
   Customer + Date
   Supports Customer360 / RFM / Cohort.
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_SalesOrder_Customer_Date'
        AND object_id
            = OBJECT_ID(
                'sales.SalesOrder'
            )
)
BEGIN

    CREATE INDEX
        IX_SalesOrder_Customer_Date

    ON sales.SalesOrder
    (
        CustomerId,
        OrderDateTime
    )

    INCLUDE
    (
        OrderId,
        StoreId,
        SalesChannelId,
        OrderStatus
    );

END;
GO


/* =========================================================
   4. SALES ORDER ITEM
   Order join
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_SalesOrderItem_Order'
        AND object_id
            = OBJECT_ID(
                'sales.SalesOrderItem'
            )
)
BEGIN

    CREATE INDEX
        IX_SalesOrderItem_Order

    ON sales.SalesOrderItem
    (
        OrderId
    )

    INCLUDE
    (
        ProductId,
        PromotionId,
        Quantity,
        NetAmount,
        VATAmount,
        LineCOGS,
        DiscountAmount
    );

END;
GO


/* =========================================================
   5. SALES ORDER ITEM
   Product analytics
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_SalesOrderItem_Product'
        AND object_id
            = OBJECT_ID(
                'sales.SalesOrderItem'
            )
)
BEGIN

    CREATE INDEX
        IX_SalesOrderItem_Product

    ON sales.SalesOrderItem
    (
        ProductId
    )

    INCLUDE
    (
        OrderId,
        Quantity,
        GrossAmount,
        DiscountAmount,
        NetAmount,
        VATAmount,
        UnitCost,
        LineCOGS
    );

END;
GO


/* =========================================================
   6. RETURN
   Original Order relationship
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_Return_Order'
        AND object_id
            = OBJECT_ID(
                'sales.Return'
            )
)
BEGIN

    CREATE INDEX
        IX_Return_Order

    ON sales.[Return]
    (
        OrderId
    )

    INCLUDE
    (
        ReturnId,
        StoreId,
        ReturnDateTime,
        ReturnStatus,
        TotalReturnNetAmount
    );

END;
GO


/* =========================================================
   7. RETURN ITEM
   Original OrderItem lookup
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_ReturnItem_OrderItem'
        AND object_id
            = OBJECT_ID(
                'sales.ReturnItem'
            )
)
BEGIN

    CREATE INDEX
        IX_ReturnItem_OrderItem

    ON sales.ReturnItem
    (
        OrderItemId
    )

    INCLUDE
    (
        ReturnId,
        ReturnQuantity,
        ReturnReason,
        ReturnedNetAmount,
        VATReversed,
        RefundAmount,
        IsRestockable
    );

END;
GO


/* =========================================================
   8. RETURN ITEM
   Return Header join
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name = 'IX_ReturnItem_Return'
        AND object_id
            = OBJECT_ID(
                'sales.ReturnItem'
            )
)
BEGIN

    CREATE INDEX
        IX_ReturnItem_Return

    ON sales.ReturnItem
    (
        ReturnId
    )

    INCLUDE
    (
        OrderItemId,
        ReturnQuantity,
        ReturnedNetAmount,
        VATReversed,
        RefundAmount
    );

END;
GO


/* =========================================================
   9. INVENTORY MOVEMENT
   Store/Product chronological ledger
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name =
            'IX_InventoryMovement_Store_Product_Date'
        AND object_id
            = OBJECT_ID(
                'inventory.InventoryMovement'
            )
)
BEGIN

    CREATE INDEX
        IX_InventoryMovement_Store_Product_Date

    ON inventory.InventoryMovement
    (
        StoreId,
        ProductId,
        MovementDateTime
    )

    INCLUDE
    (
        MovementType,
        QuantityChange,
        UnitCost,
        OrderItemId,
        ReturnItemId
    );

END;
GO


/* =========================================================
   10. INVENTORY MOVEMENT
   Sales movement lookup
   Filtered index.
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name =
            'IX_InventoryMovement_Sale_OrderItem'
        AND object_id
            = OBJECT_ID(
                'inventory.InventoryMovement'
            )
)
BEGIN

    CREATE INDEX
        IX_InventoryMovement_Sale_OrderItem

    ON inventory.InventoryMovement
    (
        OrderItemId
    )

    INCLUDE
    (
        StoreId,
        ProductId,
        MovementDateTime,
        QuantityChange
    )

    WHERE
        MovementType = 'SALE'
        AND OrderItemId IS NOT NULL;

END;
GO


/* =========================================================
   11. STORE PRODUCT INVENTORY
   Product-first analysis.

   Existing PK:
   StoreId, ProductId

   This provides reverse access:
   ProductId, StoreId
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name =
            'IX_StoreProductInventory_Product'
        AND object_id
            = OBJECT_ID(
                'inventory.StoreProductInventory'
            )
)
BEGIN

    CREATE INDEX
        IX_StoreProductInventory_Product

    ON inventory.StoreProductInventory
    (
        ProductId,
        StoreId
    )

    INCLUDE
    (
        CurrentStock,
        ReorderPoint,
        ReorderQuantity
    );

END;
GO


/* =========================================================
   12. TARGETS
   Store + Period

   Unique constraint already exists on:
   StoreId, TargetYear, TargetMonth

   We additionally support period-first company analytics.
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name =
            'IX_StoreMonthlyTarget_Period'
        AND object_id
            = OBJECT_ID(
                'sales.StoreMonthlyTarget'
            )
)
BEGIN

    CREATE INDEX
        IX_StoreMonthlyTarget_Period

    ON sales.StoreMonthlyTarget
    (
        TargetYear,
        TargetMonth,
        StoreId
    )

    INCLUDE
    (
        RevenueTarget,
        GrossProfitTarget,
        OrdersTarget
    );

END;
GO


/* =========================================================
   13. CUSTOMER SEGMENT HISTORY
   Current segment lookup
   ========================================================= */

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        name =
            'IX_CustomerSegmentHistory_Customer'
        AND object_id
            = OBJECT_ID(
                'customer.CustomerSegmentHistory'
            )
)
BEGIN

    CREATE INDEX
        IX_CustomerSegmentHistory_Customer

    ON customer.CustomerSegmentHistory
    (
        CustomerId,
        EffectiveFrom
    )

    INCLUDE
    (
        SegmentName,
        EffectiveTo,
        IsCurrent
    );

END;
GO






