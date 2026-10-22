# Analysis Notes

This file records validated results, business interpretations, limitations, and follow-up questions from each analysis step.

## 01 - Market Overview by Customer State

**Business question:** Which customer states contribute the most delivered orders and product revenue?

**SQL file:** `sql/01_market_overview.sql`

**Key results:**

- Sao Paulo (SP): 40,501 orders and R$5,067,633.16 in product revenue
- Rio de Janeiro (RJ): 12,350 orders and R$1,759,651.13 in product revenue
- Minas Gerais (MG): 11,354 orders and R$1,552,481.83 in product revenue
- SP had an average order value of R$125.12, compared with R$142.48 in RJ and R$136.73 in MG

**Interpretation:** SP was Olist's largest customer market by a wide margin. Its lead was driven by order volume rather than a high average order value.

**Limitation:** Revenue is calculated from item prices for delivered orders only. It excludes freight charges and should not be interpreted as profit.

**Next question:** Is Olist overly dependent on SP, and which smaller states combine meaningful order volume with stronger average order value?

## 02 - Explore the Orders Table

**SQL file:** `sql/02_explore_orders.sql`

**Purpose:** Preview the orders table. Each row is one order, with its status and its purchase, approval, carrier handoff, delivery, and estimated-delivery timestamps.

## 03 - Order Status Distribution

**Business question:** What is the current distribution of order status?

**Key results:**

- Total orders: 99,441
- Delivered orders: 96,478
- Canceled orders: 625
- Unavailable orders: 609
- Invoiced: 314
- Processing: 301
- Other: 7

**Interpretation:** About 97.02% of orders were delivered.

## 04 - Cancellation Rate

**Business question:** What percentage of orders were canceled?

**Key result:** The overall cancellation rate was 0.63% (625 of 99,441 orders).

**Interpretation:** Cancellation was uncommon at the marketplace level. Later analysis should test whether cancellation risk varies by time, location, seller, or product category.

**Limitation:** This metric only counts orders labeled `canceled`; it does not include `unavailable` orders.

## 05 - Dataset Date Range

**Business question:** What time period does the orders dataset cover?

**SQL file:** `sql/05_date_range.sql`

**Key results:**

- First recorded purchase: September 4, 2016
- Last recorded purchase: October 17, 2018
- Total orders: 99,441

**Next question:** Which months contain enough orders to form a reliable and comparable analysis period?

## 06 - Monthly Order Coverage

**Business question:** Which months contain enough orders to support reliable trend analysis?

**SQL file:** `sql/06_monthly_orders.sql`

**Key results:**

- The 2016 data is not analyzable: September had 4 orders, October had 324, November had none, and December had 1
- Monthly volume increased from 800 orders in January 2017 to 7,544 in November 2017
- Monthly volume remained above 6,000 from January through August 2018
- September and October 2018 contained only 16 and 4 orders

**Interpretation:** January 2017 through August 2018 is the primary analysis window. November 2017 had unusually high volume and may reflect a seasonal event that requires further investigation.

**Limitation:** January 2017 had fewer orders than later months and may still reflect an early growth period. Monthly order counts alone is weak for the analysis

## 07 - Delivered Order Trend

**Business question:** How did monthly delivered-order volume change during the primary analysis window?

**SQL file:** `sql/07_delivered_order_trend.sql`

**Key results:**

- Delivered orders increased from 750 in January 2017 to 4,478 in October 2017
- Volume peaked at 7,289 delivered orders in November 2017 before declining to 5,513 in December
- Monthly delivered orders ranged from 6,099 to 7,069 between January and August 2018

**Interpretation:** Olist expanded rapidly during 2017 and experienced an unusually strong November. In 2018, order volume remained much higher than in early 2017 but was broadly stable rather than consistently growing month over month.

**Limitation:** The November peak may be seasonal. Month-to-month comparisons do not isolate seasonality, so comparable months across years should be evaluated before describing the change as sustained growth.

**Next question:** How much did delivered-order volume grow from January-August 2017 to the same period in 2018?

## 08 - Year-over-Year Delivered Orders

**Business question:** How much did delivered-order volume change from January-August 2017 to the same period in 2018?

**SQL file:** `sql/08_yoy_delivered_orders.sql`

**Key results:**

- January-August 2017: 21,998 delivered orders
- January-August 2018: 52,783 delivered orders
- Year-over-year increase: 30,785 delivered orders, or approximately 139.94%

