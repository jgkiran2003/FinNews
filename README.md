📈 FinNews: Market Sentiment Dashboard
======================================

FinNews is an automated pipeline that fetches the latest financial news, performs sentiment analysis using a fine-tuned Transformer model (FinBERT), and visualizes the market "mood" through an interactive web dashboard.

🚀 Features
-----------

-   **Automated News Ingestion**: Fetches top business headlines via NewsAPI.

-   **AI-Powered Sentiment**: Uses a local `transformers` model to classify headlines as **Positive**, **Negative**, or **Neutral**.

-   **Persistent Storage**: Saves articles and sentiment scores in a SQLite database to track trends over time.

-   **Interactive Dashboard**: A Streamlit-based UI featuring sentiment distribution charts and searchable headline tables.

🛠️ Tech Stack
--------------

-   **Language**: Python 3.x

-   **UI/Visualization**: Streamlit, Matplotlib, Pandas

-   **AI/NLP**: PyTorch, Hugging Face Transformers (FinBERT)

-   **Database**: SQLite

-   **API**: NewsAPI

📋 Prerequisites
----------------

Before running the application, ensure you have:

1.  **Python 3.8+** installed.

2.  A **NewsAPI Key** (get one at [newsapi.org](https://newsapi.org/)).

3.  The pre-trained model folder (`sentiment_analysis_model`) located in the `src/finnews/` directory.

⚙️ Installation & Setup
-----------------------

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd FinNews
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:** Create a `.env` file in the root directory and add your API key:

    ```
    NEWS_API_KEY=your_actual_api_key_here
    ```

🖥️ Usage
---------

### 1\. Fetch News and Predict Sentiment

Run the ingestion script to populate the database with the latest headlines:

```bash
python src/finnews/app.py
```

*This will fetch news, run the sentiment model, and save the results to `finnews.db`*.

### 2\. Launch the Dashboard

Start the Streamlit interface to visualize the data:

```bash
streamlit run src/finnews/dashboard.py
```

*The dashboard will be available at `http://localhost:8501`*.

📂 Project Structure
--------------------

-   `src/finnews/app.py`: The main entry point for data collection and processing.

-   `src/finnews/dashboard.py`: The Streamlit UI code.

-   `src/finnews/predict_text.py`: Logic for loading the Transformer model and generating predictions.

-   `src/finnews/news_apis/`: Adapters for various financial news providers.

-   `src/finnews/storage/`: Database schemas and CRUD operations.

📊 Roadmap
----------

-   [ ] Add support for MarketAux and GNews APIs.

-   [ ] Implement entity extraction to identify specific companies in headlines.

* * * * *

*Developed as a tool for financial sentiment tracking and NLP analysis.*