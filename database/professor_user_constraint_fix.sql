/*
    Fix nullable professor user links.

    SQL Server treats NULL as a duplicate value for a regular unique
    constraint. Professor logins are optional, so multiple professors may have
    user_id = NULL; linked users must still be unique.
*/

IF EXISTS (
    SELECT 1
    FROM sys.key_constraints
    WHERE name = N'UQ_professors_user_id'
      AND parent_object_id = OBJECT_ID(N'dbo.professors')
)
BEGIN
    ALTER TABLE dbo.professors DROP CONSTRAINT UQ_professors_user_id;
END;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'UX_professors_user_id_nonnull'
      AND object_id = OBJECT_ID(N'dbo.professors')
)
BEGIN
    CREATE UNIQUE INDEX UX_professors_user_id_nonnull
        ON dbo.professors (user_id)
        WHERE user_id IS NOT NULL;
END;
GO