**Interpretation:** Delivered-order volume in the first eight months of 2018 was about 2.4 times the comparable 2017 volume, indicating substantial marketplace expansion.

**Limitation:** Higher delivered-order volume does not show whether revenue, average order value, profitability, or customer experience improved at the same rate.

**Next question:** Did product revenue grow alongside delivered-order volume?

## 09 - Year-over-Year Product Revenue

**Business question:** Did product revenue grow alongside delivered-order volume from January-August 2017 to the same period in 2018?

**SQL file:** `sql/09_yoy_revenue.sql`

**Key results:**

- Product revenue increased from R$2,993,456.13 in 2017 to R$7,218,125.12 in 2018, an increase of approximately 141.13%
- Delivered orders increased from 21,998 to 52,783, an increase of approximately 139.94%
- Average order value increased slightly from R$136.08 to R$136.75

**Interpretation:** Revenue grew at approximately the same rate as delivered orders. Olist's marketplace expansion was therefore driven primarily by higher order volume rather than customers spending materially more per order.

**Limitation:** Product revenue excludes freight and does not represent profit. The analysis also does not show which product categories, customer markets, or sellers generated the growth.

**Next question:** Which product categories contributed most to marketplace revenue and growth?

## 10 - Explore the Products Table

**Business question:** What product information is available for category-level analysis?

**SQL file:** `sql/10_explore_products.sql`

**Key results:**

- Each product is identified by `product_id`
- `product_category_name` stores category names in Portuguese
- The table also contains product listing attributes, photo count, weight, and package dimensions
- Category names can be translated by joining the product category translation table

**Interpretation:** Product revenue can be assigned to categories by joining `order_items` to `products` through `product_id`. English category names require one additional join to the translation table.

**Limitation:** A 10-row preview cannot establish category coverage or the extent of missing product attributes.

**Next question:** How does the category translation table map Portuguese category names to English names?

## 11 - Explore Category Translations

**Business question:** How can Portuguese product category names be converted into English labels for reporting?

**SQL file:** `sql/11_explore_category_translation.sql`

**Key result:** The translation table maps `product_category_name` in Portuguese to `product_category_name_english`, such as `beleza_saude` to `health_beauty`.

**Interpretation:** The English category field should be used in final tables, charts, and GitHub documentation so that the analysis is accessible to recruiters and business stakeholders.

**Limitation:** The preview does not prove that every Portuguese product category has an English translation.

**Next question:** Which English product categories generated the most delivered product revenue?

## 12 - Product Category Revenue

**Business question:** Which product categories generated the most delivered product revenue during the primary analysis window?

**SQL file:** `sql/12_category_revenue.sql`

**Key results:**

- `health_beauty` ranked first with R$1,229,557.50 in product revenue from 8,610 orders
- `watches_gifts` ranked second with R$1,163,465.91 from 5,491 orders and had the highest average order value among the top categories at R$211.89
- `bed_bath_table` had the largest order count among the top categories at 9,267, but a lower average order value of R$110.39
- `cool_stuff` generated R$609,158.00 from only 3,552 orders, supported by a relatively high average order value of R$171.50

**Interpretation:** Category revenue was driven by different combinations of volume and order value. `health_beauty` and `bed_bath_table` were volume-led categories, while `watches_gifts` and `cool_stuff` generated more revenue per related order.

**Limitation:** Product revenue excludes freight and profit. An order containing multiple categories is counted once in each relevant category, so category order counts should not be summed to estimate marketplace orders.

**Next question:** Which leading product categories grew the most between January-August 2017 and the same period in 2018?

## 13 - Leading Category Growth

**Business question:** Which leading product categories grew the most from January-August 2017 to the same period in 2018?

**SQL file:** `sql/13_category_yoy.sql`

**Key results:**

- `watches_gifts` had the fastest order growth at approximately 336.53% and revenue growth of 241.98%
- `health_beauty` delivered strong, balanced growth: orders increased 215.40% and revenue increased 210.33%
- `computers_accessories` orders increased 183.31%, but revenue increased by a slower 131.22%
- `sports_leisure` revenue increased 138.63%, faster than its 128.07% order growth
- `bed_bath_table` orders increased 115.77% and revenue increased 109.22%

**Interpretation:** `watches_gifts` and `health_beauty` were the strongest growth categories. However, `watches_gifts` growth was volume-led: estimated category revenue per related order declined from about R$256.88 to R$201.24. `sports_leisure` was the only category in this group where revenue grew faster than order count.

