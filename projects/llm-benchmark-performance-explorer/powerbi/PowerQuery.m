let
    Source = Csv.Document(
        File.Contents("C:\PATH\TO\benchmark-analytics\data\benchmark_scores.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types = Table.TransformColumnTypes(Headers, {
        {"model_id", type text}, {"model_name", type text},
        {"organization", type text}, {"release_date", type date},
        {"benchmark", type text}, {"benchmark_type", type text},
        {"score", type number}, {"max_score", type number}, {"score_pct", type number}
    }),
    ValidRows = Table.SelectRows(Types, each [max_score] > 0 and [score] >= 0 and [score] <= [max_score]),
    AddedScorePct = Table.AddColumn(ValidRows, "score_pct_calculated", each [score] / [max_score] * 100, type number),
    AddedReleaseYear = Table.AddColumn(AddedScorePct, "release_year", each Date.Year([release_date]), Int64.Type)
in
    AddedReleaseYear

