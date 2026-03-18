with tx as (
  select * from {{ ref('transactions_cleaned') }}
  where direction = 'expense'
),

agg as (
  select
    user_id,
    date_trunc('month', booking_date) as month,
    count(*) as n_transactions,
    sum(abs_amount) as spend_total,
    avg(abs_amount) as spend_avg,
    approx_quantile(abs_amount, 0.5) as spend_median
  from tx
  group by 1, 2
)

select * from agg
