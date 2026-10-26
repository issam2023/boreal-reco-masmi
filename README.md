# Boréal Marché — Apriori Recommendation Engine

**Vanier College — 420-975-VA: Unsupervised Learning**

**Author:** Abdelhafid Masmi

## Project Overview

A grocery recommendation system using association rule mining
with Apriori (mlxtend).

The system analyzes 1,000,000 shopping baskets and 98 products
to recommend items based on basket contents.

## Technologies

- Python 3.12
- Pandas
- mlxtend (Apriori)
- Jupyter Notebook
- Streamlit

## Project Structure

- `notebooks/` — Data analysis and Apriori mining
- `models/` — Exported rules and metadata
- `app/` — Streamlit recommendation application
- `reports/` — Performance benchmarks
- `data/` — Local datasets (excluded from Git)

## Current Results

- Transactions: 8,379,837
- Shopping baskets: 1,000,000
- Products: 98
- Generated rules: 26,991 (lift > 1)
- Recommendation coverage: 59.2%

## Status

Work in progress. Streamlit application under development.

## Data

The original transaction dataset is excluded from GitHub
because of its size. Data access instructions will be added.

## Limitations

Apriori can be memory-intensive on large datasets.
Rare products may not appear in recommendations because
they do not meet the minimum support threshold.
