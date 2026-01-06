"""
ETL Pipeline Template

A production-ready ETL template with:
- Error handling and retries
- Watermark-based incremental loading
- Idempotent operations
- Structured logging
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd
from sqlalchemy import create_engine, text
from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Base ETL pipeline with watermark support."""

    def __init__(
        self,
        source_engine: Engine,
        target_engine: Engine,
        pipeline_name: str,
    ) -> None:
        """Initialize the pipeline.

        Args:
            source_engine: SQLAlchemy engine for source database.
            target_engine: SQLAlchemy engine for target database.
            pipeline_name: Unique name for watermark tracking.
        """
        self.source_engine = source_engine
        self.target_engine = target_engine
        self.pipeline_name = pipeline_name

    def run(self) -> int:
        """Execute the full ETL pipeline.

        Returns:
            Number of records processed.
        """
        logger.info("Starting pipeline: %s", self.pipeline_name)

        # Get watermark
        watermark = self._get_watermark()
        logger.info("Using watermark: %s", watermark)

        # Extract
        df = self._extract(watermark)
        if df.empty:
            logger.info("No new records to process")
            return 0

        logger.info("Extracted %d records", len(df))

        # Transform
        df = self._transform(df)

        # Load (idempotent)
        self._load(df)

        # Update watermark
        new_watermark = df["updated_at"].max()
        self._update_watermark(new_watermark, len(df))

        logger.info("Pipeline complete: %d records processed", len(df))
        return len(df)

    def _get_watermark(self) -> datetime:
        """Get the last processed watermark."""
        with self.target_engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT last_watermark
                    FROM pipeline_watermarks
                    WHERE pipeline_name = :name
                """),
                {"name": self.pipeline_name}
            ).fetchone()
            return result[0] if result else datetime.min

    def _update_watermark(self, watermark: datetime, count: int) -> None:
        """Update the watermark after successful processing."""
        with self.target_engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO pipeline_watermarks
                        (pipeline_name, last_watermark, last_run_at, records_processed)
                    VALUES (:name, :wm, :now, :count)
                    ON CONFLICT (pipeline_name) DO UPDATE SET
                        last_watermark = :wm,
                        last_run_at = :now,
                        records_processed = :count
                """),
                {
                    "name": self.pipeline_name,
                    "wm": watermark,
                    "now": datetime.utcnow(),
                    "count": count,
                }
            )
            conn.commit()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    def _extract(self, watermark: datetime) -> pd.DataFrame:
        """Extract records newer than watermark.

        Args:
            watermark: Only extract records updated after this timestamp.

        Returns:
            DataFrame with extracted records.
        """
        query = """
            SELECT *
            FROM source_table
            WHERE updated_at > :watermark
            ORDER BY updated_at
        """
        return pd.read_sql(query, self.source_engine, params={"watermark": watermark})

    def _transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply transformations to the data.

        Override this method for custom transformations.

        Args:
            df: Input DataFrame.

        Returns:
            Transformed DataFrame.
        """
        # Example transformations:
        # - Standardize column names
        df.columns = df.columns.str.lower().str.replace(" ", "_")

        # - Add processing metadata
        df["_loaded_at"] = datetime.utcnow()

        return df

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    def _load(self, df: pd.DataFrame) -> None:
        """Load data to target (idempotent via staging + merge).

        Args:
            df: DataFrame to load.
        """
        # Load to staging table
        df.to_sql(
            "staging_table",
            self.target_engine,
            if_exists="replace",
            index=False,
        )

        # Merge to target (idempotent)
        with self.target_engine.connect() as conn:
            conn.execute(
                text("""
                    MERGE INTO target_table AS t
                    USING staging_table AS s
                    ON t.id = s.id
                    WHEN MATCHED THEN
                        UPDATE SET
                            t.column1 = s.column1,
                            t.column2 = s.column2,
                            t.updated_at = s.updated_at,
                            t._loaded_at = s._loaded_at
                    WHEN NOT MATCHED THEN
                        INSERT (id, column1, column2, updated_at, _loaded_at)
                        VALUES (s.id, s.column1, s.column2, s.updated_at, s._loaded_at)
                """)
            )
            conn.commit()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    source = create_engine("postgresql://user:pass@source-host/db")
    target = create_engine("postgresql://user:pass@target-host/db")

    pipeline = ETLPipeline(
        source_engine=source,
        target_engine=target,
        pipeline_name="orders_etl",
    )

    records_processed = pipeline.run()
    print(f"Processed {records_processed} records")
