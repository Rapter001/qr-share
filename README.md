# QR Share App

A Flask web application for uploading files and generating QR codes for easy sharing. Features user authentication, responsive design, and file management.

## Features

- **File Upload**: Upload PNG, JPG, JPEG, and PDF files
- **QR Code Generation**: Automatic QR code generation for each uploaded file
- **User Authentication**: Login system with environment-based credentials
- **File Gallery**: Browse all uploaded files with previews
- **File Deletion**: Authenticated users can delete files
- **Responsive Design**: Works on mobile, tablet, laptop, and desktop
- **Docker Support**: Easy deployment with Docker

## Setup

### Local Development

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env` file and update credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
4. Run the application:
   ```bash
   python main.py
   ```
5. Open http://localhost:5000 in your browser

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t qr-share .
   ```
2. Run the container:
   ```bash
   docker run -p 5000:5000 \
     -e APP_USERNAME=your_username \
     -e APP_PASSWORD=your_password \
     -e SECRET_KEY=your_secret_key \
     qr-share
   ```

## Environment Variables

- `APP_USERNAME`: Admin username (default: admin)
- `APP_PASSWORD`: Admin password (default: changeme123)
- `SECRET_KEY`: Flask session secret key (change in production)

## Routes

- `/` - File gallery (public)
- `/login` - Login page
- `/uploads` - File upload page (requires login)
- `/upload` - File upload handler (POST, requires login)
- `/delete/<filename>` - Delete file (POST, requires login)
- `/logout` - Logout

## File Structure

```
qr-share/
├── main.py                 # Flask application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── .env                   # Environment variables
├── templates/             # HTML templates
│   ├── index.html         # Gallery page
│   ├── login.html         # Login page
│   ├── uploads.html       # Upload page
│   └── result.html        # Upload result page
└── static/                # Static files
    ├── css/
    │   └── styles.css     # Stylesheet
    ├── uploads/           # Uploaded files
    └── qr/                # Generated QR codes
```

## Security Notes

- Change default credentials in production
- Use a strong SECRET_KEY
- The app stores files in the local filesystem
- Consider using a proper file storage service for production

## License

MIT License