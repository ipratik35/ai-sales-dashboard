# 📊 AI Sales Analytics Dashboard

An executive e-commerce analytics dashboard powered by **Streamlit**, **Plotly**, and **Groq LLM** (Natural Language to SQL). Built on real-world transaction data from the **Olist Brazilian E-Commerce dataset** (100k+ orders, 9 tables).

---

## 🚀 Key Features

* **Executive KPI Suite**: Total Revenue, Total Orders, Average Review Score, and Unique Customers with repeat-purchase tracking.
* **Interactive Visualizations**:
  * Monthly Revenue Trends
  * Top 10 Product Categories by Revenue
  * Top 10 States by Revenue (with dual-metric hover tooltips)
  * Payment Method Value Distribution
  * Review Score Distribution (1–5 stars)
  * Delivery Performance & Late Delivery Impact on Customer Satisfaction
* **AI-Powered Sales Assistant**:
  * Plain English questions converted into optimized SQL queries in real-time using Groq API.
  * Automatic smart chart selection (line trends, category bars, distribution pies).
  * Automated 2-sentence executive business insights generated for every query.
* **Unified Design System**: Minimalist light theme with custom Plotly template (`#F7F8FA` background, high-contrast dark gray typography, restrained blue gradients, and muted semantic accents).
* **Session Query History**: Logs all AI-generated questions, SQL code, and row counts.

---

## 🛠️ Tech Stack

* **Frontend / UI**: [Streamlit](https://streamlit.io/)
* **Charts & Plots**: [Plotly Express](https://plotly.com/python/)
* **AI / NLP**: [Groq API](https://groq.com/) (`openai/gpt-oss-120b`)
* **Database**: SQLite (embedded for instant cloud deployment) / MySQL
* **Data Manipulation**: [Pandas](https://pandas.pydata.org/)

---

## 📁 Dataset

* **Source**: Olist Brazilian E-Commerce Public Dataset
* **Size**: 100,000+ orders across 8 relational tables
* **Note**: Product names in Olist were anonymized with 32-character hashes; this dashboard programmatically synthesizes readable composite SKU labels (e.g., `garden_tools (#422879)`).

---

## 💻 Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/ai-sales-dashboard.git
   cd ai-sales-dashboard
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```
