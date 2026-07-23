/* Room building field required by issue #8. Safe to run repeatedly. */

IF COL_LENGTH(N'dbo.rooms', N'building') IS NULL
    ALTER TABLE dbo.rooms ADD building NVARCHAR(150) NOT NULL CONSTRAINT DF_rooms_building DEFAULT N'Main Building' WITH VALUES;
GO
