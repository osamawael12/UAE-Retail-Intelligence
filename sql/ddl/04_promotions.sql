/*
============================================================
 UAE Retail Intelligence Platform
 File: 04_promotions.sql
 Purpose: Promotions and targeting
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Promotion
   ========================================================= */

CREATE TABLE sales.Promotion
(
    PromotionId       INT IDENTITY(1,1) NOT NULL,

    PromotionCode     VARCHAR(30) NOT NULL,
    PromotionName     NVARCHAR(150) NOT NULL,

    PromotionType     VARCHAR(30) NOT NULL,

    DiscountType      VARCHAR(20) NOT NULL,
    DiscountValue     DECIMAL(19,4) NOT NULL,

    StartDate         DATE NOT NULL,
    EndDate           DATE NOT NULL,

    IsActive           BIT NOT NULL
        CONSTRAINT DF_Promotion_IsActive DEFAULT (1),

    CONSTRAINT PK_Promotion
        PRIMARY KEY (PromotionId),

    CONSTRAINT UQ_Promotion_Code
        UNIQUE (PromotionCode),

    CONSTRAINT CK_Promotion_Type
        CHECK (
            PromotionType IN (
                'SEASONAL',
                'PRODUCT',
                'CATEGORY',
                'STORE'
            )
        ),

    CONSTRAINT CK_Promotion_DiscountType
        CHECK (
            DiscountType IN (
                'PERCENTAGE',
                'FIXED_AMOUNT'
            )
        ),

    CONSTRAINT CK_Promotion_DiscountValue
        CHECK (
            DiscountValue >= 0
            AND
            (
                DiscountType <> 'PERCENTAGE'
                OR DiscountValue <= 100
            )
        ),

    CONSTRAINT CK_Promotion_Dates
        CHECK (
            EndDate >= StartDate
        )
);
GO


/* =========================================================
   2. Promotion Product
   ========================================================= */

CREATE TABLE sales.PromotionProduct
(
    PromotionId     INT NOT NULL,
    ProductId       INT NOT NULL,

    CONSTRAINT PK_PromotionProduct
        PRIMARY KEY (
            PromotionId,
            ProductId
        ),

    CONSTRAINT FK_PromotionProduct_Promotion
        FOREIGN KEY (PromotionId)
        REFERENCES sales.Promotion (PromotionId),

    CONSTRAINT FK_PromotionProduct_Product
        FOREIGN KEY (ProductId)
        REFERENCES product.Product (ProductId)
);
GO


/* =========================================================
   3. Promotion Category
   ========================================================= */

CREATE TABLE sales.PromotionCategory
(
    PromotionId     INT NOT NULL,
    CategoryId      INT NOT NULL,

    CONSTRAINT PK_PromotionCategory
        PRIMARY KEY (
            PromotionId,
            CategoryId
        ),

    CONSTRAINT FK_PromotionCategory_Promotion
        FOREIGN KEY (PromotionId)
        REFERENCES sales.Promotion (PromotionId),

    CONSTRAINT FK_PromotionCategory_Category
        FOREIGN KEY (CategoryId)
        REFERENCES product.Category (CategoryId)
);
GO


/* =========================================================
   4. Promotion Store
   ========================================================= */

CREATE TABLE sales.PromotionStore
(
    PromotionId     INT NOT NULL,
    StoreId         INT NOT NULL,

    CONSTRAINT PK_PromotionStore
        PRIMARY KEY (
            PromotionId,
            StoreId
        ),

    CONSTRAINT FK_PromotionStore_Promotion
        FOREIGN KEY (PromotionId)
        REFERENCES sales.Promotion (PromotionId),

    CONSTRAINT FK_PromotionStore_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId)
);
GO