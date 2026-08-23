# Credit Card Financial Portfolio & Risk Analytics
**Author:** [Yogesh Birla](https://github.com/yogs011)  
**Core Stack:** `Power BI`, `DAX`, `Pandas`, `NumPy`, `EDA`, `Star Schema Modeling`, `ETL`, `SQL (PostgreSQL)`

---

## Project Architecture And Overview
Architected an end-to-end financial analytics pipeline for **10,000+ credit card accounts** and **$55M+ in transaction volume**, performing data cleansing, normalization, and Star Schema data modeling across transaction and demographic data.

```mermaid
flowchart LR
    A[Raw CSV Datasets<br/>credit_card.csv & customer.csv] -->|Python ETL Pipeline<br/>Pandas & NumPy| B[(PostgreSQL Data Warehouse<br/>Star Schema Architecture)]
    B -->|Star Schema Tables| C[fact_credit_card<br/>Fact Table]
    B -->|Dimension Tables| D[dim_customer & dim_date<br/>Dimension Tables]
    C --> E[Power BI Dashboard<br/>15+ Custom DAX Measures]
    D --> E
    E --> F[Executive Financial Reports<br/>Customer & Transaction Dashboards]
```

---




