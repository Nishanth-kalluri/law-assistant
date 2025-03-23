# Connecticut Legal Assistant

A specialized AI-powered application that helps users understand Connecticut General Statutes. This tool retrieves relevant legal information from Connecticut statutes and provides accurate, source-cited responses.

## Features

- Retrieves relevant legal information from Connecticut General Statutes
- Provides accurate responses based on official legal sources
- Cites specific sections and includes links to official documentation
- Maintains conversation history for contextual understanding

## Setup

### Prerequisites

- Python 3.8 or higher
- Pinecone account with an existing index
- Google AI API key
- Groq API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/connecticut-legal-assistant.git
cd connecticut-legal-assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
GOOGLE_API_KEY=your_google_api_key
PINECONE_API_KEY=your_pinecone_api_key
GROQ_API_KEY=your_groq_api_key
PINECONE_INDEX_NAME=connecticut-legal-assistant
PINECONE_NAMESPACE=legal-sections
```

### Running the application

Start the Streamlit app:
```bash
streamlit run app.py
```

## Usage

1. Click the "Initialize System" button in the sidebar to connect to the Pinecone vectorstore.
2. Type your legal question in the chat input at the bottom of the screen.
3. Receive answers based on the Connecticut General Statutes with proper citations.

## Disclaimer

This tool provides legal information, not legal advice. For specific legal problems, consult a licensed attorney.

## License

[MIT License](LICENSE)