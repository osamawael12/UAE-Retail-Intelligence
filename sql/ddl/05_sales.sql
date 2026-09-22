/*
============================================================
 UAE Retail Intelligence Platform
 File: 05_sales.sql
 Purpose: Sales orders, order items and payments
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Sales Order
   ========================================================= */

CREATE TABLE sales.SalesOrder
(
    OrderId             BIGINT IDENTITY(1,1) NOT NULL,

    OrderNumber         VARCHAR(30) NOT NULL,

    CustomerId          INT NOT NULL,
    StoreId             INT NOT NULL,
    SalesChannelId      SMALLINT NOT NULL,
    DateKey             INT NOT NULL,

    OrderDateTime       DATETIME2(0) NOT NULL,

    OrderStatus         VARCHAR(20) NOT NULL,

    GrossAmount         DECIMAL(19,4) NOT NULL,
    DiscountAmount      DECIMAL(19,4) NOT NULL,
    NetAmount           DECIMAL(19,4) NOT NULL,
    VATAmount           DECIMAL(19,4) NOT NULL,
    CustomerTotal       DECIMAL(19,4) NOT NULL,

    CreatedAt           DATETIME2(3) NOT NULL
        CONSTRAINT DF_SalesOrder_CreatedAt
        DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_SalesOrder
        PRIMARY KEY (OrderId),

    CONSTRAINT UQ_SalesOrder_OrderNumber
        UNIQUE (OrderNumber),

    CONSTRAINT FK_SalesOrder_Customer
        FOREIGN KEY (CustomerId)
        REFERENCES customer.Customer (CustomerId),

    CONSTRAINT FK_SalesOrder_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId),

    CONSTRAINT FK_SalesOrder_Channel
        FOREIGN KEY (SalesChannelId)
        REFERENCES core.SalesChannel (SalesChannelId),

    CONSTRAINT FK_SalesOrder_Date
        FOREIGN KEY (DateKey)
        REFERENCES core.DateDimension (DateKey),

    CONSTRAINT CK_SalesOrder_Status
        CHECK (
            OrderStatus IN (
                'COMPLETED',
                'CANCELLED'
            )
        ),

    CONSTRAINT CK_SalesOrder_Gross
        CHECK (GrossAmount >= 0),

    CONSTRAINT CK_SalesOrder_Discount
        CHECK (
            DiscountAmount >= 0
            AND DiscountAmount <= GrossAmount
        ),

    CONSTRAINT CK_SalesOrder_Net
        CHECK (
            NetAmount >= 0
            AND NetAmount = GrossAmount - DiscountAmount
        ),

    CONSTRAINT CK_SalesOrder_VAT
        CHECK (VATAmount >= 0),

    CONSTRAINT CK_SalesOrder_Total
        CHECK (
            CustomerTotal >= 0
            AND CustomerTotal = NetAmount + VATAmount
        )
);
GO


/* =========================================================
   2. Sales Order Item
   ========================================================= */

CREATE TABLE sales.SalesOrderItem
(
    OrderItemId         BIGINT IDENTITY(1,1) NOT NULL,

    OrderId             BIGINT NOT NULL,
    ProductId           INT NOT NULL,

    PromotionId         INT NULL,

    Quantity            SMALLINT NOT NULL,

    UnitPrice           DECIMAL(19,4) NOT NULL,
    UnitCost            DECIMAL(19,4) NOT NULL,

    GrossAmount         DECIMAL(19,4) NOT NULL,
    DiscountAmount      DECIMAL(19,4) NOT NULL,
    NetAmount           DECIMAL(19,4) NOT NULL,

    VATRate             DECIMAL(9,6) NOT NULL,
    VATAmount           DECIMAL(19,4) NOT NULL,

    CustomerTotal       DECIMAL(19,4) NOT NULL,

    LineCOGS            DECIMAL(19,4) NOT NULL,

    CONSTRAINT PK_SalesOrderItem
        PRIMARY KEY (OrderItemId),

    CONSTRAINT FK_SalesOrderItem_Order
        FOREIGN KEY (OrderId)
        REFERENCES sales.SalesOrder (OrderId),

    CONSTRAINT FK_SalesOrderItem_Product
        FOREIGN KEY (ProductId)
        REFERENCES product.Product (ProductId),

    CONSTRAINT FK_SalesOrderItem_Promotion
        FOREIGN KEY (PromotionId)
        REFERENCES sales.Promotion (PromotionId),

    CONSTRAINT CK_SalesOrderItem_Quantity
        CHECK (Quantity > 0),

    CONSTRAINT CK_SalesOrderItem_UnitPrice
        CHECK (UnitPrice >= 0),

    CONSTRAINT CK_SalesOrderItem_UnitCost
        CHECK (UnitCost >= 0),

    CONSTRAINT CK_SalesOrderItem_Gross
        CHECK (
            GrossAmount >= 0
            AND GrossAmount = UnitPrice * Quantity
        ),

    CONSTRAINT CK_SalesOrderItem_Discount
        CHECK (
            DiscountAmount >= 0
            AND DiscountAmount <= GrossAmount
        ),

    CONSTRAINT CK_SalesOrderItem_Net
        CHECK (
            NetAmount >= 0
            AND NetAmount = GrossAmount - DiscountAmount
        ),

    CONSTRAINT CK_SalesOrderItem_VATRate
        CHECK (
            VATRate >= 0
            AND VATRate <= 1
        ),

    CONSTRAINT CK_SalesOrderItem_VAT
        CHECK (
            VATAmount >= 0
            AND VATAmount = ROUND(NetAmount * VATRate, 4)
        ),

    CONSTRAINT CK_SalesOrderItem_Total
        CHECK (
            CustomerTotal >= 0
            AND CustomerTotal = NetAmount + VATAmount
        ),

    CONSTRAINT CK_SalesOrderItem_COGS
        CHECK (
            LineCOGS >= 0
            AND LineCOGS = UnitCost * Quantity
        )
);
GO


/* =========================================================
   3. Order Payment
   ========================================================= */

CREATE TABLE sales.OrderPayment
(
    OrderPaymentId      BIGINT IDENTITY(1,1) NOT NULL,

    OrderId             BIGINT NOT NULL,

    PaymentMethodId     SMALLINT NOT NULL,

    PaymentAmount       DECIMAL(19,4) NOT NULL,

    PaymentDateTime     DATETIME2(0) NOT NULL,

    PaymentReference    VARCHAR(100) NULL,

    CONSTRAINT PK_OrderPayment
        PRIMARY KEY (OrderPaymentId),

    CONSTRAINT FK_OrderPayment_Order
        FOREIGN KEY (OrderId)
        REFERENCES sales.SalesOrder (OrderId),

    CONSTRAINT FK_OrderPayment_Method
        FOREIGN KEY (PaymentMethodId)
        REFERENCES core.PaymentMethod (PaymentMethodId),

    CONSTRAINT CK_OrderPayment_Amount
        CHECK (PaymentAmount > 0)
);
GO