/*
============================================================
 UAE Retail Intelligence Platform
 File: 08_targets.sql
 Purpose: Monthly store performance targets
============================================================
*/

USE UAERetailAnalytics;
GO


CREATE TABLE sales.StoreMonthlyTarget
(
    StoreMonthlyTargetId    BIGINT IDENTITY(1,1) NOT NULL,

    StoreId                 INT NOT NULL,

    TargetYear              SMALLINT NOT NULL,
    TargetMonth             TINYINT NOT NULL,

    RevenueTarget           DECIMAL(19,4) NOT NULL,
    GrossProfitTarget       DECIMAL(19,4) NOT NULL,
    OrdersTarget            INT NOT NULL,

    CreatedAt               DATETIME2(3) NOT NULL
        CONSTRAINT DF_StoreMonthlyTarget_CreatedAt
        DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_StoreMonthlyTarget
        PRIMARY KEY (StoreMonthlyTargetId),

    CONSTRAINT FK_StoreMonthlyTarget_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId),

    CONSTRAINT UQ_StoreMonthlyTarget_Period
        UNIQUE (
            StoreId,
            TargetYear,
            TargetMonth
        ),

    CONSTRAINT CK_StoreMonthlyTarget_Year
        CHECK (
            TargetYear BETWEEN 2023 AND 2025
        ),

    CONSTRAINT CK_StoreMonthlyTarget_Month
        CHECK (
            TargetMonth BETWEEN 1 AND 12
        ),

    CONSTRAINT CK_StoreMonthlyTarget_Revenue
        CHECK (RevenueTarget >= 0),

    CONSTRAINT CK_StoreMonthlyTarget_Profit
        CHECK (GrossProfitTarget >= 0),

    CONSTRAINT CK_StoreMonthlyTarget_Orders
        CHECK (OrdersTarget >= 0)
);
GO