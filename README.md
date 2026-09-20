# AI Sales Analytics Assistant

An enterprise analytics platform that translates plain English business questions into relational SQL queries, executes them against an e-commerce data warehouse, and returns interactive charts with automated executive insights.

Built on the real-world Olist Brazilian E-Commerce dataset (100,000+ orders across 8 relational tables).

---

## Problem

Business and operations teams routinely depend on data analysts for standard reporting: identifying top sales regions, tracking monthly trends, or reviewing customer retention. This creates an operational bottleneck where analysts spend hours answering repetitive questions instead of focusing on strategic modeling. Non-technical stakeholders lack SQL knowledge to self-serve, while static BI dashboards cannot anticipate every ad-hoc business question.

---

## Solution

The AI Sales Analytics Assistant enables non-technical stakeholders to converse directly with an enterprise relational database using natural language.

Powered by Groq's 120B model and an embedded data architecture (SQLite / MySQL), the platform:
1. Translates natural language questions into optimized multi-table SQL queries in real time.
2. Automatically determines the best visualization format (time-series line, categorical bar, or distribution pie).
3. Synthesizes concise, actionable business takeaways from the resulting data.
4. Provides an executive KPI dashboard tracking Revenue, Volume, Review Scores, and Repeat Customers.

---

## How I Approached It

- **Data Modeling & Architecture**: Ingested and indexed the real-world Olist dataset (100,000+ orders across 8 relational tables). Structured an embedded, indexed SQLite warehouse (with full MySQL compatibility) to achieve sub-0.25s join speeds with zero cloud hosting costs.
- **Prompt Engineering & Schema Context**: Designed a metadata prompt layer passing schema constraints, table relationships, and business rules to Groq's 120B model to generate deterministic, executable SQL without conversational preamble.
- **Autonomous Visualization**: Built a rule-based inference engine that inspects query result datatypes and temporal keywords to dynamically select the ideal Plotly chart type.
- **Executive Summaries**: Configured an automated analytical layer that evaluates query results to produce two-sentence business takeaways highlighting key trends and anomalies.

---

## Key Upgrades Over Version 1

| Capability | Version 1.0 | Version 2.0 (Current) |
|---|---|---|
| Data Architecture | Single flat table (Superstore, synthetic data) | 8-table normalized relational warehouse (Olist, real-world data) |
| Query Complexity | Single-table SELECT and WHERE statements | Multi-table relational JOINs resolving foreign key relationships |
| Data Sanitization | Basic English column names | Dynamic SKU resolution for 32-character anonymized product hashes; translation of Portuguese categories |
| Customer Intelligence | Total customer ID counts | Differentiates transactional IDs from unique individuals to track repeat buyers |
| Visualization Engine | Static bar charts only | Automated chart type inference based on data shape and temporal keywords |
| Analytical Output | Raw table and chart | SQL execution, dynamic visualization, and automated executive insights |
| Interface Design | Basic dark mode theme | Unified corporate design system with custom Plotly templates and high-contrast typography |
| Deployment | Local MySQL only | Embedded, indexed database architecture deployed online at zero hosting cost |

---

## Key Features

- **Natural Language to SQL**: Converts plain English business questions into multi-table SQL queries in seconds.
- **Relational Joins**: Traverses orders, order items, products, customers, sellers, payments, reviews, and category translations.
- **Dynamic Charts**: Automatically renders Line, Bar, or Pie charts using Plotly Express.
- **Executive Metric Suite**: Live KPI cards tracking Total Revenue (R$ 13.6M), Orders (99.4k), Average Review (4.1 / 5), and Unique Customers (96.1k).
- **Delivery Performance Analysis**: Quantifies how delivery delays correlate directly with lower review ratings.
- **Query Audit Log**: Retains a session history of all executed questions, generated SQL queries, and record counts.

---

## Sample Business Questions

- Top 10 product categories by total revenue?
- Monthly sales trend for delivered orders?
- Which states generate the highest revenue?
- What is the breakdown of customer payment methods?
- Average review score by product category?
- Top 5 sellers by total revenue?
- How many orders were canceled?
- Late delivery rate by state?

---

## Tech Stack

- **Frontend**: Streamlit
- **Visualization**: Plotly Express
- **Language Model**: Groq API (`openai/gpt-oss-120b`)
- **Data Engine**: SQLite, MySQL, Pandas
- **Environment**: Python 3.11+

---

## Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ipratik35/ai-sales-dashboard.git
   cd ai-sales-dashboard
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Launch the application**:
   ```bash
   streamlit run app.py
   ```
