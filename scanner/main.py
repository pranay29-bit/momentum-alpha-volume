def run() -> None:
    today_str = datetime.today().strftime("%Y%m%d")
    date_display = datetime.today().strftime("%Y-%m-%d")

    # ── Output directory ─────────────────────────────────────────────────────
    out_dir = Path(DOCS_DIR) / date_display
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Output directory: %s", out_dir)

    # ── 1. Symbols ──────────────────────────────────────────────────────────
    symbols = load_symbols()

    logger.info("Loaded %d symbols.", len(symbols))

    # ── 2. Download + indicators ────────────────────────────────────────────
    df = download_all(symbols)

    if df.empty:
        logger.error("No valid data collected. Aborting.")
        sys.exit(1)

    logger.info("Collected rows for %d symbols.", len(df))

    # ── 3. RS percentile + condition flags ─────────────────────────────────
    df["rs_percentile"] = (
        df["12m_return_pct"].rank(pct=True) * 100.0
    )

    df["cond8_rs_at_least_70"] = (
        df["rs_percentile"] >= 70.0
    )

    df["all_conditions_met"] = (
        df[COND_COLS].all(axis=1)
    )

    # ── 4. Save full results ────────────────────────────────────────────────
    full_path = out_dir / f"full_results_{today_str}.csv"

    df.to_csv(full_path, index=False)

    logger.info("Full results → %s", full_path)

    # ── 5. Passing stocks ───────────────────────────────────────────────────
    passing = df[df["all_conditions_met"]].copy()

    if not passing.empty:

        passing = enrich_with_market_caps(passing)

        logger.info(
            "Fetching quarterly result dates for passing stocks..."
        )

        passing["result_date"] = (
            passing["symbol"].apply(get_result_date)
        )

        print(
            passing[
                ["symbol", "result_date"]
            ].head(20)
        )

    passing_path = (
        out_dir / f"passing_stocks_{today_str}.csv"
    )

    passing.to_csv(passing_path, index=False)

    logger.info(
        "Passing stocks (%d) → %s",
        len(passing),
        passing_path,
    )

    # ── 6. Passing + above EMA10 ────────────────────────────────────────────
    if (
        not passing.empty
        and "cond9_price_above_ema10" in passing.columns
    ):

        passing_ema10 = (
            passing[
                passing["cond9_price_above_ema10"]
            ]
            .sort_values(
                "rs_percentile",
                ascending=False,
            )
            .copy()
        )

    else:
        passing_ema10 = pd.DataFrame()

    if not passing_ema10.empty:

        logger.info(
            "Fetching quarterly result dates for elite stocks..."
        )

        passing_ema10["result_date"] = (
            passing_ema10["symbol"].apply(
                get_result_date
            )
        )

        print(
            passing_ema10[
                ["symbol", "result_date"]
            ].head(20)
        )

    ema10_path = (
        out_dir / f"passing_ema10_{today_str}.csv"
    )

    passing_ema10.to_csv(
        ema10_path,
        index=False,
    )

    logger.info(
        "Passing+EMA10 stocks (%d) → %s",
        len(passing_ema10),
        ema10_path,
    )

    # ── 7. Fresh crossovers ─────────────────────────────────────────────────
    fresh = df[df["fresh_ma12_cross_today"]].copy()

    fresh_path = (
        out_dir / f"fresh_crossovers_{today_str}.csv"
    )

    fresh.to_csv(fresh_path, index=False)

    logger.info(
        "Fresh crossovers (%d) → %s",
        len(fresh),
        fresh_path,
    )

    # ── 8. Volume Action ────────────────────────────────────────────────────
    volume_action = (
        df[df["volume_signal"] == "ppv"].copy()
    )

    if not volume_action.empty:

        logger.info(
            "Fetching quarterly result dates for volume action stocks..."
        )

        volume_action["result_date"] = (
            volume_action["symbol"].apply(
                get_result_date
            )
        )

        print(
            volume_action[
                ["symbol", "result_date"]
            ].head(20)
        )

    volume_action_path = (
        out_dir / f"volume_action_{today_str}.csv"
    )

    volume_action.to_csv(
        volume_action_path,
        index=False,
    )

    logger.info(
        "Volume action (%d) → %s",
        len(volume_action),
        volume_action_path,
    )

    # ── 9. HTML Dashboards ──────────────────────────────────────────────────
    if not passing.empty:

        build_passing_dashboard(
            passing,
            out_dir / f"dashboard_{today_str}.html",
            today_str,
        )

    if not passing_ema10.empty:

        history: list[dict] = []

        docs_root = Path(DOCS_DIR)

        for dated_dir in sorted(docs_root.iterdir()):

            if not dated_dir.is_dir():
                continue

            dir_slug = dated_dir.name.replace("-", "")

            if (
                not dir_slug.isdigit()
                or len(dir_slug) != 8
            ):
                continue

            if dir_slug == today_str:
                continue

            csv_path = (
                dated_dir
                / f"passing_ema10_{dir_slug}.csv"
            )

            if not csv_path.exists():
                continue

            try:

                hist_df = pd.read_csv(csv_path)

                mc = (
                    float(
                        hist_df[
                            "total_market_cap_cr"
                        ].dropna().sum()
                    )
                    if "total_market_cap_cr"
                    in hist_df.columns
                    else 0.0
                )

                tv = (
                    float(
                        hist_df[
                            "traded_value_cr"
                        ].dropna().sum()
                    )
                    if "traded_value_cr"
                    in hist_df.columns
                    else 0.0
                )

                history.append(
                    {
                        "date": dir_slug,
                        "count": len(hist_df),
                        "market_cap_cr": mc,
                        "traded_value_cr": tv,
                    }
                )

            except Exception as exc:

                logger.warning(
                    "Could not read history from %s: %s",
                    csv_path,
                    exc,
                )

        build_passing_ema10_dashboard(
            passing_ema10,
            out_dir / f"elite_dashboard_{today_str}.html",
            today_str,
            history=history,
        )

    if not volume_action.empty:

        build_volume_action_dashboard(
            volume_action,
            out_dir / f"volume_dashboard_{today_str}.html",
            today_str,
        )

    # ── 10. Update index ────────────────────────────────────────────────────
    _update_index(
        today_str,
        out_dir,
        len(passing),
        len(passing_ema10),
    )

    # ── Summary ──────────────────────────────────────────────────────────────
    logger.info("── SUMMARY ──────────────────────────────")

    logger.info(
        "  Total scanned   : %d",
        len(df),
    )

    logger.info(
        "  Passing (8 cond): %d",
        len(passing),
    )

    logger.info(
        "  Passing + EMA10 : %d",
        len(passing_ema10),
    )

    logger.info(
        "  Fresh crossovers: %d",
        len(fresh),
    )

    logger.info(
        "  Volume action   : %d",
        len(volume_action),
    )