**Limitation:** The comparison covers only five categories selected from the overall revenue ranking. Revenue per related order is not a product margin measure, and category growth may be affected by changes in product mix or pricing.

**Next question:** Can SQL calculate each category's order, revenue, and average-value growth rates directly rather than relying on manual calculations?

## 14 - Delivery Date Completeness

**Business question:** Are delivery date fields complete enough to support delivery performance analysis?

**SQL file:** `sql/14_delivery_data_quality.sql`

**Key results:**

- Delivered orders in the primary analysis window: 96,211
- Orders with an actual customer delivery date: 96,203
- Orders with an estimated delivery date: 96,211
- Actual delivery date completeness: approximately 99.99%

**Interpretation:** Delivery date coverage is sufficient for marketplace-level delivery performance analysis. Only eight delivered orders lack an actual customer delivery date.

**Limitation:** The eight records with missing actual delivery dates must be excluded from calculations that require delivery duration or late-delivery status.

**Next question:** How long did delivery take on average, and what percentage of delivered orders arrived after the estimated date?

## 15 - Delivery Performance

**Business question:** How long did delivery take, and what percentage of delivered orders arrived after the estimated date?

**SQL file:** `sql/15_delivery_performance.sql`

**Key results:**

- Analyzed delivered orders: 96,203
- Average delivery time from purchase to customer delivery: 12.48 days
- Late orders: 7,822
- Late-delivery rate: 8.13%

**Interpretation:** Olist delivered approximately 91.87% of analyzed orders by the estimated delivery date under this definition. Delivery delay is a meaningful operational risk to investigate alongside customer review scores.

**Limitation:** This result is an overall marketplace average. It does not show which states, sellers, categories, or order periods have the highest delay risk, and it does not establish that delays caused negative reviews.

**Next question:** Do late deliveries correspond to a higher rate of low customer review scores?

## 16 - Delivery and Customer Reviews

**Business question:** Do late deliveries correspond to lower customer review scores and a higher negative-review rate?

**SQL file:** `sql/16_delivery_reviews.sql`

**Key results:**

- Late orders: 7,658 reviewed orders, average review score 2.57, negative-review rate 53.98%
- On-time orders: 87,902 reviewed orders, average review score 4.30, negative-review rate 9.17%
- The late-delivery group had a negative-review rate approximately 5.9 times higher than the on-time group
- The late-delivery group had an average review score 1.73 points lower

**Interpretation:** Late delivery is strongly associated with poor customer experience in this dataset. Delivery reliability should therefore be treated as a growth constraint, not only an operations metric.

**Limitation:** This is an observational comparison and does not prove that late delivery caused the lower review scores. Product quality, seller behavior, category, price, and customer location may also influence reviews. The analysis includes only orders with a matched review.

**Next question:** Which customer states combine meaningful demand with high delivery-delay risk?

## 17 - State-Level Delivery Risk

**Business question:** Which customer states combine meaningful demand with elevated delivery-delay risk?

**SQL file:** `sql/17_state_delivery_risk.sql`

**Key results:**

- Sao Paulo (SP) was the largest market with 40,399 delivered orders and a 5.90% late-delivery rate
- Rio de Janeiro (RJ) had 12,310 delivered orders and a substantially higher 13.52% late-delivery rate
- Minas Gerais (MG) and Parana (PR) combined large order volumes with lower late-delivery rates of 5.63% and 5.02%
- Bahia (BA) had 3,253 delivered orders and a 14.05% late-delivery rate
- Some smaller states had higher rates, such as Alagoas (AL) at 23.99% and Maranhao (MA) at 19.64%, but their order volumes were much lower

**Interpretation:** RJ is the clearest large-market operations risk: it has substantial demand but a late-delivery rate more than twice SP's. BA is a smaller market with a similar risk pattern. SP, MG, and PR currently show scale with comparatively stronger delivery reliability.

**Limitation:** High delay rate in a small state may be unstable because of the smaller sample size. State-level delay rates do not identify whether the problem comes from sellers, carriers, distance, category mix, or customer location. Seller coverage and other operational variables are still required before recommending investment.

**Next question:** Do states with higher demand and delay risk also have weaker active-seller coverage?

## 18 - State-Level Seller Supply Proxy

**Business question:** Which customer states have meaningful demand but relatively limited local seller supply?

**SQL file:** `sql/18_state_seller_coverage.sql`

