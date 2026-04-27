-- ============================================================================
-- 모바일게임 시장 변화 조사 (Mobile Game Market Change Investigation) - SQL Queries
-- ============================================================================
-- 데이터 소스 : AI_mobilegame DB (PostgreSQL)
-- 핵심 테이블 : dw_app_monthly (월·OS·국가·앱 grain, USD/KRW 정규화 완료)
-- 기준일      : 2026-04-27
--
-- 보고서      : index.html (KR/JP/US 시장 + 3국 공통 트렌드 인사이트)
-- 분석 범위   : 2022-01 ~ 2026-03 (51개월)
-- 비교 기준   : 25년 전(22~24, 36개월) vs 후(25~26.1Q, 15개월)
-- 매출        : revenue_krw_100 (USD/0.7 × 연도별 환율, 100% 보정)
-- TOP100 필터 : in_revenue_top100_unified_os = TRUE (iOS+Android 합산)
-- 퍼블리셔 분류: NEXON→KR / FUNFLY→중화권 강제 + publisher_country
--               (KR / JP / 중화권 / 북미 / 기타)
-- 장르 분류   : COALESCE(lv2_genre, genre) 기준 lv2 우선
-- ============================================================================


-- ============================================================================
-- Q1. 퍼블리셔 그룹별 연도별 월평균 매출 (KR/JP/US)
-- ============================================================================
-- 사용처: 시장 매출 추이 (Step 1) · 점유율 (Step 2) · 시장 요약 박스
-- 결과: 국가 × 연도 × 퍼블 그룹별 월평균 매출 (억원, 100% 보정)
WITH base AS (
    SELECT country, unified_app_id, date,
           SUM(revenue_krw_100) AS rev,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US')
      AND in_revenue_top100_unified_os = TRUE
      AND date BETWEEN '2022-01-01' AND '2026-03-01'
    GROUP BY country, unified_app_id, date
),
classified AS (
    SELECT country, date, rev,
        CASE
            WHEN publisher_name ILIKE '%NEXON%' THEN 'KR'
            WHEN publisher_name ILIKE '%FUNFLY%' THEN '중화권'
            WHEN publisher_country = 'South Korea' THEN 'KR'
            WHEN publisher_country = 'Japan' THEN 'JP'
            WHEN publisher_country IN ('China','Hong Kong','Taiwan','Macao') THEN '중화권'
            WHEN publisher_country IN ('US','USA','United States','Canada') THEN '북미'
            ELSE '기타'
        END AS pub_group
    FROM base
)
SELECT country,
       EXTRACT(YEAR FROM date)::int AS yr,
       pub_group,
       ROUND(SUM(rev) / COUNT(DISTINCT date) / 1e8, 0) AS monthly_avg_yiek
FROM classified
GROUP BY country, EXTRACT(YEAR FROM date)::int, pub_group
ORDER BY country, yr, pub_group;


-- ============================================================================
-- Q2. 25년 전후(Pre/Post) 퍼블 그룹별 매출 변화
-- ============================================================================
-- 사용처: Step 1 헤드라인 ("US +17% / JP -4% / KR +13%") · 시장 요약 박스
-- Pre = 22~24 (36개월), Post = 25~26.1Q (15개월)
WITH base AS (
    SELECT country, unified_app_id, date,
           SUM(revenue_krw_100) AS rev,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US')
      AND in_revenue_top100_unified_os = TRUE
    GROUP BY country, unified_app_id, date
),
classified AS (
    SELECT country, date, rev,
        CASE
            WHEN publisher_name ILIKE '%NEXON%' THEN 'KR'
            WHEN publisher_name ILIKE '%FUNFLY%' THEN '중화권'
            WHEN publisher_country = 'South Korea' THEN 'KR'
            WHEN publisher_country = 'Japan' THEN 'JP'
            WHEN publisher_country IN ('China','Hong Kong','Taiwan','Macao') THEN '중화권'
            WHEN publisher_country IN ('US','USA','United States','Canada') THEN '북미'
            ELSE '기타'
        END AS pub_group
    FROM base
),
periods AS (
    SELECT country, pub_group,
        CASE WHEN date < '2025-01-01' THEN 'pre' ELSE 'post' END AS period,
        SUM(rev) AS total_rev,
        COUNT(DISTINCT date) AS months
    FROM classified
    WHERE date BETWEEN '2022-01-01' AND '2026-03-01'
    GROUP BY country, pub_group, CASE WHEN date < '2025-01-01' THEN 'pre' ELSE 'post' END
)
SELECT country, pub_group, period, months,
       ROUND(total_rev / months / 1e8, 0) AS monthly_avg_yiek
