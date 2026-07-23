/* Activity log foundation for issue #21. Safe to run repeatedly. */

IF OBJECT_ID(N'dbo.activity_log', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.activity_log (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_activity_log PRIMARY KEY,
        entity_type NVARCHAR(100) NOT NULL,
        entity_id INT NULL,
        action NVARCHAR(50) NOT NULL,
        old_value NVARCHAR(MAX) NULL,
        new_value NVARCHAR(MAX) NULL,
        actor_user_id INT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_activity_log_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_activity_log_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_activity_log_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_activity_log_actor FOREIGN KEY (actor_user_id) REFERENCES dbo.users(id),
        CONSTRAINT FK_activity_log_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_activity_log_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_activity_log_recent' AND object_id = OBJECT_ID(N'dbo.activity_log'))
    CREATE INDEX IX_activity_log_recent ON dbo.activity_log (created_at DESC, id DESC) WHERE is_active = 1;
GO
