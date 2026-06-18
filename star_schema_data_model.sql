-- =========================================================================
-- Credit Card Financial Portfolio - Star Schema Data Modeling & ETL
-- Author: Yogesh Birla
-- Repository: https://github.com/yogs011/citi-credit-card-portfolio-analytics
-- Database Engine: PostgreSQL / Data Warehouse
-- Modeling: Star Schema (Fact: fact_credit_card | Dimensions: dim_customer, dim_date)
-- =========================================================================

-- -------------------------------------------------------------------------
-- 1. STAR SCHEMA DEFINITIONS
-- -------------------------------------------------------------------------

CREATE DATABASE ccdb;

DROP TABLE IF EXISTS fact_credit_card CASCADE;
DROP TABLE IF EXISTS dim_customer CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- Dimension 1: Customer Demographic (dim_customer)
CREATE TABLE dim_customer (
    Client_Num INT PRIMARY KEY,
    Customer_Age INT,
    Gender VARCHAR(10),
    Dependent_Count INT,
    Education_Level VARCHAR(50),
    Marital_Status VARCHAR(20),
    State_cd VARCHAR(10),
    Zipcode VARCHAR(20),
    Car_Owner VARCHAR(5),
    House_Owner VARCHAR(5),
    Personal_Loan VARCHAR(5),
    Contact VARCHAR(50),
    Customer_Job VARCHAR(50),
    Income INT,
    Cust_Satisfaction_Score INT
);

-- Dimension 2: Date Dimension (dim_date)
CREATE TABLE dim_date (
    Date_Key DATE PRIMARY KEY,
    Week_Num VARCHAR(20),
    Week_Num_Int INT,
    Qtr VARCHAR(10),
    Current_Year INT,
    Month_Num INT,
    Month_Name VARCHAR(20)
);

-- Fact Table: Credit Card Transactions & Balances (fact_credit_card)
CREATE TABLE fact_credit_card (
    Transaction_ID SERIAL PRIMARY KEY,
    Client_Num INT REFERENCES dim_customer(Client_Num),
    Date_Key DATE REFERENCES dim_date(Date_Key),
    Card_Category VARCHAR(20),
    Annual_Fees INT,
    Activation_30_Days INT,
    Customer_Acq_Cost INT,
    Credit_Limit DECIMAL(10,2),
    Total_Revolving_Bal INT,
    Total_Trans_Amt INT,
    Total_Trans_Vol INT,
    Avg_Utilization_Ratio DECIMAL(10,3),
    Use_Chip VARCHAR(20),
    Exp_Type VARCHAR(50),
    Interest_Earned DECIMAL(10,3),
    Delinquent_Acc INT
);

-- Indexes for optimized Star Schema JOIN performance
CREATE INDEX idx_fact_client_num ON fact_credit_card(Client_Num);
CREATE INDEX idx_fact_date_key ON fact_credit_card(Date_Key);
CREATE INDEX idx_fact_card_cat ON fact_credit_card(Card_Category);

-- -------------------------------------------------------------------------
-- 2. ETL INGESTION & DATA TRANSFORMATION
-- -------------------------------------------------------------------------

-- Staging Tables for raw CSV data extraction
CREATE TEMP TABLE staging_credit_card (
    Client_Num INT,
    Card_Category VARCHAR(20),
    Annual_Fees INT,
    Activation_30_Days INT,
    Customer_Acq_Cost INT,
    Week_Start_Date DATE,
    Week_Num VARCHAR(20),
    Qtr VARCHAR(10),
    current_year INT,
    Credit_Limit DECIMAL(10,2),
    Total_Revolving_Bal INT,
    Total_Trans_Amt INT,
    Total_Trans_Vol INT,
    Avg_Utilization_Ratio DECIMAL(10,3),
    Use_Chip VARCHAR(20),
    Exp_Type VARCHAR(50),
    Interest_Earned DECIMAL(10,3),
    Delinquent_Acc INT
);

SET datestyle TO 'ISO, DMY';

