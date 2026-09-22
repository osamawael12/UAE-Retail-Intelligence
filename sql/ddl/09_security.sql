/*
============================================================
 UAE Retail Intelligence Platform
 File: 09_security.sql
 Purpose: Authentication, RBAC, data scopes and audit
============================================================
*/

USE UAERetailAnalytics;
GO


/* =========================================================
   1. Application User
   ========================================================= */

CREATE TABLE security.AppUser
(
    UserId              INT IDENTITY(1,1) NOT NULL,

    Username            NVARCHAR(100) NOT NULL,
    Email               NVARCHAR(254) NOT NULL,

    PasswordHash        NVARCHAR(500) NOT NULL,

    IsActive            BIT NOT NULL
        CONSTRAINT DF_AppUser_IsActive DEFAULT (1),

    FailedLoginCount    INT NOT NULL
        CONSTRAINT DF_AppUser_FailedLoginCount DEFAULT (0),

    LastLoginAt         DATETIME2(3) NULL,

    CreatedAt           DATETIME2(3) NOT NULL
        CONSTRAINT DF_AppUser_CreatedAt
        DEFAULT SYSUTCDATETIME(),

    UpdatedAt           DATETIME2(3) NOT NULL
        CONSTRAINT DF_AppUser_UpdatedAt
        DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_AppUser
        PRIMARY KEY (UserId),

    CONSTRAINT UQ_AppUser_Username
        UNIQUE (Username),

    CONSTRAINT UQ_AppUser_Email
        UNIQUE (Email),

    CONSTRAINT CK_AppUser_FailedLoginCount
        CHECK (FailedLoginCount >= 0)
);
GO


/* =========================================================
   2. Role
   ========================================================= */

CREATE TABLE security.Role
(
    RoleId          INT IDENTITY(1,1) NOT NULL,

    RoleName        NVARCHAR(100) NOT NULL,

    Description     NVARCHAR(500) NULL,

    CONSTRAINT PK_Role
        PRIMARY KEY (RoleId),

    CONSTRAINT UQ_Role_Name
        UNIQUE (RoleName)
);
GO


/* =========================================================
   3. Permission
   ========================================================= */

CREATE TABLE security.Permission
(
    PermissionId      INT IDENTITY(1,1) NOT NULL,

    PermissionCode    VARCHAR(100) NOT NULL,
    PermissionName    NVARCHAR(150) NOT NULL,

    Description       NVARCHAR(500) NULL,

    CONSTRAINT PK_Permission
        PRIMARY KEY (PermissionId),

    CONSTRAINT UQ_Permission_Code
        UNIQUE (PermissionCode)
);
GO


/* =========================================================
   4. User Role
   ========================================================= */

CREATE TABLE security.UserRole
(
    UserId    INT NOT NULL,
    RoleId    INT NOT NULL,

    CONSTRAINT PK_UserRole
        PRIMARY KEY (UserId, RoleId),

    CONSTRAINT FK_UserRole_User
        FOREIGN KEY (UserId)
        REFERENCES security.AppUser (UserId),

    CONSTRAINT FK_UserRole_Role
        FOREIGN KEY (RoleId)
        REFERENCES security.Role (RoleId)
);
GO


/* =========================================================
   5. Role Permission
   ========================================================= */

CREATE TABLE security.RolePermission
(
    RoleId          INT NOT NULL,
    PermissionId    INT NOT NULL,

    CONSTRAINT PK_RolePermission
        PRIMARY KEY (RoleId, PermissionId),

    CONSTRAINT FK_RolePermission_Role
        FOREIGN KEY (RoleId)
        REFERENCES security.Role (RoleId),

    CONSTRAINT FK_RolePermission_Permission
        FOREIGN KEY (PermissionId)
        REFERENCES security.Permission (PermissionId)
);
GO


/* =========================================================
   6. User Data Scope
   ========================================================= */

CREATE TABLE security.UserDataScope
(
    UserDataScopeId    INT IDENTITY(1,1) NOT NULL,

    UserId             INT NOT NULL,

    ScopeType          VARCHAR(20) NOT NULL,

    EmirateId          INT NULL,
    StoreId            INT NULL,

    IsActive           BIT NOT NULL
        CONSTRAINT DF_UserDataScope_IsActive DEFAULT (1),

    CONSTRAINT PK_UserDataScope
        PRIMARY KEY (UserDataScopeId),

    CONSTRAINT FK_UserDataScope_User
        FOREIGN KEY (UserId)
        REFERENCES security.AppUser (UserId),

    CONSTRAINT FK_UserDataScope_Emirate
        FOREIGN KEY (EmirateId)
        REFERENCES core.Emirate (EmirateId),

    CONSTRAINT FK_UserDataScope_Store
        FOREIGN KEY (StoreId)
        REFERENCES core.Store (StoreId),

    CONSTRAINT CK_UserDataScope_Type
        CHECK (
            ScopeType IN (
                'ALL',
                'EMIRATE',
                'STORE'
            )
        ),

    CONSTRAINT CK_UserDataScope_Consistency
        CHECK (
               (
                    ScopeType = 'ALL'
                    AND EmirateId IS NULL
                    AND StoreId IS NULL
               )

            OR (
                    ScopeType = 'EMIRATE'
                    AND EmirateId IS NOT NULL
                    AND StoreId IS NULL
               )

            OR (
                    ScopeType = 'STORE'
                    AND EmirateId IS NULL
                    AND StoreId IS NOT NULL
               )
        )
);
GO


/* =========================================================
   Prevent duplicate active ALL scope per user
   ========================================================= */

CREATE UNIQUE INDEX UX_UserDataScope_ActiveAll
ON security.UserDataScope (UserId)
WHERE
    ScopeType = 'ALL'
    AND IsActive = 1;
GO


/* =========================================================
   Prevent duplicate active Emirate scope
   ========================================================= */

CREATE UNIQUE INDEX UX_UserDataScope_ActiveEmirate
ON security.UserDataScope
(
    UserId,
    EmirateId
)
WHERE
    ScopeType = 'EMIRATE'
    AND IsActive = 1;
GO


/* =========================================================
   Prevent duplicate active Store scope
   ========================================================= */

CREATE UNIQUE INDEX UX_UserDataScope_ActiveStore
ON security.UserDataScope
(
    UserId,
    StoreId
)
WHERE
    ScopeType = 'STORE'
    AND IsActive = 1;
GO


/* =========================================================
   7. Audit Log
   ========================================================= */

CREATE TABLE security.AuditLog
(
    AuditLogId       BIGINT IDENTITY(1,1) NOT NULL,

    UserId           INT NULL,

    EventType        VARCHAR(50) NOT NULL,

    EventDateTime    DATETIME2(3) NOT NULL
        CONSTRAINT DF_AuditLog_EventDateTime
        DEFAULT SYSUTCDATETIME(),

    Success          BIT NOT NULL,

    IPAddress        VARCHAR(45) NULL,

    Details          NVARCHAR(2000) NULL,

    CONSTRAINT PK_AuditLog
        PRIMARY KEY (AuditLogId),

    CONSTRAINT FK_AuditLog_User
        FOREIGN KEY (UserId)
        REFERENCES security.AppUser (UserId)
);
GO