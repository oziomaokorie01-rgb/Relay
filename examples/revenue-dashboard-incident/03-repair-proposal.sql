-- Relay generated repair proposal
-- Incident: Revenue dashboard dropped by 35%

with normalized_orders as (

    select
        *,
        try_cast(customer_id as integer) as normalized_customer_id

    from raw.raw_orders

),

valid_orders as (

    select *
    from normalized_orders
    where normalized_customer_id is not null

),

invalid_customer_ids as (

    select
        customer_id
    from normalized_orders
    where customer_id is not null
      and normalized_customer_id is null

)

select
    *
from valid_orders;