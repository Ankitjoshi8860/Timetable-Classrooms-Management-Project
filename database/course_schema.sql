/* Course fields required by issue #7. Safe to run repeatedly. */

IF COL_LENGTH(N'dbo.courses', N'department') IS NULL
    ALTER TABLE dbo.courses ADD department NVARCHAR(150) NOT NULL CONSTRAINT DF_courses_department DEFAULT N'General' WITH VALUES;
GO

IF COL_LENGTH(N'dbo.courses', N'credit_hours') IS NULL
    ALTER TABLE dbo.courses ADD credit_hours TINYINT NOT NULL CONSTRAINT DF_courses_credit_hours DEFAULT 3 WITH VALUES;
GO

IF NOT EXISTS (SELECT 1 FROM sys.check_constraints WHERE name = N'CK_courses_credit_hours' AND parent_object_id = OBJECT_ID(N'dbo.courses'))
    ALTER TABLE dbo.courses ADD CONSTRAINT CK_courses_credit_hours CHECK (credit_hours BETWEEN 1 AND 12);
GO
