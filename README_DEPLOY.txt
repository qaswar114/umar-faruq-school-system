
UMAR FARUQ INTEGRATED ACADEMY - RENDER READY PACKAGE

Local test:
1. Install Python
2. Open terminal in this folder
3. Run: pip install -r requirements.txt
4. Run: python app.py
5. Open: http://127.0.0.1:5000

Default logins:
Admin: admin / admin123
Registrar: registrar / reg123
Bursar: bursar / bursar123

Render deployment:
1. Upload this folder to a GitHub repository.
2. Create a new Web Service on Render.
3. Connect the GitHub repository.
4. Build command: pip install -r requirements.txt
5. Start command: gunicorn app:app
6. Add environment variable:
   SECRET_KEY = any long random text
7. Add PostgreSQL database and copy its DATABASE_URL into the Web Service environment variables.
8. Deploy.

Logo:
- static/logo.png
- Displayed at 90 degrees clockwise in login, header, receipts, and statements.
