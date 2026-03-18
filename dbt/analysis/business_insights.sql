-- Quelques requêtes “analytics” typiques (exécutables dans DuckDB).
-- En prod: materializations / BI tool (Looker/QuickSight) + gouvernance.

-- 1) Top merchants par volume de dépenses (30 derniers jours)
with tx as (
  select *
  from transactions_cleaned
  where direction = 'expense'
    and booking_date >= current_date - interval '30 day'
)
select
  merchant,
  count(*) as n,
  sum(abs_amount) as spend_total,
  avg(abs_amount) as avg_ticket
from tx
group by 1
order by spend_total desc
limit 20;

-- 2) Distribution catégories “ground truth” (qualité dataset)
select
  category_true,
  count(*) as n,
  round(count(*) * 100.0 / sum(count(*)) over (), 2) as pct
from transactions_cleaned
group by 1
order by n desc;

-- 3) Dépenses mensuelles (trend) + MoM
with m as (
  select
    month,
    sum(spend_total) as spend_total
  from user_spending_summary
  group by 1
),
with_mom as (
  select
    month,
    spend_total,
    lag(spend_total) over (order by month) as prev_total
  from m
)
select
  month,
  spend_total,
  prev_total,
  case when prev_total is null then null else (spend_total - prev_total) / prev_total end as mom_growth
from with_mom
order by month;
