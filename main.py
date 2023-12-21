from flask import Flask
from WEBSITE import create_app

app = Flask(__name__, static_url_path='/static')
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
