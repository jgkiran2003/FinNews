# FinNews: AI-Powered Financial Sentiment Analysis Pipeline

FinNews is a sophisticated, end-to-end data engineering and machine learning project that automates the process of gathering financial news, analyzing market sentiment using a custom-trained AI model, and visualizing the results on an interactive dashboard.

This project is designed to showcase a complete pipeline, from raw data acquisition and model fine-tuning to data persistence and final presentation. It serves as a strong portfolio piece demonstrating skills in Python, NLP, data architecture, and web application development.


## 🚀 Core Features

-   **Automated News Aggregation**: Fetches and de-duplicates the latest financial news from multiple sources using a modular, extensible client system (initially supporting NewsAPI and MarketAux).
-   **AI-Powered Sentiment Analysis**: Employs a **fine-tuned FinBERT model** (`ProsusAI/finbert`) to classify news headlines into `positive`, `negative`, or `neutral` sentiment with high contextual accuracy for financial text.
-   **Robust Data Persistence**: Utilizes a well-structured **SQLite database** to store articles, sentiment scores, and related metadata, enabling historical analysis and preventing redundant processing.
-   **Interactive Data Dashboard**: A **Streamlit**-based web application provides an intuitive interface for visualizing sentiment trends, including dynamic charts and a searchable table of recent headlines.
-   **Jupyter Notebooks for ML Experimentation**: Includes detailed notebooks for both the **model training process** and **performance evaluation**, demonstrating a clear and reproducible machine learning workflow.


## 🏛️ System Architecture

The project is structured as a classic data pipeline, with clear separation of concerns between data ingestion, processing, storage, and presentation.

1.  **News Ingestion (`src/finnews/news_apis/`)**
    -   A `BaseAPI` class provides a foundation for making authenticated and rate-limited requests.
    -   `NewsAPIClientAdapter` and `MarketAuxClient` are specific implementations for different news providers. They normalize the fetched data into a consistent format.
    -   The main application (`app.py`) orchestrates calls to these clients to gather a fresh set of articles.

2.  **Data Storage (`src/finnews/storage/`)**
    -   A **SQLite database** (`finnews.db`) acts as the central data store. Its schema (`schema.sql`) is designed to handle articles, sentiment results, and potentially future data like stock price movements.
    -   The `db.py` module provides a clean, function-based API for all database operations (e.g., `init_db`, `upsert_article`, `save_sentiment`). It includes `UPSERT` logic to efficiently handle new and existing articles.

3.  **Sentiment Analysis Engine**
    -   **Model Fine-Tuning (`dev/finbert_finetuned_v1/` & `src/finnews/train_model.py`)**: The core of the project's intelligence. The `ProsusAI/finbert` model is fine-tuned on a labeled financial sentiment dataset using the Hugging Face `Trainer` API, PyTorch, and `scikit-learn`. This step creates a highly specialized model for our specific domain.
    -   **Inference (`src/finnews/predict_text.py`)**: A simple, efficient module loads the saved fine-tuned model from disk and provides a `predict_sentiment` function for real-time classification of news headlines during the pipeline run.

4.  **Presentation Layer (`src/finnews/dashboard.py`)**
    -   A Streamlit application that queries the SQLite database to fetch the latest articles and sentiment data.
    -   It uses `pandas` for data manipulation and `matplotlib` to generate and display a pie chart of the current market sentiment distribution.
    -   The dashboard is designed to be the primary user-facing component of the system.


## 💡 Technical Highlights & Challenges Solved

-   **Domain-Specific Model Customization**: The most significant technical achievement is the fine-tuning of a pre-trained Transformer model. This goes beyond simply using an off-the-shelf API, demonstrating a deeper understanding of the NLP workflow required to achieve high performance on specialized text. The process involved data preparation, managing `label2id` mappings, and using the `Trainer` for efficient, mixed-precision training.
-   **Modular and Extensible API Clients**: The design of the `news_apis` module makes it straightforward to add new data sources without altering the main application logic. This is a key principle of good software architecture.
-   **Efficient Data Handling**: The use of `UPSERT` logic in the database ensures data integrity and avoids duplication. Checking if an article URL has already been processed before making an expensive sentiment prediction call is a crucial optimization.
-   **Decoupled Architecture**: Each component (ingestion, storage, AI, UI) is self-contained. The database acts as the central message bus, allowing each part to operate independently. For example, the Streamlit app doesn't need to know how the data was fetched or analyzed; it only needs to read from the database.


## 🛠️ Technologies & Libraries Used

-   **Machine Learning & NLP**:
    -   `PyTorch`: The deep learning framework used for model training and inference.
    -   `Hugging Face Transformers`: For accessing the pre-trained FinBERT model and using the high-level `Trainer` API.
    -   `scikit-learn`: For splitting data and evaluating model performance (e.g., confusion matrix, classification report).
    -   `pandas`: For data manipulation and preparation.

-   **Backend & Data**:
    -   `Python 3`: The core programming language.
    -   `SQLite`: For lightweight, file-based relational data storage.
    -   `requests` & `newsapi-python`: For interacting with external news APIs.

-   **Frontend & Visualization**:
    -   `Streamlit`: To rapidly build and deploy the interactive web dashboard.
    -   `matplotlib`: For creating static charts and plots.

-   **Development & Tooling**:
    -   `Jupyter Notebook`: For ML experimentation and model evaluation.
    -   `python-dotenv`: For managing environment variables like API keys securely.


## ⚙️ Setup & Usage

### Prerequisites
-   Python 3.8+
-   A NewsAPI Key (from [newsapi.org](https://newsapi.org/))
-   A MarketAux API Key (from [marketaux.com](https://www.marketaux.com/))

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/finnews.git
    cd finnews
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and add your API keys:
    ```env
    NEWSAPI_API_KEY="your_newsapi_key"
    MARKETAUX_API_KEY="your_marketaux_key"
    ```

### Running the Application

1.  **Train the Sentiment Model (First-time setup):**
    The fine-tuned FinBERT model is the heart of this project. Run the training script to generate it. This will download the base model from Hugging Face and fine-tune it on the provided dataset.
    ```bash
    python src/finnews/train_model.py
    ```
    This will create a `./final_model/model` directory containing the trained model artifacts.

2.  **Run the Data Ingestion Pipeline:**
    Execute the main app script to fetch news, run sentiment analysis, and save the results to the database.
    ```bash
    python src/finnews/app.py
    ```

3.  **Launch the Dashboard:**
    Start the Streamlit web server to view the results.
    ```bash
    streamlit run src/finnews/dashboard.py
    ```
    Navigate to `http://localhost:8501` in your browser.


## 📈 Future Improvements

-   **Expand Data Sources**: Integrate additional news APIs like GNews or financial-specific sources like Polygon.io.
-   **Named Entity Recognition (NER)**: Add an NER model to extract company names, stock tickers, and key people from headlines, linking sentiment directly to specific entities.
-   **Track Price Correlation**: Ingest historical stock price data (e.g., from Alpha Vantage) to analyze the correlation between news sentiment and subsequent market movements.
-   **Dockerize the Application**: Containerize the pipeline and dashboard for simplified deployment and scalability.
-   **Advanced Visualizations**: Use libraries like Plotly or Altair for more interactive charts on the dashboard.
