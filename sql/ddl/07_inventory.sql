/*
============================================================
 UAE Retail Intelligence Platform
 File: 07_inventory.sql
 Purpose: Store inventory state and movement ledger
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Store Product Inventory
   ========================================================= */

CREATE TABLE inventory.StoreProductInventory
(
    StoreId            INT NOT NULL,
    ProductId          INT NOT NULL,

    ReorderPoint       INT NOT NULL,
    ReorderQuantity    INT NOT NULL,

    CurrentStock       INT NOT NULL,

    LastUpdatedAt      DATETIME2(3) NOT NULL
        CONSTRAINT DF_StoreProductInventory_UpdatedAt
        DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_StoreProductInventory
        PRIMARY KEY (StoreId, ProductId),

    CONSTRAINT FK_StoreProductInventory_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId),

    CONSTRAINT FK_StoreProductInventory_Product
        FOREIGN KEY (ProductId)
        REFERENCES product.Product (ProductId),

    CONSTRAINT CK_StoreProductInventory_ReorderPoint
        CHECK (ReorderPoint >= 0),

    CONSTRAINT CK_StoreProductInventory_ReorderQuantity
        CHECK (ReorderQuantity > 0),

    CONSTRAINT CK_StoreProductInventory_CurrentStock
        CHECK (CurrentStock >= 0)
);
GO


/* =========================================================
   2. Inventory Movement
   ========================================================= */

CREATE TABLE inventory.InventoryMovement
(
    InventoryMovementId    BIGINT IDENTITY(1,1) NOT NULL,

    StoreId                INT NOT NULL,
    ProductId              INT NOT NULL,

    OrderItemId            BIGINT NULL,
    ReturnItemId           BIGINT NULL,

    MovementDateTime       DATETIME2(0) NOT NULL,

    MovementType           VARCHAR(20) NOT NULL,

    QuantityChange         INT NOT NULL,

    UnitCost               DECIMAL(19,4) NOT NULL,

    ReferenceNumber        VARCHAR(100) NULL,
    Notes                  NVARCHAR(500) NULL,

    CONSTRAINT PK_InventoryMovement
        PRIMARY KEY (InventoryMovementId),

    CONSTRAINT FK_InventoryMovement_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId),

    CONSTRAINT FK_InventoryMovement_Product
        FOREIGN KEY (ProductId)
        REFERENCES product.Product (ProductId),

    CONSTRAINT FK_InventoryMovement_OrderItem
        FOREIGN KEY (OrderItemId)
        REFERENCES sales.SalesOrderItem (OrderItemId),

    CONSTRAINT FK_InventoryMovement_ReturnItem
        FOREIGN KEY (ReturnItemId)
        REFERENCES sales.ReturnItem (ReturnItemId),

    CONSTRAINT CK_InventoryMovement_Type
        CHECK (
            MovementType IN (
                'PURCHASE',
                'SALE',
                'RETURN',
                'TRANSFER_IN',
                'TRANSFER_OUT',
                'DAMAGED',
                'ADJUSTMENT'
            )
        ),

    CONSTRAINT CK_InventoryMovement_Quantity
        CHECK (QuantityChange <> 0),

    CONSTRAINT CK_InventoryMovement_Cost
        CHECK (UnitCost >= 0),

    CONSTRAINT CK_InventoryMovement_Sign
        CHECK (
               (MovementType = 'PURCHASE'
                    AND QuantityChange > 0)

            OR (MovementType = 'SALE'
                    AND QuantityChange < 0)

            OR (MovementType = 'RETURN'
                    AND QuantityChange > 0)

            OR (MovementType = 'TRANSFER_IN'
                    AND QuantityChange > 0)

            OR (MovementType = 'TRANSFER_OUT'
                    AND QuantityChange < 0)

            OR (MovementType = 'DAMAGED'
                    AND QuantityChange < 0)

            OR (MovementType = 'ADJUSTMENT')
        )
);
GO