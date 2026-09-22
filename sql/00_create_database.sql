/*
============================================================
 UAE Retail Intelligence Platform
 Database Initialization
============================================================
*/

USE master;
GO

IF DB_ID(N'UAERetailAnalytics') IS NULL
BEGIN
    CREATE DATABASE UAERetailAnalytics;
END;
GO

USE UAERetailAnalytics;
GO

SELECT
    DB_NAME() AS CurrentDatabase;
GO