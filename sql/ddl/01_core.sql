/*
============================================================
 UAE Retail Intelligence Platform
 File: 01_core.sql
 Purpose: Core reference and organizational tables
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Emirate
   ========================================================= */

CREATE TABLE core.Emirate
(
    EmirateId      INT IDENTITY(1,1) NOT NULL,
    EmirateCode    VARCHAR(10) NOT NULL,
    EmirateName    NVARCHAR(50) NOT NULL,
    IsActive       BIT NOT NULL
        CONSTRAINT DF_Emirate_IsActive DEFAULT (1),

    CONSTRAINT PK_Emirate
        PRIMARY KEY (EmirateId),

    CONSTRAINT UQ_Emirate_Code
        UNIQUE (EmirateCode),

    CONSTRAINT UQ_Emirate_Name
        UNIQUE (EmirateName)
);
GO


/* =========================================================
   2. City
   ========================================================= */

CREATE TABLE core.City
(
    CityId          INT IDENTITY(1,1) NOT NULL,
    EmirateId       INT NOT NULL,
    CityName        NVARCHAR(100) NOT NULL,
    IsActive        BIT NOT NULL
        CONSTRAINT DF_City_IsActive DEFAULT (1),

    CONSTRAINT PK_City
        PRIMARY KEY (CityId),

    CONSTRAINT FK_City_Emirate
        FOREIGN KEY (EmirateId)
        REFERENCES core.Emirate (EmirateId),

    CONSTRAINT UQ_City_Emirate_Name
        UNIQUE (EmirateId, CityName)
);
GO


/* =========================================================
   3. Store
   ========================================================= */

CREATE TABLE core.Store
(
    StoreId          INT IDENTITY(1,1) NOT NULL,
    CityId           INT NOT NULL,
    StoreCode        VARCHAR(20) NOT NULL,
    StoreName        NVARCHAR(150) NOT NULL,
    OpenDate         DATE NOT NULL,
    StoreType        VARCHAR(30) NOT NULL,
    FloorAreaSqM     DECIMAL(10,2) NULL,
    IsActive         BIT NOT NULL
        CONSTRAINT DF_Store_IsActive DEFAULT (1),

    CONSTRAINT PK_Store
        PRIMARY KEY (StoreId),

    CONSTRAINT UQ_Store_Code
        UNIQUE (StoreCode),

    CONSTRAINT FK_Store_City
        FOREIGN KEY (CityId)
        REFERENCES core.City (CityId),

    CONSTRAINT CK_Store_Type
        CHECK (
            StoreType IN (
                'MALL',
                'HIGH_STREET',
                'COMMUNITY'
            )
        ),

    CONSTRAINT CK_Store_FloorArea
        CHECK (
            FloorAreaSqM IS NULL
            OR FloorAreaSqM > 0
        )
);
GO


/* =========================================================
   4. Date Dimension
   ========================================================= */

CREATE TABLE core.DateDimension
(
    DateKey               INT NOT NULL,
    FullDate              DATE NOT NULL,

    DayNumber             TINYINT NOT NULL,
    DayName               VARCHAR(10) NOT NULL,
    DayOfWeekNumber       TINYINT NOT NULL,

    WeekOfYear            TINYINT NOT NULL,

    MonthNumber           TINYINT NOT NULL,
    MonthName             VARCHAR(10) NOT NULL,

    QuarterNumber         TINYINT NOT NULL,
    YearNumber            SMALLINT NOT NULL,

    IsWeekend             BIT NOT NULL,

    IsRamadan             BIT NOT NULL
        CONSTRAINT DF_Date_IsRamadan DEFAULT (0),

    IsEidAlFitr           BIT NOT NULL
        CONSTRAINT DF_Date_IsEidAlFitr DEFAULT (0),

    IsEidAlAdha           BIT NOT NULL
        CONSTRAINT DF_Date_IsEidAlAdha DEFAULT (0),

    IsWhiteFriday         BIT NOT NULL
        CONSTRAINT DF_Date_IsWhiteFriday DEFAULT (0),

    IsEidAlEtihad         BIT NOT NULL
        CONSTRAINT DF_Date_IsEidAlEtihad DEFAULT (0),

    IsSummer              BIT NOT NULL
        CONSTRAINT DF_Date_IsSummer DEFAULT (0),

    IsYearEndSeason       BIT NOT NULL
        CONSTRAINT DF_Date_IsYearEnd DEFAULT (0),

    CONSTRAINT PK_DateDimension
        PRIMARY KEY (DateKey),

    CONSTRAINT UQ_DateDimension_FullDate
        UNIQUE (FullDate),

    CONSTRAINT CK_Date_DayNumber
        CHECK (DayNumber BETWEEN 1 AND 31),

    CONSTRAINT CK_Date_DayOfWeek
        CHECK (DayOfWeekNumber BETWEEN 1 AND 7),

    CONSTRAINT CK_Date_Month
        CHECK (MonthNumber BETWEEN 1 AND 12),

    CONSTRAINT CK_Date_Quarter
        CHECK (QuarterNumber BETWEEN 1 AND 4),

    CONSTRAINT CK_Date_Week
        CHECK (WeekOfYear BETWEEN 1 AND 53),

    CONSTRAINT CK_Date_DateKey
        CHECK (
            DateKey =
                YEAR(FullDate) * 10000
                + MONTH(FullDate) * 100
                + DAY(FullDate)
        )
);
GO


