from dotenv import load_dotenv

load_dotenv()  # must run before create_app() so OPENAI_API_KEY is in os.environ

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
