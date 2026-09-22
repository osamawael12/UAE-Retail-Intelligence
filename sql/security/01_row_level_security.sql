/*
============================================================
 UAE Retail Intelligence Platform
 SQL Server Row-Level Security

 Security source:
 SESSION_CONTEXT(N'UserId')

 Supported scopes:
 ALL
 EMIRATE
 STORE

 Default behavior:
 No valid UserId context = no protected business rows.

 Note:
 Database owners / highly privileged SQL principals should not
 be treated as the final application execution identity.
============================================================
*/

USE UAERetailAnalytics;
GO

SET NOCOUNT ON;
GO


/* =========================================================
   Drop policy first if this script is intentionally rerun.
   Predicate functions cannot be altered while actively bound.
   ========================================================= */

IF EXISTS
(
    SELECT 1
    FROM sys.security_policies
    WHERE
        name = N'BusinessDataSecurityPolicy'
        AND schema_id = SCHEMA_ID(
            N'security'
        )
)
BEGIN
    DROP SECURITY POLICY
        security.BusinessDataSecurityPolicy;
END;
GO


DROP FUNCTION IF EXISTS
    security.fn_UserCanAccessStore;
GO

DROP FUNCTION IF EXISTS
    security.fn_UserCanAccessOrder;
GO

DROP FUNCTION IF EXISTS
    security.fn_UserCanAccessOrderItem;
GO

DROP FUNCTION IF EXISTS
    security.fn_UserCanAccessReturn;
GO


/* =========================================================
   1. STORE ACCESS PREDICATE
   ========================================================= */

CREATE FUNCTION security.fn_UserCanAccessStore
(
    @StoreId INT
)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
(
    SELECT
        1 AS AccessGranted

    WHERE EXISTS
    (
        SELECT 1

        FROM security.UserDataScope AS uds

        WHERE
            uds.UserId
            =
            TRY_CONVERT(
                INT,
                SESSION_CONTEXT(
                    N'UserId'
                )
            )

            AND uds.IsActive = 1

            AND
            (
                /* Company-wide */
                uds.ScopeType = 'ALL'

                OR

                /* Specific Store */
                (
                    uds.ScopeType = 'STORE'
                    AND uds.StoreId
                        = @StoreId
                )

                OR

                /* All stores inside assigned Emirate */
                (
                    uds.ScopeType = 'EMIRATE'

                    AND EXISTS
                    (
                        SELECT 1

                        FROM core.Store AS st

                        INNER JOIN core.City AS ci
                            ON st.CityId
                               = ci.CityId

                        WHERE
                            st.StoreId
                            = @StoreId

                            AND ci.EmirateId
                            = uds.EmirateId
                    )
                )
            )
    )
);
GO


/* =========================================================
   2. ORDER ACCESS PREDICATE
   Used for tables that only contain OrderId.
   ========================================================= */

CREATE FUNCTION security.fn_UserCanAccessOrder
(
    @OrderId BIGINT
)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
(
    SELECT
        1 AS AccessGranted

    WHERE EXISTS
    (
        SELECT 1

        FROM sales.SalesOrder AS o

        WHERE
            o.OrderId = @OrderId

            AND EXISTS
            (
                SELECT 1

                FROM security.UserDataScope AS uds

                WHERE
                    uds.UserId
                    =
                    TRY_CONVERT(
                        INT,
                        SESSION_CONTEXT(
                            N'UserId'
                        )
                    )

                    AND uds.IsActive = 1

                    AND
                    (
                        uds.ScopeType = 'ALL'

                        OR

                        (
                            uds.ScopeType = 'STORE'
                            AND uds.StoreId
                                = o.StoreId
                        )

                        OR

                        (
                            uds.ScopeType = 'EMIRATE'

                            AND EXISTS
                            (
                                SELECT 1

                                FROM core.Store AS st

                                INNER JOIN core.City AS ci
                                    ON st.CityId
                                       = ci.CityId

                                WHERE
                                    st.StoreId
                                    = o.StoreId

                                    AND ci.EmirateId
                                    = uds.EmirateId
                            )
                        )
                    )
            )
    )
);
GO


/* =========================================================
   3. ORDER ITEM ACCESS PREDICATE
   ========================================================= */

