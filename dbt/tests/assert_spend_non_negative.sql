select *
from {{ ref('user_spending_summary') }}
where spend_total < 0
