"""
Credit Card Financial Portfolio & Risk Analytics
================================================
Author: Yogesh Birla
GitHub: https://github.com/yogs011/citi-credit-card-portfolio-analytics
Tech Stack: Power BI | DAX | Pandas | NumPy | EDA | Star Schema Modeling | ETL

Highlights:
- End-to-End ETL Pipeline: Extraction, Cleansing, Normalization, and Star Schema Modeling.
- Analysis of 10,000+ cardholder accounts and $55M+ portfolio transaction and fee volume.
- Portfolio KPI Computation (Net Revenue, Delinquency Rate, Spend Channels, Utilization).
- Exploratory Data Analysis (EDA) & Automated Chart Generation to 'output_charts/' directory.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Visual formatting configurations
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.linewidth'] = 0.8


def run_etl_pipeline(base_path="."):
    """
    ETL Pipeline:
    1. Extract: Ingest raw CSV files (base + week 53 additions).
    2. Transform: Clean strings, format dates, engineer revenue and demographic buckets.
    3. Model: Assemble Star Schema DataFrames (dim_customer, dim_date, fact_credit_card).
    """
    print("="*65)
    print("        STARTING ETL PIPELINE (PANDAS & NUMPY)")
    print("="*65)
    
    # 1. EXTRACT
    print("[1/3] EXTRACT: Reading raw CSV datasets...")
    cc = pd.read_csv(os.path.join(base_path, "credit_card.csv"))
    cust = pd.read_csv(os.path.join(base_path, "customer.csv"))
    cc_add = pd.read_csv(os.path.join(base_path, "cc_add.csv"))
    cust_add = pd.read_csv(os.path.join(base_path, "cust_add.csv"))

    cc_raw = pd.concat([cc, cc_add], ignore_index=True)
    cust_raw = pd.concat([cust, cust_add], ignore_index=True)
    print(f"      Extracted {len(cc_raw):,} credit card rows & {len(cust_raw):,} customer rows.")

    # 2. TRANSFORM
    print("[2/3] TRANSFORM: Cleaning and engineering features...")
    cc_raw.columns = cc_raw.columns.str.strip()
    cust_raw.columns = cust_raw.columns.str.strip()

    if "Use Chip" in cc_raw.columns:
        cc_raw.rename(columns={"Use Chip": "Use_Chip"}, inplace=True)
    if "Exp Type" in cc_raw.columns:
        cc_raw.rename(columns={"Exp Type": "Exp_Type"}, inplace=True)

    # String stripping
    cc_raw['Card_Category'] = cc_raw['Card_Category'].str.strip()
    cc_raw['Use_Chip'] = cc_raw['Use_Chip'].str.strip()
    cc_raw['Exp_Type'] = cc_raw['Exp_Type'].str.strip()
    cust_raw['Gender'] = cust_raw['Gender'].str.strip()
    cust_raw['Education_Level'] = cust_raw['Education_Level'].str.strip()
    cust_raw['Customer_Job'] = cust_raw['Customer_Job'].str.strip()

    # Datatype parsing & cleaning with NumPy / Pandas
    cc_raw['Delinquent_Acc'] = pd.to_numeric(cc_raw['Delinquent_Acc'], errors='coerce').fillna(0).astype(int)
    cc_raw['Week_Start_Date'] = pd.to_datetime(cc_raw['Week_Start_Date'], format='%d-%m-%Y', errors='coerce')
    cc_raw['Total_Revenue'] = cc_raw['Annual_Fees'] + cc_raw['Total_Trans_Amt'] + cc_raw['Interest_Earned']
    
    # Customer Demographic Bins
    cust_raw['Age_Group'] = pd.cut(
        cust_raw['Customer_Age'], 
        bins=[18, 30, 45, 60, 100], 
        labels=['18-30', '31-45', '46-60', '60+']
    )
    cust_raw['Income_Bracket'] = pd.cut(
        cust_raw['Income'],
        bins=[-1, 35000, 70000, 120000, 1000000],
        labels=['Low (<$35k)', 'Moderate ($35k-$70k)', 'High ($70k-$120k)', 'Executive (>$120k)']
    )

    # 3. STAR SCHEMA LOAD
    print("[3/3] LOAD: Constructing Star Schema Data Model...")
    dim_customer = cust_raw.drop_duplicates(subset=['Client_Num']).copy()
    
    dim_date = cc_raw[['Week_Start_Date', 'Week_Num', 'Qtr', 'current_year']].drop_duplicates().copy()
    dim_date.rename(columns={'Week_Start_Date': 'Date_Key', 'current_year': 'Current_Year'}, inplace=True)
    dim_date['Week_Num_Int'] = dim_date['Week_Num'].str.extract(r'(\d+)').astype(int)
    dim_date['Month_Name'] = dim_date['Date_Key'].dt.strftime('%B')

    fact_credit_card = cc_raw.copy()
    fact_credit_card.rename(columns={'Week_Start_Date': 'Date_Key'}, inplace=True)

    # Merged Master DataFrame for EDA
    df_merged = pd.merge(fact_credit_card, dim_customer, on="Client_Num", how="inner")
    print(f"      ETL Complete: {len(df_merged):,} modeled records across {dim_customer['Client_Num'].nunique():,} accounts.")
    print("="*65 + "\n")

    return df_merged, dim_customer, dim_date, fact_credit_card


def compute_portfolio_kpis(df):
    """Calculate and display core portfolio metrics and KPIs."""
    total_accounts = df['Client_Num'].nunique()
    total_trans_amt = df['Total_Trans_Amt'].sum()
    total_trans_vol = df['Total_Trans_Vol'].sum()
    total_interest = df['Interest_Earned'].sum()
    total_annual_fees = df['Annual_Fees'].sum()
    total_combined_volume = total_annual_fees + total_trans_amt + total_interest
    delinquency_rate = df['Delinquent_Acc'].mean() * 100
    avg_utilization = df['Avg_Utilization_Ratio'].mean() * 100
    avg_credit_limit = df['Credit_Limit'].mean()
    arpu = total_combined_volume / total_accounts

    print("="*65)
    print("           EXECUTIVE PORTFOLIO KPI REPORT")
    print("="*65)
    print(f"  Active Cardholder Accounts    : {total_accounts:,}")
    print(f"  Total Transaction Spend ($)   : ${total_trans_amt:,.2f}")
    print(f"  Total Transaction Volume (#)  : {total_trans_vol:,.0f}")
    print(f"  Interest Earned Revenue ($)   : ${total_interest:,.2f}")
    print(f"  Annual Fees Collected ($)     : ${total_annual_fees:,.2f}")
    print(f"  Total Combined Volume ($)     : ${total_combined_volume:,.2f}")
    print(f"  Average Revenue Per User (ARPU): ${arpu:,.2f}")
    print(f"  Portfolio Delinquency Rate    : {delinquency_rate:.2f}%")
    print(f"  Average Credit Utilization    : {avg_utilization:.2f}%")
    print(f"  Average Credit Limit          : ${avg_credit_limit:,.2f}")
    print("="*65 + "\n")


def generate_eda_charts(df, output_dir="output_charts"):
    """Generate high-resolution EDA visualization figures."""
    os.makedirs(output_dir, exist_ok=True)
    print(f">>> Generating EDA charts to '{output_dir}/'...")

    # Chart 1: Revenue by Card Category & Gender
    fig, ax = plt.subplots(figsize=(10, 6))
    category_rev = df.groupby(['Card_Category', 'Gender'])['Total_Trans_Amt'].sum().unstack()
    category_rev.plot(kind='bar', stacked=False, color=['#2b5c8f', '#d95f02'], ax=ax)
    ax.set_title("Total Transaction Spend by Card Category & Gender", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Card Category", fontsize=12)
    ax.set_ylabel("Spend Amount ($)", fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x*1e-6:.1f}M"))
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "1_revenue_by_card_category.png"), dpi=300)
    plt.close()

    # Chart 2: Spend Channel Share (Chip, Swipe, Online)
    fig, ax = plt.subplots(figsize=(8, 6))
    channel_spend = df.groupby('Use_Chip')['Total_Trans_Amt'].sum().sort_values(ascending=False)
    colors = ['#1f77b4', '#aec7e8', '#ff7f0e']
    channel_spend.plot(kind='pie', autopct='%1.1f%%', colors=colors, startangle=140, ax=ax, textprops={'fontsize': 11})
    ax.set_title("Transaction Spend Share by Channel (Swipe, Chip, Online)", fontsize=14, fontweight='bold', pad=15)
    ax.set_ylabel("")
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "2_spend_channel_share.png"), dpi=300)
    plt.close()

    # Chart 3: Delinquency Rate by Income Bracket
    fig, ax = plt.subplots(figsize=(10, 6))
    risk_summary = df.groupby('Income_Bracket', observed=False)['Delinquent_Acc'].mean() * 100
    sns.barplot(x=risk_summary.index, y=risk_summary.values, hue=risk_summary.index, palette='Blues_r', legend=False, ax=ax)
    ax.set_title("Delinquency Rate Across Customer Income Brackets (%)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Income Tier", fontsize=12)
    ax.set_ylabel("Delinquency Rate (%)", fontsize=12)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height()),
                    ha='center', va='bottom', fontsize=11, xytext=(0, 5), textcoords='offset points')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "3_delinquency_by_income.png"), dpi=300)
    plt.close()

    # Chart 4: Weekly Transaction Volume Trend
    fig, ax = plt.subplots(figsize=(12, 5))
    weekly_trend = df.groupby('Date_Key')['Total_Trans_Amt'].sum().reset_index()
    sns.lineplot(data=weekly_trend, x='Date_Key', y='Total_Trans_Amt', color='#1b9e77', linewidth=2.5, marker='o', ax=ax)
    ax.set_title("Weekly Portfolio Transaction Volume Trend ($)", fontsize=14, fontweight='bold', pad=15)
    ax.set_xlabel("Week Start Date", fontsize=12)
    ax.set_ylabel("Weekly Spend ($)", fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x*1e-3:.0f}K"))
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "4_weekly_transaction_trend.png"), dpi=300)
    plt.close()

    print(" All EDA charts generated and saved to 'output_charts/'.")


def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    df, dim_customer, dim_date, fact_credit_card = run_etl_pipeline(base_path)
    compute_portfolio_kpis(df)
    generate_eda_charts(df, output_dir=os.path.join(base_path, "output_charts"))
    print(" Pipeline executed successfully!")


if __name__ == "__main__":
    main()
