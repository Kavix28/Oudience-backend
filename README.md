# 🤖 Oudience AI Assistant

An enterprise-grade RAG (Retrieval-Augmented Generation) chatbot system built with Flask that provides intelligent responses about company policies, procedures, and general information.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 🤖 **AI-Powered Conversations** - Natural language understanding with semantic search
- 📄 **PDF Document Processing** - Automatic text extraction and intelligent chunking
- 🔍 **Semantic Search** - Uses sentence transformers for accurate information retrieval
- 👨‍💼 **Admin Dashboard** - Professional interface for document management
- 🎨 **Modern UI** - Responsive design with dark mode support
- 💬 **Multi-PDF Support** - Handle multiple documents simultaneously
- 🛡️ **Secure Authentication** - Session-based admin access

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/oudience-ai-assistant.git
cd oudience-ai-assistant
```

2. **Create virtual environment**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure the application**

Edit `app.py` and change the admin token:
```python
ADMIN_TOKEN = "your-secure-token-here"  # Change this!
```

5. **Run the application**
```bash
python app.py
```

6. **Access the application**
- User Interface: http://localhost:5002/
- Admin Dashboard: http://localhost:5002/admin

## 📖 Usage

### For Users

1. Open http://localhost:5002/ in your browser
2. Type your question in the chat interface
3. Get instant AI-powered responses about company policies

**Example queries:**
- "What are the working hours?"
- "Tell me about the leave policy"
- "Where are the office locations?"
- "What are the company values?"

### For Administrators

1. Navigate to http://localhost:5002/admin
2. Enter admin token (default: `admin123` - **change this!**)
3. Upload PDF documents via drag-and-drop or file picker
4. Manage uploaded documents and view statistics

## 🏗️ Architecture

### Technology Stack

**Backend:**
- Flask - Web framework
- Sentence Transformers - Semantic embeddings (all-MiniLM-L6-v2)
- PDFPlumber - PDF text extraction
- NumPy - Vector operations

**Frontend:**
- Vanilla JavaScript
- Font Awesome icons
- Google Fonts (Inter)
- Modern CSS3

**Storage:**
- JSON files for knowledge base
- Filesystem for PDFs and sessions

### How It Works

1. **Document Upload**: PDFs are uploaded and processed into 250-word chunks
2. **Embedding Generation**: Each chunk is converted to vector embeddings
3. **Query Processing**: User queries are encoded and matched against embeddings
4. **Semantic Search**: Cosine similarity finds the most relevant information
5. **Response Generation**: Focused, professional responses are formatted and returned

## 📁 Project Structure

```
oudience-ai-assistant/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── CODEBASE_DOCUMENTATION.md   # Detailed technical docs
├── .gitignore                  # Git ignore rules
│
├── static/                     # Frontend files
│   ├── index.html             # User chat interface
│   └── admin.html             # Admin dashboard
│
├── uploads_exp/               # Uploaded PDFs (gitignored)
├── flask_sessions/            # Session data (gitignored)
└── data/                      # Data directories
    ├── processed/
    └── raw/
```

## 🔧 Configuration

### Environment Variables

You can configure the application by editing these constants in `app.py`:

```python
ADMIN_TOKEN = "admin123"           # Admin authentication token
UPLOAD_DIR = "uploads_exp"         # PDF storage directory
KB_FILE = "knowledge_base_exp.json" # Knowledge base file
PORT = 5002                        # Application port
```

### Similarity Thresholds

Adjust search sensitivity in `app.py`:

```python
# For policy queries (multi-chunk)
if scores[idx] >= 0.25:  # Lower threshold for broader results

# For specific queries (single-chunk)
if best_score >= 0.35:   # Higher threshold for precision
```

## 🎨 Screenshots

### User Chat Interface
Modern, responsive chat interface with dark mode support and real-time responses.

### Admin Dashboard
Professional dashboard for managing documents, viewing statistics, and monitoring uploads.

## 🔐 Security

### Important Security Notes

1. **Change the default admin token** in `app.py`
2. Use HTTPS in production
3. Implement rate limiting for API endpoints
4. Add CSRF protection for forms
5. Use environment variables for sensitive data

### Recommended Production Setup

```python
# Use environment variables
import os
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'change-me')

# Use Waitress for production
from waitress import serve
serve(app, host='0.0.0.0', port=5002)
```

## 📊 API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/` | GET | No | User chat interface |
| `/query` | POST | No | Submit chat query |
| `/admin` | GET | Yes | Admin dashboard |
| `/admin/login` | POST | No | Admin authentication |
| `/admin/upload` | POST | Yes | Upload PDF document |
| `/admin/uploads` | GET | Yes | List uploaded files |
| `/admin/delete/<filename>` | DELETE | Yes | Delete document |
| `/admin/stats` | GET | Yes | Get statistics |

## 🐛 Troubleshooting

### Common Issues

**"Knowledge base is empty"**
- Upload PDFs through the admin dashboard
- Check if `knowledge_base_exp.json` exists

**Upload fails**
- Verify file is PDF format
- Check file size is under 10MB
- Ensure sufficient disk space

**Port already in use**
- Change the port in `app.py`
- Or stop the process using port 5002

## 🚀 Deployment

### Production Deployment

1. **Use a production WSGI server** (Waitress is included)
2. **Set up reverse proxy** (Nginx/Apache)
3. **Enable HTTPS** with SSL certificates
4. **Use environment variables** for configuration
5. **Set up monitoring** and logging
6. **Regular backups** of knowledge base

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5002
CMD ["python", "app.py"]
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Sentence Transformers** - For semantic search capabilities
- **PDFPlumber** - For PDF text extraction
- **Flask** - For the web framework
- **Font Awesome** - For beautiful icons

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🔄 Changelog

### Version 1.0.0 (January 2026)
- Initial release
- Multi-PDF support
- Semantic search with sentence transformers
- Professional UI with dark mode
- Admin dashboard with statistics
- Drag-and-drop file upload
- Delete functionality
- Response time tracking

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Conversation history
- [ ] Export chat transcripts
- [ ] Advanced analytics
- [ ] User feedback system
- [ ] API key management
- [ ] Webhook integrations
- [ ] Custom branding options

---

**Made with ❤️ for Oudience**
#   K n o w l e g e b a s e - c h a t b o t  
 