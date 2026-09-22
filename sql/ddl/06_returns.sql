/*
============================================================
 UAE Retail Intelligence Platform
 File: 06_returns.sql
 Purpose: Product returns and customer refunds
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Return Header
   ========================================================= */

CREATE TABLE sales.[Return]
(
    ReturnId                BIGINT IDENTITY(1,1) NOT NULL,

    ReturnNumber            VARCHAR(30) NOT NULL,

    OrderId                 BIGINT NOT NULL,

    StoreId                 INT NOT NULL,

    DateKey                 INT NOT NULL,

    ReturnDateTime          DATETIME2(0) NOT NULL,

    ReturnStatus            VARCHAR(20) NOT NULL,

    TotalReturnNetAmount    DECIMAL(19,4) NOT NULL,

    TotalVATReversed        DECIMAL(19,4) NOT NULL,

    TotalRefundAmount       DECIMAL(19,4) NOT NULL,

    CreatedAt               DATETIME2(3) NOT NULL
        CONSTRAINT DF_Return_CreatedAt
        DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_Return
        PRIMARY KEY (ReturnId),

    CONSTRAINT UQ_Return_Number
        UNIQUE (ReturnNumber),

    CONSTRAINT FK_Return_Order
        FOREIGN KEY (OrderId)
        REFERENCES sales.SalesOrder (OrderId),

    CONSTRAINT FK_Return_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId),

    CONSTRAINT FK_Return_Date
        FOREIGN KEY (DateKey)
        REFERENCES core.DateDimension (DateKey),

    CONSTRAINT CK_Return_Status
        CHECK (
            ReturnStatus IN (
                'COMPLETED',
                'REJECTED'
            )
        ),

    CONSTRAINT CK_Return_NetAmount
        CHECK (TotalReturnNetAmount >= 0),

    CONSTRAINT CK_Return_VAT
        CHECK (TotalVATReversed >= 0),

    CONSTRAINT CK_Return_Refund
        CHECK (
            TotalRefundAmount >= 0
            AND
            TotalRefundAmount
                <= TotalReturnNetAmount + TotalVATReversed
        )
);
GO


/* =========================================================
   2. Return Item
   ========================================================= */

CREATE TABLE sales.ReturnItem
(
    ReturnItemId         BIGINT IDENTITY(1,1) NOT NULL,

    ReturnId             BIGINT NOT NULL,

    OrderItemId          BIGINT NOT NULL,

    ReturnQuantity       SMALLINT NOT NULL,

    ReturnReason         VARCHAR(50) NOT NULL,

    ReturnedNetAmount    DECIMAL(19,4) NOT NULL,

    VATReversed          DECIMAL(19,4) NOT NULL,

    RefundAmount         DECIMAL(19,4) NOT NULL,

    IsRestockable        BIT NOT NULL
        CONSTRAINT DF_ReturnItem_Restockable DEFAULT (1),

    CONSTRAINT PK_ReturnItem
        PRIMARY KEY (ReturnItemId),

    CONSTRAINT FK_ReturnItem_Return
        FOREIGN KEY (ReturnId)
        REFERENCES sales.[Return] (ReturnId),

    CONSTRAINT FK_ReturnItem_OrderItem
        FOREIGN KEY (OrderItemId)
        REFERENCES sales.SalesOrderItem (OrderItemId),

    CONSTRAINT CK_ReturnItem_Quantity
        CHECK (ReturnQuantity > 0),

    CONSTRAINT CK_ReturnItem_Reason
        CHECK (
            ReturnReason IN (
                'DEFECTIVE_PRODUCT',
                'WRONG_ITEM',
                'SIZE_FIT_ISSUE',
                'CHANGED_MIND',
                'DAMAGED_PRODUCT',
                'OTHER'
            )
        ),

    CONSTRAINT CK_ReturnItem_NetAmount
        CHECK (ReturnedNetAmount >= 0),

    CONSTRAINT CK_ReturnItem_VAT
        CHECK (VATReversed >= 0),

    CONSTRAINT CK_ReturnItem_Refund
        CHECK (
            RefundAmount >= 0
            AND
            RefundAmount <= ReturnedNetAmount + VATReversed
        )
);
GO


/* =========================================================
   3. Refund
   ========================================================= */

CREATE TABLE sales.Refund
(
    RefundId             BIGINT IDENTITY(1,1) NOT NULL,

    ReturnId             BIGINT NOT NULL,

    PaymentMethodId      SMALLINT NOT NULL,

    RefundAmount         DECIMAL(19,4) NOT NULL,

    RefundDateTime       DATETIME2(0) NOT NULL,

    RefundReference      VARCHAR(100) NULL,

    RefundStatus         VARCHAR(20) NOT NULL,

    CONSTRAINT PK_Refund
        PRIMARY KEY (RefundId),

    CONSTRAINT FK_Refund_Return
        FOREIGN KEY (ReturnId)
        REFERENCES sales.[Return] (ReturnId),

    CONSTRAINT FK_Refund_PaymentMethod
        FOREIGN KEY (PaymentMethodId)
        REFERENCES core.PaymentMethod (PaymentMethodId),

    CONSTRAINT CK_Refund_Amount
        CHECK (RefundAmount > 0),

    CONSTRAINT CK_Refund_Status
        CHECK (
            RefundStatus IN (
                'COMPLETED',
                'PENDING',
                'FAILED'
            )
        )
);
GO