FROM periods
ORDER BY country, pub_group, period;


-- ============================================================================
-- Q3. 장르별(lv2) 연도별 월평균 매출 (3국)
-- ============================================================================
-- 사용처: Step 5 (장르별 매출 변화) · 공통 Step 2 (장르 추이)
-- lv2_genre 우선 (없으면 genre 사용)
WITH base AS (
    SELECT country, unified_app_id, date,
           SUM(revenue_krw_100) AS rev,
           MAX(COALESCE(lv2_genre, genre)) AS lv2
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US')
      AND in_revenue_top100_unified_os = TRUE
      AND date BETWEEN '2022-01-01' AND '2026-03-01'
    GROUP BY country, unified_app_id, date
),
genre_keyed AS (
    SELECT country, date, rev,
        CASE
            WHEN lv2 ILIKE '%Casino%' OR lv2 ILIKE '%PvE%' THEN 'Casino(PvE)'
            WHEN lv2 = '머지' OR lv2 = 'Merge' THEN '머지'
            WHEN lv2 = '방치형' OR lv2 = 'Idle' THEN '방치형'
            WHEN lv2 ILIKE '%PvP%' OR lv2 ILIKE '%웹보드%' THEN '웹보드(PvP)'
            ELSE COALESCE(lv2, '기타')
        END AS genre_key
    FROM base
)
SELECT country, EXTRACT(YEAR FROM date)::int AS yr, genre_key,
       ROUND(SUM(rev) / COUNT(DISTINCT date) / 1e8, 0) AS monthly_avg_yiek
FROM genre_keyed
GROUP BY country, EXTRACT(YEAR FROM date)::int, genre_key
ORDER BY country, yr, monthly_avg_yiek DESC;


-- ============================================================================
-- Q4. 신흥 세부 장르 비중 — Strategy / 머지 / 방치형 (3국)
-- ============================================================================
-- 사용처: 공통 Step 3 (Strategy·머지 3국 동반 상승, 방치형 KR 독주)
WITH base AS (
    SELECT country, unified_app_id, date,
           SUM(revenue_krw_100) AS rev,
           MAX(COALESCE(lv2_genre, genre)) AS lv2
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US')
      AND in_revenue_top100_unified_os = TRUE
    GROUP BY country, unified_app_id, date
),
classified AS (
    SELECT country, date, rev,
        CASE
            WHEN lv2 = 'Strategy' THEN 'Strategy'
            WHEN lv2 = '머지' THEN '머지'
            WHEN lv2 = '방치형' THEN '방치형'
            ELSE 'OTHER'
        END AS genre_key
    FROM base
    WHERE date BETWEEN '2022-01-01' AND '2026-03-01'
),
yearly AS (
    SELECT country, EXTRACT(YEAR FROM date)::int AS yr,
           SUM(CASE WHEN genre_key='Strategy' THEN rev ELSE 0 END) AS strategy_rev,
           SUM(CASE WHEN genre_key='머지'    THEN rev ELSE 0 END) AS merge_rev,
           SUM(CASE WHEN genre_key='방치형'   THEN rev ELSE 0 END) AS idle_rev,
           SUM(rev) AS total_rev
    FROM classified
    GROUP BY country, EXTRACT(YEAR FROM date)::int
)
SELECT country, yr,
       ROUND((strategy_rev / NULLIF(total_rev, 0) * 100)::numeric, 1) AS strategy_pct,
       ROUND((merge_rev    / NULLIF(total_rev, 0) * 100)::numeric, 1) AS merge_pct,
       ROUND((idle_rev     / NULLIF(total_rev, 0) * 100)::numeric, 1) AS idle_pct
FROM yearly
ORDER BY country, yr;