CREATE FUNCTION security.fn_UserCanAccessOrderItem
(
    @OrderItemId BIGINT
)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
(
    SELECT
        1 AS AccessGranted

    WHERE EXISTS
    (
        SELECT 1

        FROM sales.SalesOrderItem AS oi

        INNER JOIN sales.SalesOrder AS o
            ON oi.OrderId
               = o.OrderId

        WHERE
            oi.OrderItemId
            = @OrderItemId

            AND EXISTS
            (
                SELECT 1

                FROM security.UserDataScope AS uds

                WHERE
                    uds.UserId
                    =
                    TRY_CONVERT(
                        INT,
                        SESSION_CONTEXT(
                            N'UserId'
                        )
                    )

                    AND uds.IsActive = 1

                    AND
                    (
                        uds.ScopeType = 'ALL'

                        OR

                        (
                            uds.ScopeType = 'STORE'
                            AND uds.StoreId
                                = o.StoreId
                        )

                        OR

                        (
                            uds.ScopeType = 'EMIRATE'

                            AND EXISTS
                            (
                                SELECT 1

                                FROM core.Store AS st

                                INNER JOIN core.City AS ci
                                    ON st.CityId
                                       = ci.CityId

                                WHERE
                                    st.StoreId
                                    = o.StoreId

                                    AND ci.EmirateId
                                    = uds.EmirateId
                            )
                        )
                    )
            )
    )
);
GO


/* =========================================================
   4. RETURN ACCESS PREDICATE
   Used by Refund.
   ========================================================= */

CREATE FUNCTION security.fn_UserCanAccessReturn
(
    @ReturnId BIGINT
)
RETURNS TABLE
WITH SCHEMABINDING
AS
RETURN
(
    SELECT
        1 AS AccessGranted

    WHERE EXISTS
    (
        SELECT 1

        FROM sales.[Return] AS r

        WHERE
            r.ReturnId = @ReturnId

            AND EXISTS
            (
                SELECT 1

                FROM security.UserDataScope AS uds

                WHERE
                    uds.UserId
                    =
                    TRY_CONVERT(
                        INT,
                        SESSION_CONTEXT(
                            N'UserId'
                        )
                    )

                    AND uds.IsActive = 1

                    AND
                    (
                        uds.ScopeType = 'ALL'

                        OR

                        (
                            uds.ScopeType = 'STORE'
                            AND uds.StoreId
                                = r.StoreId
                        )

                        OR

                        (
                            uds.ScopeType = 'EMIRATE'

                            AND EXISTS
                            (
                                SELECT 1

                                FROM core.Store AS st

                                INNER JOIN core.City AS ci
                                    ON st.CityId
                                       = ci.CityId

                                WHERE
                                    st.StoreId
                                    = r.StoreId

                                    AND ci.EmirateId
                                    = uds.EmirateId
                            )
                        )
                    )
            )
    )
);
GO


/* =========================================================
   5. SECURITY POLICY

   Protect tables with direct StoreId using store predicate.

   Protect child transaction tables using relational predicates.
   ========================================================= */

CREATE SECURITY POLICY
    security.BusinessDataSecurityPolicy


/* Store master */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON core.Store,


/* Employees belong to Store.
   NULL StoreId rows are intentionally not visible through
   this store-scoped policy. */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON core.Employee,


/* Orders */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON sales.SalesOrder,


/* Order Items */
ADD FILTER PREDICATE
    security.fn_UserCanAccessOrder(
        OrderId
    )
ON sales.SalesOrderItem,


/* Payments */
ADD FILTER PREDICATE
    security.fn_UserCanAccessOrder(
        OrderId
    )
ON sales.OrderPayment,


/* Returns */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON sales.[Return],


/* Return Items */
ADD FILTER PREDICATE
    security.fn_UserCanAccessOrderItem(
        OrderItemId
    )
ON sales.ReturnItem,


/* Refunds */
ADD FILTER PREDICATE
    security.fn_UserCanAccessReturn(
        ReturnId
    )
ON sales.Refund,


/* Inventory snapshot */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON inventory.StoreProductInventory,


/* Inventory movements */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON inventory.InventoryMovement,


/* Targets */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON sales.StoreMonthlyTarget,


/* Promotion Store bridge */
ADD FILTER PREDICATE
    security.fn_UserCanAccessStore(
        StoreId
    )
ON sales.PromotionStore


WITH
(
    STATE = ON
);
GO


/* =========================================================
   VALIDATE POLICY
   ========================================================= */

SELECT
    p.name AS PolicyName,
    p.is_enabled AS IsEnabled,

    OBJECT_SCHEMA_NAME(
        sp.target_object_id
    ) AS TargetSchema,

    OBJECT_NAME(
        sp.target_object_id
    ) AS TargetTable,

    sp.predicate_type_desc
        AS PredicateType

FROM sys.security_policies p

INNER JOIN sys.security_predicates sp
    ON p.object_id
       = sp.object_id

WHERE
    p.name
    = N'BusinessDataSecurityPolicy'

ORDER BY
    TargetSchema,
    TargetTable;
GO