**Key results:**

- Sao Paulo had 1,849 sellers located in the state and 40,406 delivered orders, or 21.85 orders per local seller
- Rio de Janeiro had 12,310 delivered orders and 171 local sellers, or 71.99 orders per local seller
- Bahia had 3,253 delivered orders but only 19 local sellers, or 171.21 orders per local seller
- Pernambuco had 1,587 delivered orders and 9 local sellers, or 176.33 orders per local seller
- Para had 942 delivered orders and only 1 local seller, or 942 orders per local seller
- Some states with demand had zero locally located sellers, including Alagoas, Tocantins, Amapa, and Roraima

**Interpretation:** BA, PE, PA, and RJ combine meaningful customer demand with relatively limited local seller supply. This suggests possible supply-development opportunities, while SP and PR show stronger local seller coverage relative to demand.

**Limitation:** `seller_state` measures seller location, not actual service territory, fulfillment capacity, or seller productivity. `orders_per_seller` is therefore a supply-gap proxy and should not be interpreted as a causal capacity measure. Small states can also produce unstable ratios.

**Next question:** How can demand scale, delay risk, and seller supply be ranked together to identify regional candidates for deeper Python analysis?

## 19 - State Opportunity Rankings

**Business question:** How do customer demand, delivery risk, and local seller supply rank across states?

**SQL file:** `sql/19_state_rankings.sql`

**Key results:**

- SP ranked first in demand, but ranked 15th in delay risk and 15th in orders per local seller, making it a stable core market rather than an obvious supply-gap market
- RJ ranked second in demand and fourth in delay risk, combining large scale with an operational improvement opportunity
- BA ranked seventh in demand, third in delay risk, and fifth in supply gap, making it a balanced candidate for deeper investigation
- PE ranked fourth in supply gap but only 11th in demand, suggesting a smaller-market supply opportunity
- CE ranked second in delay risk and seventh in supply gap, but only 12th in demand
- MA and PA had extreme delay or supply-gap rankings, but their smaller order volumes and very small local seller counts require caution

**Interpretation:** Different states represent different types of opportunity: RJ is a large-market operations problem, BA is a balanced growth-and-operations candidate, and PE/CE are smaller markets requiring targeted validation. The three rankings should not be added together without explicit weights and normalization.

**Limitation:** The rankings are descriptive and use seller location as a supply proxy. They do not account for profit, freight cost, competition, seller productivity, or actual cross-state fulfillment. Small-sample states may be unstable.

**Next question:** Can Python standardize these metrics, test alternative weights, and produce a transparent regional opportunity score?

## 20 - Regional Opportunity Score Inputs

**Business question:** What comparable state-level metrics should feed the Python regional opportunity score?

**SQL file:** `sql/20_state_score_inputs.sql`

**Analysis scope:** Delivered orders purchased from January-August 2017 or January-August 2018. States with fewer than 500 delivered orders in the combined comparison period were excluded.

**Key results:**

- SP remained the largest included market with 31,907 delivered orders, a 171.96% order-growth rate, a 6.03% late-delivery rate, and a 10.59% negative-review rate
- RJ combined the second-largest volume at 9,307 orders with 113.90% growth, an 11.78% late-delivery rate, a 17.53% negative-review rate, and 54.43 orders per local seller
- BA combined 2,497 orders with a 13.62% late-delivery rate, a 17.12% negative-review rate, and 131.42 orders per local seller
- PE combined 1,210 orders with 137.99% growth and 134.44 orders per local seller, but its smaller scale requires caution
- PR combined 3,904 orders, 127.24% growth, a 4.74% late-delivery rate, a 10.37% negative-review rate, and only 11.19 orders per local seller
- CE had a high 15.93% late-delivery rate and 16.86% negative-review rate, but only 954 delivered orders

**Interpretation:** RJ is a large-scale growth and operations candidate. BA is a balanced candidate with meaningful demand, elevated delivery and review risk, and limited local seller supply. PE may represent a supply-development opportunity, while PR provides a useful benchmark for strong growth with lower operational risk. SP is the scale benchmark rather than an obvious supply-gap market.

**Limitation:** Growth compares January-August 2018 with January-August 2017 and is not a forecast. Customer review metrics use only orders with matched reviews. Seller supply is based on seller location and does not measure actual service territory or capacity. The final score must make these assumptions and weights explicit.

**Next question:** How should Python standardize these inputs and test whether the recommended states remain stable under different weights?
