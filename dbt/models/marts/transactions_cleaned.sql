with stg as (
  select * from {{ ref('stg_raw_transactions') }}
),

enriched as (
  select
    transaction_id,
    user_id,
    booking_date,
    amount,
    currency,
    label_raw,
    label_norm,
    merchant_guess as merchant,
    case when amount < 0 then 'expense' else 'income' end as direction,
    abs(amount) as abs_amount,
    category_true
  from stg
)

select * from enriched