-- ============================================================================
-- Q5. 중화권 퍼블 점유율 추이 (3국 공통)
-- ============================================================================
-- 사용처: 공통 Step 1 (중화권 점유율 상승은 3국 공통 현상)
WITH base AS (
    SELECT country, unified_app_id, date,
           SUM(revenue_krw_100) AS rev,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US')
      AND in_revenue_top100_unified_os = TRUE
    GROUP BY country, unified_app_id, date
),
classified AS (
    SELECT country, date, rev,
        CASE
            WHEN publisher_name ILIKE '%FUNFLY%' THEN 'CN'
            WHEN publisher_country IN ('China','Hong Kong','Taiwan','Macao') THEN 'CN'
            ELSE 'OTHER'
        END AS pub_group
    FROM base
    WHERE date BETWEEN '2022-01-01' AND '2026-03-01'
),
yearly AS (
    SELECT country, EXTRACT(YEAR FROM date)::int AS yr,
           SUM(CASE WHEN pub_group='CN' THEN rev ELSE 0 END) AS cn_rev,
           SUM(rev) AS total_rev
    FROM classified
    GROUP BY country, EXTRACT(YEAR FROM date)::int
)
SELECT country, yr,
       ROUND((cn_rev / NULLIF(total_rev, 0) * 100)::numeric, 1) AS cn_share_pct
FROM yearly
ORDER BY country, yr;


-- ============================================================================
-- Q6. 신규 진입 게임 수 (퍼블 그룹별, 연도별)
-- ============================================================================
-- 사용처: Step 7 (신규 진입 추이)
-- 신규 진입 정의: 22~26.1Q 중 unified_app_id 기준 첫 등장월 (1월 제외)
WITH base AS (
    SELECT unified_app_id, country, date,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US') AND in_revenue_top100_unified_os = TRUE
    GROUP BY unified_app_id, country, date
),
first_entry AS (
    SELECT country, unified_app_id,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country,
           MIN(date) AS first_month
    FROM base
    GROUP BY country, unified_app_id
),
classified AS (
    SELECT fe.country,
        EXTRACT(YEAR FROM first_month)::int AS yr,
        EXTRACT(MONTH FROM first_month)::int AS mo,
        CASE
            WHEN publisher_name ILIKE '%NEXON%' THEN 'KR'
            WHEN publisher_name ILIKE '%FUNFLY%' THEN '중화권'
            WHEN publisher_country = 'South Korea' THEN 'KR'
            WHEN publisher_country = 'Japan' THEN 'JP'
            WHEN publisher_country IN ('China','Hong Kong','Taiwan','Macao') THEN '중화권'
            WHEN publisher_country IN ('US','USA','United States','Canada') THEN '북미'
            ELSE '기타'
        END AS pub_group
    FROM first_entry fe
)
SELECT country, yr, pub_group, COUNT(*) AS new_entries
FROM classified
WHERE mo > 1                  -- 1월 제외 (해당 연도에 새로 진입한 것만)
  AND yr BETWEEN 2022 AND 2026
GROUP BY country, yr, pub_group
ORDER BY country, yr, pub_group;


-- ============================================================================
-- Q7. 3개월 생존율 — 퍼블 그룹별 (KR/JP/US Step 8)
-- ============================================================================
-- 사용처: Step 8 (신규 진입 3개월 생존율)
-- 생존 정의: 첫 진입월 + 3개월 시점에 TOP100 잔류 여부
WITH base AS (
    SELECT unified_app_id, country, date,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US') AND in_revenue_top100_unified_os = TRUE
    GROUP BY unified_app_id, country, date
),
first_entry AS (
    SELECT country, unified_app_id,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country,
           MIN(date) AS first_month
    FROM base
    GROUP BY country, unified_app_id
),
classified AS (
    SELECT fe.*,
        EXTRACT(YEAR FROM first_month)::int AS yr,
        EXTRACT(MONTH FROM first_month)::int AS mo,
        CASE
            WHEN publisher_name ILIKE '%NEXON%' THEN 'KR'
            WHEN publisher_name ILIKE '%FUNFLY%' THEN '중화권'
            WHEN publisher_country = 'South Korea' THEN 'KR'
            WHEN publisher_country = 'Japan' THEN 'JP'
            WHEN publisher_country IN ('China','Hong Kong','Taiwan','Macao') THEN '중화권'
            WHEN publisher_country IN ('US','USA','United States','Canada') THEN '북미'
            ELSE '기타'
        END AS pub_group
    FROM first_entry fe
),
survival AS (
    SELECT c.*,
        EXISTS(
            SELECT 1 FROM dw_app_monthly d2
            WHERE d2.unified_app_id = c.unified_app_id
              AND d2.country = c.country
              AND d2.in_revenue_top100_unified_os = TRUE
              AND d2.date = (c.first_month + INTERVAL '3 months')::date
        ) AS survived
    FROM classified c
    WHERE mo > 1 AND yr BETWEEN 2022 AND 2025
)
SELECT country, yr, pub_group,
       COUNT(*) AS total,
       SUM(CASE WHEN survived THEN 1 ELSE 0 END) AS survived,
       ROUND((SUM(CASE WHEN survived THEN 1 ELSE 0 END)::numeric
              / NULLIF(COUNT(*), 0) * 100), 1) AS survival_pct
