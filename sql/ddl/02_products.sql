/*
============================================================
 UAE Retail Intelligence Platform
 File: 02_products.sql
 Purpose: Product catalog and supplier tables
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Category
   ========================================================= */

CREATE TABLE product.Category
(
    CategoryId      INT IDENTITY(1,1) NOT NULL,
    CategoryName    NVARCHAR(100) NOT NULL,

    IsActive        BIT NOT NULL
        CONSTRAINT DF_Category_IsActive DEFAULT (1),

    CONSTRAINT PK_Category
        PRIMARY KEY (CategoryId),

    CONSTRAINT UQ_Category_Name
        UNIQUE (CategoryName)
);
GO


/* =========================================================
   2. Subcategory
   ========================================================= */

CREATE TABLE product.Subcategory
(
    SubcategoryId      INT IDENTITY(1,1) NOT NULL,
    CategoryId         INT NOT NULL,
    SubcategoryName    NVARCHAR(100) NOT NULL,

    IsActive           BIT NOT NULL
        CONSTRAINT DF_Subcategory_IsActive DEFAULT (1),

    CONSTRAINT PK_Subcategory
        PRIMARY KEY (SubcategoryId),

    CONSTRAINT FK_Subcategory_Category
        FOREIGN KEY (CategoryId)
        REFERENCES product.Category (CategoryId),

    CONSTRAINT UQ_Subcategory_Category_Name
        UNIQUE (CategoryId, SubcategoryName)
);
GO


/* =========================================================
   3. Brand
   ========================================================= */

CREATE TABLE product.Brand
(
    BrandId       INT IDENTITY(1,1) NOT NULL,
    BrandName     NVARCHAR(100) NOT NULL,

    IsActive      BIT NOT NULL
        CONSTRAINT DF_Brand_IsActive DEFAULT (1),

    CONSTRAINT PK_Brand
        PRIMARY KEY (BrandId),

    CONSTRAINT UQ_Brand_Name
        UNIQUE (BrandName)
);
GO


/* =========================================================
   4. Supplier
   ========================================================= */

CREATE TABLE product.Supplier
(
    SupplierId       INT IDENTITY(1,1) NOT NULL,
    SupplierCode     VARCHAR(20) NOT NULL,
    SupplierName     NVARCHAR(150) NOT NULL,

    ContactEmail     NVARCHAR(254) NULL,
    ContactPhone     VARCHAR(30) NULL,

    IsActive         BIT NOT NULL
        CONSTRAINT DF_Supplier_IsActive DEFAULT (1),

    CONSTRAINT PK_Supplier
        PRIMARY KEY (SupplierId),

    CONSTRAINT UQ_Supplier_Code
        UNIQUE (SupplierCode)
);
GO


/* =========================================================
   5. Product
   ========================================================= */

CREATE TABLE product.Product
(
    ProductId                 INT IDENTITY(1,1) NOT NULL,

    SubcategoryId             INT NOT NULL,
    BrandId                   INT NOT NULL,

    SKU                       VARCHAR(30) NOT NULL,
    ProductName               NVARCHAR(200) NOT NULL,

    BaseSellingPrice          DECIMAL(19,4) NOT NULL,
    StandardCost              DECIMAL(19,4) NOT NULL,

    DefaultVATRate            DECIMAL(9,6) NOT NULL
        CONSTRAINT DF_Product_VATRate DEFAULT (0.05),

    PopularityScore           DECIMAL(9,6) NOT NULL,

    SeasonalityProfile        VARCHAR(30) NOT NULL,

    BaseReturnProbability     DECIMAL(9,6) NOT NULL,

    LaunchDate                DATE NOT NULL,
    DiscontinuedDate          DATE NULL,

    IsActive                  BIT NOT NULL
        CONSTRAINT DF_Product_IsActive DEFAULT (1),

    CONSTRAINT PK_Product
        PRIMARY KEY (ProductId),

    CONSTRAINT UQ_Product_SKU
        UNIQUE (SKU),

    CONSTRAINT FK_Product_Subcategory
        FOREIGN KEY (SubcategoryId)
        REFERENCES product.Subcategory (SubcategoryId),

    CONSTRAINT FK_Product_Brand
        FOREIGN KEY (BrandId)
        REFERENCES product.Brand (BrandId),

    CONSTRAINT CK_Product_BaseSellingPrice
        CHECK (BaseSellingPrice >= 0),

    CONSTRAINT CK_Product_StandardCost
        CHECK (StandardCost >= 0),

    CONSTRAINT CK_Product_VATRate
        CHECK (
            DefaultVATRate >= 0
            AND DefaultVATRate <= 1
        ),

    CONSTRAINT CK_Product_Popularity
        CHECK (
            PopularityScore >= 0
            AND PopularityScore <= 1
        ),

    CONSTRAINT CK_Product_ReturnProbability
        CHECK (
            BaseReturnProbability >= 0
            AND BaseReturnProbability <= 1
        ),

    CONSTRAINT CK_Product_SeasonalityProfile
        CHECK (
            SeasonalityProfile IN
            (
                'STABLE',
                'RAMADAN',
                'EID',
                'SUMMER',
                'WHITE_FRIDAY',
                'YEAR_END'
            )
        ),

    CONSTRAINT CK_Product_Lifecycle
        CHECK (
            DiscontinuedDate IS NULL
            OR DiscontinuedDate >= LaunchDate
        )
);
GO


/* =========================================================
   6. Product Supplier
   ========================================================= */

CREATE TABLE product.ProductSupplier
(
    ProductId              INT NOT NULL,
    SupplierId             INT NOT NULL,

    SupplierProductCode    VARCHAR(50) NULL,

    SupplierCost           DECIMAL(19,4) NOT NULL,
    LeadTimeDays           SMALLINT NOT NULL,

    IsPrimarySupplier      BIT NOT NULL
        CONSTRAINT DF_ProductSupplier_Primary DEFAULT (0),

    IsActive               BIT NOT NULL
        CONSTRAINT DF_ProductSupplier_Active DEFAULT (1),

    CONSTRAINT PK_ProductSupplier
        PRIMARY KEY (ProductId, SupplierId),

    CONSTRAINT FK_ProductSupplier_Product
        FOREIGN KEY (ProductId)
        REFERENCES product.Product (ProductId),

    CONSTRAINT FK_ProductSupplier_Supplier
        FOREIGN KEY (SupplierId)
        REFERENCES product.Supplier (SupplierId),

    CONSTRAINT CK_ProductSupplier_Cost
        CHECK (SupplierCost >= 0),

    CONSTRAINT CK_ProductSupplier_LeadTime
        CHECK (LeadTimeDays >= 0)
);
GO


/* =========================================================
   Filtered Unique Index

   A product can have many suppliers,
   but at most one ACTIVE primary supplier.
   ========================================================= */

CREATE UNIQUE INDEX UX_ProductSupplier_ActivePrimary
ON product.ProductSupplier (ProductId)
WHERE IsPrimarySupplier = 1
  AND IsActive = 1;
GO








SELECT
    s.name AS SchemaName,
    t.name AS TableName
FROM sys.tables t
INNER JOIN sys.schemas s
    ON t.schema_id = s.schema_id
WHERE s.name = 'product'
ORDER BY t.name;