/* =========================================================
   5. Sales Channel
   ========================================================= */

CREATE TABLE core.SalesChannel
(
    SalesChannelId     SMALLINT IDENTITY(1,1) NOT NULL,
    ChannelCode        VARCHAR(20) NOT NULL,
    ChannelName        NVARCHAR(50) NOT NULL,

    IsActive            BIT NOT NULL
        CONSTRAINT DF_SalesChannel_IsActive DEFAULT (1),

    CONSTRAINT PK_SalesChannel
        PRIMARY KEY (SalesChannelId),

    CONSTRAINT UQ_SalesChannel_Code
        UNIQUE (ChannelCode),

    CONSTRAINT UQ_SalesChannel_Name
        UNIQUE (ChannelName)
);
GO


/* =========================================================
   6. Payment Method
   ========================================================= */

CREATE TABLE core.PaymentMethod
(
    PaymentMethodId       SMALLINT IDENTITY(1,1) NOT NULL,
    PaymentMethodCode     VARCHAR(30) NOT NULL,
    PaymentMethodName     NVARCHAR(50) NOT NULL,

    IsActive              BIT NOT NULL
        CONSTRAINT DF_PaymentMethod_IsActive DEFAULT (1),

    CONSTRAINT PK_PaymentMethod
        PRIMARY KEY (PaymentMethodId),

    CONSTRAINT UQ_PaymentMethod_Code
        UNIQUE (PaymentMethodCode),

    CONSTRAINT UQ_PaymentMethod_Name
        UNIQUE (PaymentMethodName)
);
GO


/* =========================================================
   7. Employee
   ========================================================= */

CREATE TABLE core.Employee
(
    EmployeeId        INT IDENTITY(1,1) NOT NULL,
    StoreId           INT NULL,

    EmployeeCode      VARCHAR(20) NOT NULL,

    FirstName         NVARCHAR(100) NOT NULL,
    LastName          NVARCHAR(100) NOT NULL,

    JobTitle          NVARCHAR(100) NOT NULL,

    HireDate          DATE NOT NULL,
    TerminationDate   DATE NULL,

    Email             NVARCHAR(254) NULL,

    IsActive          BIT NOT NULL
        CONSTRAINT DF_Employee_IsActive DEFAULT (1),

    CONSTRAINT PK_Employee
        PRIMARY KEY (EmployeeId),

    CONSTRAINT UQ_Employee_Code
        UNIQUE (EmployeeCode),

    CONSTRAINT FK_Employee_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId),

    CONSTRAINT CK_Employee_Dates
        CHECK (
            TerminationDate IS NULL
            OR TerminationDate >= HireDate
        )
);
GO


USE UAERetailAnalytics;
GO

SELECT
    s.name AS SchemaName,
    t.name AS TableName
FROM sys.tables t
INNER JOIN sys.schemas s
    ON t.schema_id = s.schema_id
WHERE s.name = 'core'
ORDER BY t.name;


SELECT
    t.name AS TableName,
    COUNT(DISTINCT fk.object_id) AS ForeignKeys,
    COUNT(DISTINCT cc.object_id) AS CheckConstraints
FROM sys.tables t
LEFT JOIN sys.foreign_keys fk
    ON fk.parent_object_id = t.object_id
LEFT JOIN sys.check_constraints cc
    ON cc.parent_object_id = t.object_id
WHERE SCHEMA_NAME(t.schema_id) = 'core'
GROUP BY t.name
ORDER BY t.name;