FROM survival
GROUP BY country, yr, pub_group
ORDER BY country, yr, pub_group;


-- ============================================================================
-- Q8. 3개월 생존율 — 퍼블 그룹 × lv2 장르 버킷 (Local 2-3, 2-4)
-- ============================================================================
-- 사용처: KR/JP/US 신규진입게임분석 탭의 2-3 (중화권), 2-4 (자국/기타) 섹션
-- lv2 분류 기준 (Role Playing/Strategy/방치형/머지/Puzzle/기타 등)
WITH base AS (
    SELECT unified_app_id, country, date,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country,
           MAX(COALESCE(lv2_genre, genre)) AS lv2
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US') AND in_revenue_top100_unified_os = TRUE
    GROUP BY unified_app_id, country, date
),
first_entry AS (
    SELECT country, unified_app_id,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country,
           MAX(lv2) AS lv2,
           MIN(date) AS first_month
    FROM base
    GROUP BY country, unified_app_id
),
classified AS (
    SELECT fe.*,
        EXTRACT(YEAR FROM first_month)::int AS yr,
        EXTRACT(MONTH FROM first_month)::int AS mo,
        CASE
            WHEN publisher_name ILIKE '%NEXON%' THEN 'KR'
            WHEN publisher_name ILIKE '%FUNFLY%' THEN '중화권'
            WHEN publisher_country = 'South Korea' THEN 'KR'
            WHEN publisher_country = 'Japan' THEN 'JP'
            WHEN publisher_country IN ('China','Hong Kong','Taiwan','Macao') THEN '중화권'
            WHEN publisher_country IN ('US','USA','United States','Canada') THEN '북미'
            ELSE '기타'
        END AS pub_group,
        CASE
            WHEN lv2 ILIKE '%MMORPG%' THEN 'MMORPG'
            WHEN lv2 = '비MMORPG' THEN '비MMORPG'
            WHEN lv2 = 'Role Playing' THEN 'Role Playing'
            WHEN lv2 = '방치형' THEN '방치형'
            WHEN lv2 = '머지'   THEN '머지'
            WHEN lv2 = 'Strategy' THEN 'Strategy'
            WHEN lv2 = 'Puzzle' THEN 'Puzzle'
            WHEN lv2 IN ('Simulation','Casual') THEN 'Simulation/Casual'
            ELSE '기타'
        END AS genre_bucket
    FROM first_entry fe
),
survival AS (
    SELECT c.*,
        EXISTS(
            SELECT 1 FROM dw_app_monthly d2
            WHERE d2.unified_app_id = c.unified_app_id
              AND d2.country = c.country
              AND d2.in_revenue_top100_unified_os = TRUE
              AND d2.date = (c.first_month + INTERVAL '3 months')::date
        ) AS survived
    FROM classified c
    WHERE mo > 1 AND yr BETWEEN 2022 AND 2025
)
SELECT country, yr, pub_group, genre_bucket,
       COUNT(*) AS total,
       SUM(CASE WHEN survived THEN 1 ELSE 0 END) AS survived
FROM survival
GROUP BY country, yr, pub_group, genre_bucket
ORDER BY country, yr, pub_group, genre_bucket;


