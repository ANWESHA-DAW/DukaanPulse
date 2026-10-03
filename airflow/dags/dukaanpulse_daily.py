# Optional Airflow DAG.
# Copy/use this DAG after installing Apache Airflow in an Airflow environment.
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="dukaanpulse_daily_etl",
    start_date=datetime(2026, 1, 1),
    schedule="0 23 * * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["dukaanpulse", "etl"],
) as dag:

    run_pipeline = BashOperator(
        task_id="run_dukaanpulse_pipeline",
        bash_command="cd /opt/dukaanpulse && python -m src.pipeline",
    )

    run_pipeline