-- Ingest Raw Customer CSV Data (Base + Week 53)
COPY dim_customer FROM 'C:/customer.csv' DELIMITER ',' CSV HEADER;
COPY dim_customer FROM 'C:/cust_add.csv' DELIMITER ',' CSV HEADER ON CONFLICT (Client_Num) DO NOTHING;

-- Ingest Raw Credit Card CSV Data (Base + Week 53) into Staging
COPY staging_credit_card FROM 'C:/credit_card.csv' DELIMITER ',' CSV HEADER;
COPY staging_credit_card FROM 'C:/cc_add.csv' DELIMITER ',' CSV HEADER;

-- Populate Date Dimension (dim_date) from distinct dates in staging
INSERT INTO dim_date (Date_Key, Week_Num, Week_Num_Int, Qtr, Current_Year, Month_Num, Month_Name)
SELECT DISTINCT
    Week_Start_Date AS Date_Key,
    Week_Num,
    CAST(SUBSTRING(Week_Num FROM '[0-9]+') AS INT) AS Week_Num_Int,
    Qtr,
    current_year,
    EXTRACT(MONTH FROM Week_Start_Date) AS Month_Num,
    TO_CHAR(Week_Start_Date, 'Month') AS Month_Name
FROM staging_credit_card
ON CONFLICT (Date_Key) DO NOTHING;

-- Populate Fact Table (fact_credit_card) with cleaned and normalized data
INSERT INTO fact_credit_card (
    Client_Num,
    Date_Key,
    Card_Category,
    Annual_Fees,
    Activation_30_Days,
    Customer_Acq_Cost,
    Credit_Limit,
    Total_Revolving_Bal,
    Total_Trans_Amt,
    Total_Trans_Vol,
    Avg_Utilization_Ratio,
    Use_Chip,
    Exp_Type,
    Interest_Earned,
    Delinquent_Acc
)
SELECT 
    Client_Num,
    Week_Start_Date,
    TRIM(Card_Category),
    Annual_Fees,
    Activation_30_Days,
    Customer_Acq_Cost,
    Credit_Limit,
    Total_Revolving_Bal,
    Total_Trans_Amt,
    Total_Trans_Vol,
    Avg_Utilization_Ratio,
    TRIM(Use_Chip),
    TRIM(Exp_Type),
    Interest_Earned,
    Delinquent_Acc
FROM staging_credit_card;


-- -------------------------------------------------------------------------
-- 3. STAR SCHEMA ANALYTICS QUERIES (ETL VALIDATION & KPIS)
-- -------------------------------------------------------------------------

-- Query 1: Fact-Dimension Join for Customer Segment Revenue
SELECT 
    c.Education_Level,
    c.Gender,
    COUNT(DISTINCT f.Client_Num) AS Active_Cardholders,
    SUM(f.Total_Trans_Amt) AS Total_Spend,
    SUM(f.Annual_Fees + f.Total_Trans_Amt + f.Interest_Earned) AS Total_Revenue,
    ROUND(AVG(f.Avg_Utilization_Ratio) * 100, 2) AS Avg_Utilization_Pct,
    ROUND(AVG(f.Delinquent_Acc) * 100, 2) AS Delinquency_Rate_Pct
FROM fact_credit_card f
INNER JOIN dim_customer c ON f.Client_Num = c.Client_Num
GROUP BY c.Education_Level, c.Gender
ORDER BY Total_Revenue DESC;

-- Query 2: Time-Dimension Join for Quarterly Performance
SELECT 
    d.Current_Year,
    d.Qtr,
    COUNT(f.Transaction_ID) AS Transaction_Records,
    SUM(f.Total_Trans_Amt) AS Total_Quarterly_Spend,
    SUM(f.Interest_Earned) AS Total_Interest_Earned,
    ROUND(AVG(f.Credit_Limit), 2) AS Avg_Credit_Limit
FROM fact_credit_card f
INNER JOIN dim_date d ON f.Date_Key = d.Date_Key
GROUP BY d.Current_Year, d.Qtr
ORDER BY d.Current_Year, d.Qtr;