-- ============================================================================
-- Q9. MAU × ARPMAU 추이 (Step 6)
-- ============================================================================
-- 사용처: 시장 매출 +X% 성장 — 단가/유저 분해 (단가 주도 vs 유저 풀 주도)
WITH base AS (
    SELECT country, unified_app_id, date,
           SUM(revenue_krw_100) AS rev,
           SUM(mau) AS mau_sum,
           SUM(units) AS units_sum
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US') AND in_revenue_top100_unified_os = TRUE
      AND date BETWEEN '2022-01-01' AND '2026-03-01'
    GROUP BY country, unified_app_id, date
),
monthly AS (
    SELECT country, date,
           SUM(rev) AS rev, SUM(mau_sum) AS mau, SUM(units_sum) AS units
    FROM base
    GROUP BY country, date
)
SELECT country, EXTRACT(YEAR FROM date)::int AS yr,
       ROUND(AVG(rev) / 1e8, 0) AS rev_yiek,
       ROUND(AVG(mau) / 1e4, 0) AS mau_man,
       ROUND(AVG(units) / 1e4, 0) AS units_man,
       ROUND(AVG(rev) / NULLIF(AVG(mau), 0), 0) AS arpmau
FROM monthly
GROUP BY country, EXTRACT(YEAR FROM date)::int
ORDER BY country, yr;


-- ============================================================================
-- Q10. 순위별 월평균 매출 (1/10/20/50/100위, 3국, 5개 연도)
-- ============================================================================
-- 사용처: 공통 Step 4 (순위별 매출 — 3국 시장 규모·분포 비교)
-- Rank 결정: 연 누적 매출(yr_rev) 기준
-- 표시값   : yr_rev / active_months (해당 연도 활동월 수로 나눈 월평균)
WITH annual_app AS (
    SELECT country, EXTRACT(YEAR FROM date)::int AS yr, unified_app_id,
           SUM(revenue_krw_100) AS yr_rev,
           COUNT(DISTINCT date) AS active_months
    FROM dw_app_monthly
    WHERE country IN ('KR','JP','US') AND in_revenue_top100_unified_os = TRUE
      AND date BETWEEN '2022-01-01' AND '2026-03-01'
    GROUP BY country, EXTRACT(YEAR FROM date)::int, unified_app_id
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY country, yr ORDER BY yr_rev DESC) AS rnk
    FROM annual_app
)
SELECT country, yr, rnk,
       ROUND((yr_rev / active_months) / 1e8, 0) AS rev_yiek
FROM ranked
WHERE rnk IN (1, 10, 20, 50, 100)
ORDER BY rnk, country, yr;


-- ============================================================================
-- Q11. 북미 자국 분해 — 북미 TOP5 vs 기타 (US 전용, Step 3·4)
-- ============================================================================
-- 사용처: US Step 3 (북미 자국 감소), Step 4 (북미 TOP5 양극화 — Scopely vs Roblox)
-- 북미 TOP5 = Scopely · Roblox · Product Madness · Niantic · Activision
WITH base AS (
    SELECT unified_app_id, date,
           SUM(revenue_krw_100) AS rev,
           MAX(publisher_name) AS publisher_name,
           MAX(publisher_country) AS publisher_country
    FROM dw_app_monthly
    WHERE country='US' AND in_revenue_top100_unified_os = TRUE
      AND date BETWEEN '2022-01-01' AND '2026-03-01'
    GROUP BY unified_app_id, date
),
labeled AS (
    SELECT date, rev, publisher_name,
        CASE
            WHEN publisher_country IN ('US','USA','United States','Canada') AND (
                publisher_name ILIKE '%scopely%' OR
                publisher_name ILIKE '%roblox%' OR
                publisher_name ILIKE '%product madness%' OR
                publisher_name ILIKE '%niantic%' OR
                publisher_name ILIKE '%activision%'
            ) THEN '북미 TOP5'
            WHEN publisher_country IN ('US','USA','United States','Canada') THEN '북미 기타'
            ELSE '해외'
        END AS bucket
    FROM base
)
SELECT EXTRACT(YEAR FROM date)::int AS yr, bucket,
       ROUND(SUM(rev) / COUNT(DISTINCT date) / 1e8, 0) AS monthly_avg_yiek
FROM labeled
GROUP BY EXTRACT(YEAR FROM date)::int, bucket
ORDER BY yr, bucket;


-- ============================================================================
-- 환율 참고 (revenue_krw_100 산식)
-- ============================================================================
-- revenue_krw_100 = revenue_usd / 0.7 × 연도별 한국은행 환율
--   2022: 1,292 / 2023: 1,307 / 2024: 1,364 / 2025: 1,422 / 2026: 1,409
-- (센서타워 매출 = 실제의 약 70% 추정치 → 100% 보정)
