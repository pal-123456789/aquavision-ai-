import os
from src import create_app
app = create_app()

# Add health check endpoint
@app.route('/health')
def health_check():
    return 'OK', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))