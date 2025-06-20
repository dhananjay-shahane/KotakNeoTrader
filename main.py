from app import app  # noqa: F401
# Import the populate function after app is ready
    try:
        from populate_etf_quotes import populate_etf_signals_with_csv_data
        signals_count = populate_etf_signals_with_csv_data()
        logging.info(f"✅ Populated {signals_count} ETF signals with CMP data")
    except ImportError as e:
        logging.error(f"❌ Could not import populate function: {e}")
    except Exception as e:
        logging.error(f"❌ Error populating ETF signals: {e}")