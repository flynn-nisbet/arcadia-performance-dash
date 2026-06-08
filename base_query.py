from databricks.connect import DatabricksSession
from datetime import date
import pandas as pd
import os
import glob
import io

def get_data():
    spark = DatabricksSession.builder \
        .host("redventures-rv-energy-prod-production-9xwiei.cloud.databricks.com") \
        .serverless(True) \
        .getOrCreate()

    query = """
      WITH params AS (
        SELECT
          TIMESTAMP '2026-01-12 00:00:00' AS from_ts_est,
          DATE      '2026-01-12'          AS from_date_est
      ),

      acf_base AS (
        SELECT
          acf.call_id,
          acf.call_datetime_est,
          DATE(acf.call_datetime_est)          AS call_date_est,
          acf.call_date,
          acf.agent_name,
          acf.employeeid,
          acf.call_direction,
          acf.center_location,
          acf.ib_contact_calls,
          acf.credit_calls_ind,
          acf.credit_calls_Ind,
          acf.passed_credit_call_ind,
          acf.credit_sold_calls_ind,
          acf.order_count,
          acf.allconnect_transition_ind,
          acf.conversion_exclude_ind,
          acf.talk_time_seconds,
          acf.total_points,
          acf.marketing_code_id,
          acf.disposition,
          acf.pc,
          acf.hire_date,
          ROW_NUMBER() OVER (
            PARTITION BY acf.call_id
            ORDER BY acf.call_datetime_est DESC NULLS LAST
          ) AS rn
        FROM energy_prod.energy.v_agent_calls acf
        WHERE acf.call_datetime_est     >= (SELECT from_ts_est FROM params)
          AND acf.conversion_exclude_ind IS NULL
      ),

      acf_dedup AS (
        SELECT * FROM acf_base WHERE rn = 1
      ),

      brand_test AS (
        SELECT
          call_context_call_id AS call_id,
          CAST(parse_json(attributes) AS STRUCT<brandTest: STRING>).brandTest AS brand_test
        FROM lakehouse_production.energy.event_twilio_generic_flow_event
        QUALIFY ROW_NUMBER() OVER (
          PARTITION BY call_context_call_id
          ORDER BY 1
        ) = 1
      ),

      ecp_module AS (
        SELECT
          callId AS call_id,
          CASE
            WHEN moduleNodeName = 'is_ecp'            THEN 'clicked_ecp'
            WHEN moduleNodeName = 'mover_or_switcher' THEN 'clicked_mover_or_switcher'
          END AS ecp_module_selection
        FROM (
          SELECT
            callId,
            moduleNodeName,
            ROW_NUMBER() OVER (
              PARTITION BY callId
              ORDER BY _date ASC
            ) AS rn
          FROM lakehouse_production.energy.event_arcadia_elementviewed
          WHERE _date >= (SELECT from_date_est FROM params)
            AND moduleNodeName IN ('is_ecp', 'mover_or_switcher')
        ) ranked
        WHERE rn = 1
      ),

      short_call_anchor AS (
        SELECT
          short.call_id                                                          AS short_call_id,
          MAX(long.call_datetime_est)                                            AS anchor_call_datetime_est
        FROM acf_dedup short
        JOIN acf_dedup long
          ON  long.employeeid          = short.employeeid
          AND long.talk_time_seconds   > 30
          AND long.call_datetime_est  <= short.call_datetime_est
        WHERE short.talk_time_seconds <= 30
        GROUP BY short.call_id
      ),

      short_call_anchor_id AS (
        SELECT
          sca.short_call_id,
          ad.call_id AS anchor_call_id
        FROM short_call_anchor sca
        JOIN acf_dedup ad
          ON  ad.call_datetime_est = sca.anchor_call_datetime_est
          AND ad.talk_time_seconds > 30
        JOIN acf_dedup short_call
          ON  short_call.call_id    = sca.short_call_id
          AND short_call.employeeid = ad.employeeid
      ),

      b_member AS (
        SELECT DISTINCT call_id
        FROM energy_prod.energy.rpt_arcadia_frontend
        WHERE session_start_date >= (SELECT from_date_est FROM params)
      ),

      orders_by_call AS (
        SELECT
          o.call_id,
          COUNT(DISTINCT o.order_id)                                                       AS orders,
          SUM(COALESCE(o.gcv_v2, 0))                                                      AS gcv_fo,
          MAX(o.product_name)                                                              AS product_name,
          MAX(o.partner_name)                                                              AS partner_name
        FROM energy_prod.energy.v_orders o
        INNER JOIN acf_dedup acf ON acf.call_id = o.call_id
        WHERE DATE(
                COALESCE(
                  CAST(o.order_date_est AS TIMESTAMP),
                  from_utc_timestamp(CAST(o.order_date_utc AS TIMESTAMP), 'America/New_York')
                )
              ) >= (SELECT from_date_est FROM params)
        GROUP BY 1
      ),

      fmp_eligible AS (
        SELECT DISTINCT v.call_id
        FROM energy_prod.data_science.fmp_base_query fmp
        JOIN energy_prod.energy.v_calls v
          ON v.web_session_id = fmp.webcontext_session_id
        WHERE fmp.experience       = 'FMP_LP'
          AND fmp.top_match_name_1 IS NOT NULL
          AND v.call_id            IS NOT NULL
      )

      SELECT
        acf.call_id,
        acf.call_datetime_est                                             AS call_time_est,
        acf.call_date_est,
        CAST(DATE_TRUNC('week',  acf.call_date_est) AS DATE)             AS week_start,
        CAST(DATE_TRUNC('month', acf.call_date_est) AS DATE)             AS month_start,
        acf.pc,

        CASE ((dayofweek(acf.call_date_est) + 5) % 7) + 1
          WHEN 1 THEN 'Monday'
          WHEN 2 THEN 'Tuesday'
          WHEN 3 THEN 'Wednesday'
          WHEN 4 THEN 'Thursday'
          WHEN 5 THEN 'Friday'
          WHEN 6 THEN 'Saturday'
          WHEN 7 THEN 'Sunday'
        END                                                               AS day_of_week,

        CASE
          WHEN DATEDIFF(day, acf.hire_date, acf.call_date_est) <= 30  THEN '0-30 day Tenure'
          WHEN DATEDIFF(day, acf.hire_date, acf.call_date_est) <= 60  THEN '31-60 day Tenure'
          WHEN DATEDIFF(day, acf.hire_date, acf.call_date_est) <= 90  THEN '61-90 day Tenure'
          WHEN DATEDIFF(day, acf.hire_date, acf.call_date_est) <= 120 THEN '91-120 day Tenure'
          WHEN DATEDIFF(day, acf.hire_date, acf.call_date_est) <= 150 THEN '121-150 day Tenure'
          ELSE 'Vet'
        END                                                               AS tenure_bucket,

        COALESCE(mcdim.marketing_bucket, 'Other')                        AS marketing_bucket,

        CASE
          WHEN cf.permalease_call_ind = 1
              AND cf.remote_number_call NOT IN (
                '8772917225','8554026764','8444474658','8558385573','8774259108','8442933169',
                '8669765629','8445386748','8442383028','8338550434','8552098145','8776798574',
                '8448515993','8777419736','8553253608','8338524238','8555968675','8556198095',
                '8775083197','8664875294','8777193624','8776827574','8553818886','8334310102',
                '8665099704','8774259108','8669765629'
              )
          THEN 'Permalease'
          ELSE 'Site Session'
        END                                                               AS call_type,

        COALESCE(acf.call_direction, 'UNKNOWN')                          AS call_direction,

        CASE
          WHEN acf.talk_time_seconds <= 30 THEN
            CASE WHEN b_anchor.call_id IS NOT NULL THEN 'Arcadia' ELSE 'Atomizer' END
          ELSE
            CASE WHEN b.call_id IS NOT NULL THEN 'Arcadia' ELSE 'Atomizer' END
        END                                                               AS membership,

        COALESCE(acf.agent_name, a.employee_name)                        AS agent_name,
        COALESCE(acf.center_location, 'UNKNOWN')                         AS center_location,

        CASE
          WHEN UPPER(ms.movingSwitchingExtracted) = 'MOVING'    THEN 'mover'
          WHEN UPPER(ms.movingSwitchingExtracted) = 'SWITCHING' THEN 'switcher'
          ELSE 'Uncollected'
        END                                                               AS moverSwitcher,

        COALESCE(acf.ib_contact_calls, 0)                                AS ib_contact_calls,
        COALESCE(acf.credit_calls_ind, acf.credit_calls_Ind, 0)          AS credit_calls_flag,

        CASE WHEN acf.passed_credit_call_ind > 0
                  AND COALESCE(acf.credit_calls_ind, acf.credit_calls_Ind, 0) > 0
            THEN 1 ELSE 0 END                                           AS passed_credit_call_flag,

        CASE WHEN COALESCE(acf.credit_calls_ind, acf.credit_calls_Ind, 0) = 1
                  AND acf.passed_credit_call_ind = 0
            THEN 1 ELSE 0 END                                           AS failed_credit_call_flag,

        CASE WHEN acf.credit_sold_calls_ind > 0
                  AND acf.passed_credit_call_ind > 0
            THEN 1 ELSE 0 END                                           AS passed_credit_sale_flag,

        CASE WHEN acf.credit_sold_calls_ind > 0
                  AND acf.passed_credit_call_ind = 0
                  AND COALESCE(obc.orders, 0) > 0
            THEN 1 ELSE 0 END                                           AS failed_credit_sale_flag,

        COALESCE(obc.orders, 0)                                          AS orders,
        COALESCE(obc.gcv_fo, 0)                                          AS gcv_fo,
        COALESCE(obc.gcv_fo, 0)                                          AS total_revenue,
        obc.product_name                                                  AS product_name,
        obc.partner_name                                                  AS partner_name,

        CASE
          WHEN obc.partner_name IN ('TXU Energy', 'TriEagle Energy', 'Octopus Energy') THEN 1
          ELSE 0
        END                                                               AS top_product_mix,

        acf.talk_time_seconds / 60.0                                     AS talk_time_minutes,
        CASE WHEN COALESCE(obc.orders, 0) > 0 THEN acf.talk_time_seconds / 60.0 END AS talk_time_minutes_sold,
        CASE WHEN COALESCE(obc.orders, 0) = 0 THEN acf.talk_time_seconds / 60.0 END AS talk_time_minutes_unsold,

        CASE
          WHEN acf.call_date_est <  DATE '2023-06-01' AND COALESCE(acf.total_points, 0) >= 28 THEN 1
          WHEN acf.call_date_est >= DATE '2023-06-01' AND COALESCE(acf.total_points, 0) >= 25 THEN 1
          ELSE 0
        END                                                               AS tpsales_flag,

        bt.brand_test                                                     AS brand_test,
        ms.siteExperienceHint                                             AS site_experience_hint,
        em.ecp_module_selection                                           AS ecp_module_selection,
        CASE WHEN fe.call_id IS NOT NULL THEN 1 ELSE 0 END                AS fmp_hint_eligible

      FROM acf_dedup acf
      LEFT JOIN b_member b
        ON b.call_id = acf.call_id
      LEFT JOIN short_call_anchor_id scai
        ON scai.short_call_id = acf.call_id
      LEFT JOIN b_member b_anchor
        ON b_anchor.call_id = scai.anchor_call_id
      LEFT JOIN orders_by_call obc
        ON obc.call_id = acf.call_id
      LEFT JOIN energy_prod.energy.v_agents a
        ON acf.employeeid = a.employeeid
      LEFT JOIN energy_prod.fivetran_salesops.marketingbucket_dim mcdim
        ON mcdim.mcid = COALESCE(acf.marketing_code_id, 0)
      LEFT JOIN energy_prod.energy.v_calls cf
        ON cf.call_id = acf.call_id
      LEFT JOIN ai_products_prod.energy.compass_call_fct ms
        ON acf.call_id = ms.call_id
      LEFT JOIN brand_test bt
        ON bt.call_id = acf.call_id
      LEFT JOIN ecp_module em
        ON em.call_id = acf.call_id
      LEFT JOIN fmp_eligible fe
        ON fe.call_id = acf.call_id

      WHERE COALESCE(acf.agent_name, a.employee_name) NOT IN (
              'Harry Barcia', 'Diane Perez', 'Chris Curry', 'David Loughry'
            )
        AND COALESCE(acf.center_location, '') != 'Barranquilla'

      ORDER BY acf.call_datetime_est DESC
    """

    return spark.sql(query).toPandas()


