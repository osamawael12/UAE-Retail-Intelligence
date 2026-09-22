/*
============================================================
 UAE Retail Intelligence Platform
 File: 03_customers.sql
 Purpose: Customer master and segment history
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Customer
   ========================================================= */

CREATE TABLE customer.Customer
(
    CustomerId             INT IDENTITY(1,1) NOT NULL,

    CustomerCode           VARCHAR(30) NOT NULL,

    FirstName              NVARCHAR(100) NOT NULL,
    LastName               NVARCHAR(100) NOT NULL,

    Gender                 VARCHAR(20) NULL,
    DateOfBirth            DATE NULL,

    Email                  NVARCHAR(254) NULL,
    Phone                  VARCHAR(30) NULL,
    Nationality            NVARCHAR(100) NULL,

    RegistrationDate       DATE NOT NULL,

    PreferredEmirateId     INT NULL,
    PreferredChannelId     SMALLINT NULL,

    IsActive               BIT NOT NULL
        CONSTRAINT DF_Customer_IsActive DEFAULT (1),

    CONSTRAINT PK_Customer
        PRIMARY KEY (CustomerId),

    CONSTRAINT UQ_Customer_Code
        UNIQUE (CustomerCode),

    CONSTRAINT FK_Customer_PreferredEmirate
        FOREIGN KEY (PreferredEmirateId)
        REFERENCES core.Emirate (EmirateId),

    CONSTRAINT FK_Customer_PreferredChannel
        FOREIGN KEY (PreferredChannelId)
        REFERENCES core.SalesChannel (SalesChannelId),

    CONSTRAINT CK_Customer_Gender
        CHECK (
            Gender IS NULL
            OR Gender IN (
                'MALE',
                'FEMALE',
                'OTHER',
                'PREFER_NOT_TO_SAY'
            )
        ),

    CONSTRAINT CK_Customer_BirthDate
        CHECK (
            DateOfBirth IS NULL
            OR DateOfBirth < RegistrationDate
        )
);
GO


/* =========================================================
   2. Customer Segment History
   ========================================================= */

CREATE TABLE customer.CustomerSegmentHistory
(
    CustomerSegmentHistoryId
        BIGINT IDENTITY(1,1) NOT NULL,

    CustomerId       INT NOT NULL,

    SegmentName      VARCHAR(50) NOT NULL,

    EffectiveFrom    DATE NOT NULL,
    EffectiveTo      DATE NULL,

    IsCurrent        BIT NOT NULL
        CONSTRAINT DF_CustomerSegment_IsCurrent DEFAULT (0),

    CONSTRAINT PK_CustomerSegmentHistory
        PRIMARY KEY (CustomerSegmentHistoryId),

    CONSTRAINT FK_CustomerSegment_Customer
        FOREIGN KEY (CustomerId)
        REFERENCES customer.Customer (CustomerId),

    CONSTRAINT CK_CustomerSegment_Name
        CHECK (
            SegmentName IN (
                'VIP',
                'LOYAL',
                'REGULAR',
                'DISCOUNT_SEEKER',
                'AT_RISK'
            )
        ),

    CONSTRAINT CK_CustomerSegment_Dates
        CHECK (
            EffectiveTo IS NULL
            OR EffectiveTo >= EffectiveFrom
        ),

    CONSTRAINT CK_CustomerSegment_Current
        CHECK (
            (IsCurrent = 1 AND EffectiveTo IS NULL)
            OR
            (IsCurrent = 0)
        )
);
GO


/* =========================================================
   At most one current segment per customer
   ========================================================= */

CREATE UNIQUE INDEX UX_CustomerSegment_Current
ON customer.CustomerSegmentHistory (CustomerId)
WHERE IsCurrent = 1;
GO