/*
    Timetable Classroom Management - core schema
    SQL Server migration for issue #3.

    The migration is safe to run more than once. It creates the core entities,
    fixed periods, and the child rows used to represent a lecture's recurring
    weekdays without duplicating the lecture for every calendar date.
*/

IF OBJECT_ID(N'dbo.users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.users (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_users PRIMARY KEY,
        username NVARCHAR(100) NOT NULL CONSTRAINT UQ_users_username UNIQUE,
        email NVARCHAR(255) NOT NULL CONSTRAINT UQ_users_email UNIQUE,
        password_hash NVARCHAR(255) NOT NULL,
        role NVARCHAR(20) NOT NULL CONSTRAINT DF_users_role DEFAULT N'scheduler',
        is_active BIT NOT NULL CONSTRAINT DF_users_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_users_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_users_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_users_role CHECK (role IN (N'scheduler', N'professor')),
        CONSTRAINT FK_users_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_users_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.professors', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.professors (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_professors PRIMARY KEY,
        user_id INT NULL,
        employee_code NVARCHAR(50) NOT NULL CONSTRAINT UQ_professors_employee_code UNIQUE,
        first_name NVARCHAR(100) NOT NULL,
        last_name NVARCHAR(100) NOT NULL,
        email NVARCHAR(255) NULL,
        is_active BIT NOT NULL CONSTRAINT DF_professors_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_professors_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_professors_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_professors_user FOREIGN KEY (user_id) REFERENCES dbo.users(id),
        CONSTRAINT FK_professors_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_professors_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.courses', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.courses (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_courses PRIMARY KEY,
        course_code NVARCHAR(50) NOT NULL CONSTRAINT UQ_courses_course_code UNIQUE,
        course_name NVARCHAR(200) NOT NULL,
        description NVARCHAR(1000) NULL,
        department NVARCHAR(150) NOT NULL CONSTRAINT DF_courses_department DEFAULT N'General',
        credit_hours TINYINT NOT NULL CONSTRAINT DF_courses_credit_hours DEFAULT 3,
        is_active BIT NOT NULL CONSTRAINT DF_courses_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_courses_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_courses_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_courses_credit_hours CHECK (credit_hours BETWEEN 1 AND 12),
        CONSTRAINT FK_courses_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_courses_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.rooms', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.rooms (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_rooms PRIMARY KEY,
        room_code NVARCHAR(50) NOT NULL CONSTRAINT UQ_rooms_room_code UNIQUE,
        room_name NVARCHAR(200) NOT NULL,
        building NVARCHAR(150) NOT NULL CONSTRAINT DF_rooms_building DEFAULT N'Main Building',
        is_active BIT NOT NULL CONSTRAINT DF_rooms_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_rooms_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_rooms_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_rooms_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_rooms_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.terms', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.terms (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_terms PRIMARY KEY,
        term_name NVARCHAR(100) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_terms_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_terms_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_terms_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_terms_date_range CHECK (end_date >= start_date),
        CONSTRAINT UQ_terms_name_dates UNIQUE (term_name, start_date),
        CONSTRAINT FK_terms_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_terms_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.periods', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.periods (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_periods PRIMARY KEY,
        period_number TINYINT NOT NULL CONSTRAINT UQ_periods_period_number UNIQUE,
        period_label NVARCHAR(50) NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_periods_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_periods_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_periods_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT CK_periods_period_number CHECK (period_number > 0),
        CONSTRAINT FK_periods_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_periods_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.lectures', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lectures (
        id INT IDENTITY(1, 1) NOT NULL CONSTRAINT PK_lectures PRIMARY KEY,
        course_id INT NOT NULL,
        professor_id INT NOT NULL,
        room_id INT NOT NULL,
        term_id INT NOT NULL,
        period_id INT NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_lectures_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_lectures_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_lectures_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_lectures_course FOREIGN KEY (course_id) REFERENCES dbo.courses(id),
        CONSTRAINT FK_lectures_professor FOREIGN KEY (professor_id) REFERENCES dbo.professors(id),
        CONSTRAINT FK_lectures_room FOREIGN KEY (room_id) REFERENCES dbo.rooms(id),
        CONSTRAINT FK_lectures_term FOREIGN KEY (term_id) REFERENCES dbo.terms(id),
        CONSTRAINT FK_lectures_period FOREIGN KEY (period_id) REFERENCES dbo.periods(id),
        CONSTRAINT FK_lectures_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_lectures_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF OBJECT_ID(N'dbo.lecture_days', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.lecture_days (
        lecture_id INT NOT NULL,
        day_of_week TINYINT NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_lecture_days_is_active DEFAULT 1,
        created_by INT NULL,
        updated_by INT NULL,
        created_at DATETIME2(3) NOT NULL CONSTRAINT DF_lecture_days_created_at DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(3) NOT NULL CONSTRAINT DF_lecture_days_updated_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT PK_lecture_days PRIMARY KEY (lecture_id, day_of_week),
        CONSTRAINT CK_lecture_days_day_of_week CHECK (day_of_week BETWEEN 1 AND 7),
        CONSTRAINT FK_lecture_days_lecture FOREIGN KEY (lecture_id) REFERENCES dbo.lectures(id),
        CONSTRAINT FK_lecture_days_created_by FOREIGN KEY (created_by) REFERENCES dbo.users(id),
        CONSTRAINT FK_lecture_days_updated_by FOREIGN KEY (updated_by) REFERENCES dbo.users(id)
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_lectures_term_room' AND object_id = OBJECT_ID(N'dbo.lectures'))
    CREATE INDEX IX_lectures_term_room ON dbo.lectures (term_id, room_id, period_id) WHERE is_active = 1;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'UX_professors_user_id_nonnull' AND object_id = OBJECT_ID(N'dbo.professors'))
    CREATE UNIQUE INDEX UX_professors_user_id_nonnull ON dbo.professors (user_id) WHERE user_id IS NOT NULL;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_lectures_term_professor' AND object_id = OBJECT_ID(N'dbo.lectures'))
    CREATE INDEX IX_lectures_term_professor ON dbo.lectures (term_id, professor_id, period_id) WHERE is_active = 1;

IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = N'IX_lecture_days_day' AND object_id = OBJECT_ID(N'dbo.lecture_days'))
    CREATE INDEX IX_lecture_days_day ON dbo.lecture_days (day_of_week, lecture_id) WHERE is_active = 1;
GO
