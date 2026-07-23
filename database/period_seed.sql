/* Standard fixed periods used by the allocation form. Safe to run repeatedly. */

INSERT INTO dbo.periods (period_number, period_label)
SELECT source.period_number, source.period_label
FROM (VALUES
    (1, N'Period 1'),
    (2, N'Period 2'),
    (3, N'Period 3'),
    (4, N'Period 4'),
    (5, N'Period 5'),
    (6, N'Period 6'),
    (7, N'Period 7'),
    (8, N'Period 8')
) AS source(period_number, period_label)
WHERE NOT EXISTS (
    SELECT 1 FROM dbo.periods AS existing
    WHERE existing.period_number = source.period_number
);
GO