def deploy_app():
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.apps import AppDeployment

    w = WorkspaceClient()
    print("Deploying arcadia-performance-dash...")
    deployment = w.apps.deploy(
        app_name="arcadia-performance",
        app_deployment=AppDeployment(
            source_code_path="/Workspace/Users/fnisbet@redventures.com/arcadia-performance-dash"
        )
    )
    print(f"Deploy complete: {deployment}")


if __name__ == "__main__":
    df = get_data()

    OUTPUT_DIR = "/Workspace/Users/fnisbet@redventures.com/arcadia-performance-dash/data/"

    for f in glob.glob(OUTPUT_DIR + "agent_calls_*.csv"):
        os.remove(f)
        print(f"Removed {f}")

    TARGET_BYTES = 8 * 1024 * 1024
    sample_size  = min(1000, len(df))
    sample_bytes = len(df.head(sample_size).to_csv(index=False).encode("utf-8"))
    bytes_per_row = sample_bytes / sample_size
    rows_per_chunk = max(1, int(TARGET_BYTES / bytes_per_row))

    print(f"Estimated {bytes_per_row:.0f} bytes/row → {rows_per_chunk:,} rows per chunk")

    total_rows = len(df)
    part = 1

    for start in range(0, total_rows, rows_per_chunk):
        chunk = df.iloc[start : start + rows_per_chunk]
        filename = f"agent_calls_part{part}.csv"
        path = OUTPUT_DIR + filename
        chunk.to_csv(path, index=False)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"Saved {len(chunk):,} rows to {filename} ({size_mb:.1f} MB)")
        part += 1

    deploy_app()