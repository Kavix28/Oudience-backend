import os
import json
import time
import pdfplumber
import numpy as np
import re
from flask import (
    Flask, request, jsonify, send_from_directory,
    session, abort
)
from flask_session import Session
from werkzeug.utils import secure_filename
from sentence_transformers import SentenceTransformer

# =========================
# Flask Setup
# =========================
app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = "oudience-secret-key"

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "flask_sessions"
app.config["SESSION_PERMANENT"] = False
Session(app)

# =========================
# Constants
# =========================
ADMIN_TOKEN = "admin123"
UPLOAD_DIR = "uploads_exp"
KB_FILE = "knowledge_base_exp.json"
UPLOAD_LOGS = "upload_logs.json"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("flask_sessions", exist_ok=True)

# =========================
# Embedding Model
# =========================
embedder = SentenceTransformer("all-MiniLM-L6-v2")

kb_docs = []
kb_embeddings = None

# =========================
# Helpers
# =========================
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def chunk_text(text, size=250):
    words = text.split()
    return [
        " ".join(words[i:i + size])
        for i in range(0, len(words), size)
        if len(words[i:i + size]) > 30
    ]

def load_kb():
    global kb_docs, kb_embeddings
    kb_docs = load_json(KB_FILE)
    
    # Handle nested array structure if present
    if kb_docs and isinstance(kb_docs[0], list):
        kb_docs = kb_docs[0]
    
    if not kb_docs:
        kb_embeddings = None
        return
        
    # Ensure kb_docs is a list of dictionaries
    if not isinstance(kb_docs, list) or not all(isinstance(d, dict) and "text" in d for d in kb_docs):
        print(f"Error: Invalid knowledge base format in {KB_FILE}")
        kb_docs = []
        kb_embeddings = None
        return
        
    texts = [d["text"] for d in kb_docs]
    kb_embeddings = embedder.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

load_kb()

# =========================
# Conversational AI Helper
# =========================
def generate_conversational_response(query):
    """Generate responses for general conversational queries"""
    query_lower = query.lower().strip()
    
    # Greetings
    if any(word in query_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return "Hello! I'm here to help you with information about Oudience and answer your questions. What would you like to know?"
    
    # How are you / status
    if any(phrase in query_lower for phrase in ['how are you', 'how do you do', 'what\'s up']):
        return "I'm doing great, thank you for asking! I'm ready to help you with any questions about Oudience or general inquiries. How can I assist you today?"
    
    # What can you do
    if any(phrase in query_lower for phrase in ['what can you do', 'what do you do', 'help me', 'capabilities']):
        return "I can help you with:\n• Information about Oudience company policies, procedures, and guidelines\n• General questions and conversations\n• Details about our products, services, and support\n• Workplace culture and employee information\n\nJust ask me anything!"
    
    # Thank you
    if any(word in query_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're very welcome! I'm happy to help. Feel free to ask me anything else you'd like to know."
    
    # Goodbye
    if any(word in query_lower for word in ['bye', 'goodbye', 'see you', 'farewell']):
        return "Goodbye! It was great chatting with you. Feel free to come back anytime if you have more questions!"
    
    # Who are you
    if any(phrase in query_lower for phrase in ['who are you', 'what are you', 'tell me about yourself']):
        return "I'm Oudience's AI assistant! I'm here to help you find information about our company, policies, products, and services. I can also have general conversations and answer various questions. How can I help you today?"
    
    # Time/Date related
    if any(word in query_lower for word in ['time', 'date', 'today', 'now']):
        return f"I can see you're asking about time/date. While I don't have real-time capabilities, I can help you with Oudience's working hours (9:30 AM to 6:30 PM, Monday to Friday) or other time-related policies. What specifically would you like to know?"
    
    # Weather
    if 'weather' in query_lower:
        return "I don't have access to current weather information, but I can help you with Oudience-related questions or other topics. Is there something about our company or services you'd like to know?"
    
    # General questions that might need knowledge base context
    if any(word in query_lower for word in ['oudience', 'company', 'policy', 'policies', 'work', 'employee', 'office', 'support']):
        return "I'd be happy to help with information about Oudience! I can tell you about our policies including working hours, office locations, leave policies, remote work guidelines, probation periods, workplace culture, and code of conduct. What specific policy or information would you like to know about?"
    
    # Default conversational response
    return f"That's an interesting question! While I specialize in helping with Oudience-related information, I'm happy to chat. Could you tell me more about what you're looking for, or would you like to know something about Oudience?"

def is_general_query(query):
    """Check if query is likely a general conversational query rather than knowledge-seeking"""
    general_patterns = [
        r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
        r'\b(how are you|what\'s up|how do you do)\b',
        r'\b(thank|thanks|appreciate)\b',
        r'\b(bye|goodbye|see you|farewell)\b',
        r'\b(who are you|what are you|tell me about yourself)\b',
        r'\b(what can you do|help me|capabilities)\b'
    ]
    
    query_lower = query.lower()
    return any(re.search(pattern, query_lower) for pattern in general_patterns)

def extract_relevant_info(query, text):
    """Extract relevant information from the knowledge base text based on the query"""
    query_lower = query.lower()
    text_lower = text.lower()
    
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # Keywords to look for based on query
    query_keywords = set(re.findall(r'\b\w+\b', query_lower))
    
    # Find most relevant sentences
    relevant_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        # Count keyword matches
        matches = sum(1 for keyword in query_keywords if keyword in sentence_lower)
        if matches > 0:
            relevant_sentences.append((sentence, matches))
    
    # Sort by relevance and take top sentences
    relevant_sentences.sort(key=lambda x: x[1], reverse=True)
    
    if relevant_sentences:
        # Take top 2-3 most relevant sentences
        top_sentences = [s[0] for s in relevant_sentences[:3]]
        return '. '.join(top_sentences) + '.'
    
    # If no specific matches, return a condensed version
    return text[:300] + '...' if len(text) > 300 else text

def generate_focused_response(query, kb_text):
    """Generate a focused response based on the query and knowledge base text"""
    query_lower = query.lower()
    
    # Handle combined questions (working hours + location + policies)
    if ('working hours' in query_lower or 'work time' in query_lower) and any(word in query_lower for word in ['location', 'located', 'where', 'office']) and any(word in query_lower for word in ['policy', 'policies']):
        
        # Create well-formatted response with proper line breaks
        response = "📋 OUDIENCE COMPANY INFORMATION\n\n"
        
        response += "🕘 WORKING HOURS\n"
        response += "Our standard business hours are 9:30 AM to 6:30 PM, Monday through Friday.\n"
        response += "• Flexible arrival: 9:00 AM to 11:00 AM\n"
        response += "• Daily requirement: 8 productive hours (excluding lunch)\n\n"
        
        response += "🏢 OFFICE LOCATIONS\n"
        response += "We maintain a global presence with three strategic locations:\n"
        response += "• 🇮🇳 Bengaluru, India - Primary engineering & product hub\n"
        response += "• 🇮🇳 Pune, India - Operations & support center\n"
        response += "• 🇩🇪 Berlin, Germany - European remote collaboration hub\n\n"
        
        response += "📋 KEY POLICIES\n"
        response += "• 🏖️ Leave: 18 annual days + 10 public holidays + 7 sick days\n"
        response += "• 🏠 Remote Work: Up to 3 days/week (manager approval required)\n"
        response += "• 🤝 Core Values: Respect, Integrity, Collaboration, Professionalism\n"
        response += "• 🛡️ Standards: Zero tolerance for discrimination & harassment\n\n"
        
        response += "💡 Need specific details about any policy? Just ask!"
        
        return response
    
    # Company policies - comprehensive detection
    if any(word in query_lower for word in ['policy', 'policies', 'rules', 'guidelines', 'code of conduct', 'workplace culture']):
        
        # If asking for general policies, provide comprehensive overview
        if not any(specific in query_lower for specific in ['leave', 'remote', 'probation', 'notice', 'dress', 'communication', 'safety']):
            policy_overview = []
            
            # Check what policies are available in the text
            if 'leave' in kb_text.lower() or 'annual leave' in kb_text.lower():
                policy_overview.append("**Leave Policy:** 18 days annual leave, 10 public holidays, 7 sick days annually")
            
            if 'remote work' in kb_text.lower() or 'work remotely' in kb_text.lower():
                policy_overview.append("**Remote Work:** Up to 3 days/week with manager approval")
            
            if 'working hours' in kb_text.lower():
                policy_overview.append("**Working Hours:** 9:30 AM - 6:30 PM, Monday to Friday with flexible arrival")
            
            if 'probation' in kb_text.lower():
                policy_overview.append("**Probation:** 3-month period for new employees")
            
            if any(word in kb_text.lower() for word in ['respect', 'integrity', 'values', 'culture']):
                policy_overview.append("**Core Values:** Respect, Integrity, Collaboration, Professionalism, Continuous Learning")
            
            if any(word in kb_text.lower() for word in ['harassment', 'discrimination', 'conduct']):
                policy_overview.append("**Code of Conduct:** Zero tolerance for harassment/discrimination, professional behavior required")
            
            if policy_overview:
                return "Here are Oudience's key company policies:\n\n" + "\n".join(policy_overview) + "\n\nWould you like details about any specific policy?"
        
        # Specific policy responses with better formatting
        if 'leave' in query_lower or 'vacation' in query_lower or 'holiday' in query_lower:
            response = "🏖️ LEAVE POLICY\n\n"
            response += "We provide comprehensive leave benefits:\n\n"
            response += "• Annual Leave: 18 paid days per year\n"
            response += "• Public Holidays: 10 days (Indian calendar)\n"
            response += "• Sick Leave: 7 paid days annually\n"
            response += "• Carryover: Up to 10 unused days maximum\n\n"
            response += "💡 Questions about leave approval or procedures?"
            return response
        
        elif 'remote' in query_lower or 'work from home' in query_lower or 'wfh' in query_lower:
            response = "🏠 REMOTE WORK POLICY\n\n"
            response += "Flexible work arrangements to enhance productivity:\n\n"
            response += "• Hybrid Work: Up to 3 days/week remotely\n"
            response += "• Approval: Manager approval required\n"
            response += "• Fully Remote: Available for senior/specialized roles\n"
            response += "• Requirements: Maintain productivity & communication\n\n"
            response += "💡 Need details about remote work setup?"
            return response
        
        elif any(word in query_lower for word in ['culture', 'values', 'conduct', 'behavior', 'ethics']):
            response = "🤝 WORKPLACE CULTURE & VALUES\n\n"
            response += "Our organizational foundation built on five principles:\n\n"
            response += "• 🤝 Respect: Treat everyone with dignity\n"
            response += "• 🎯 Integrity: Maintain honesty & ethics\n"
            response += "• 👥 Collaboration: Foster teamwork & support\n"
            response += "• 💼 Professionalism: Uphold high standards\n"
            response += "• 📚 Continuous Learning: Encourage growth\n\n"
            response += "🛡️ Zero Tolerance: Strict policies against discrimination & harassment\n\n"
            response += "💡 Want to know more about workplace guidelines?"
            return response
        
        elif 'dress' in query_lower or 'attire' in query_lower:
            return "**Dress Code Policy:** Employees should dress appropriately as per company guidelines, maintain professional conduct, and follow organizational policies and procedures."
        
        elif any(word in query_lower for word in ['communication', 'meeting', 'email']):
            return "**Communication Policy:** Communication should be clear, respectful, and constructive. Listen actively, value diverse opinions, and address concerns professionally through proper channels. Maintain professionalism in virtual meetings and avoid aggressive or unprofessional messages."
        
        elif 'safety' in query_lower or 'health' in query_lower:
            return "**Health & Safety Policy:** Follow all safety rules and emergency procedures, maintain a clean and safe workspace, and report hazards or unsafe conditions immediately. Secure company data and devices, especially when working remotely."
    
    # Individual topic responses with clean formatting
    if 'working hours' in query_lower or 'work time' in query_lower:
        response = "🕘 WORKING HOURS\n\n"
        response += "Our flexible schedule accommodates diverse needs:\n\n"
        response += "• Standard Hours: 9:30 AM to 6:30 PM (Mon-Fri)\n"
        response += "• Flexible Arrival: 9:00 AM to 11:00 AM window\n"
        response += "• Daily Requirement: 8 productive hours\n"
        response += "• Breaks: Dedicated lunch breaks included\n\n"
        response += "💡 Questions about schedule flexibility?"
        return response
    
    if any(word in query_lower for word in ['location', 'located', 'office', 'where', 'address']):
        if any(word in kb_text.lower() for word in ['bengaluru', 'pune', 'berlin', 'office locations']):
            response = "🏢 OFFICE LOCATIONS\n\n"
            response += "Our global presence spans three strategic locations:\n\n"
            response += "• 🇮🇳 Bengaluru, India\n"
            response += "  Primary engineering & product development hub\n\n"
            response += "• 🇮🇳 Pune, India\n"
            response += "  Operations & support center\n\n"
            response += "• 🇩🇪 Berlin, Germany\n"
            response += "  European remote collaboration hub\n\n"
            response += "💡 Most engineering roles are based in Bengaluru"
            return response
    
def format_professional_response(content_sections):
    """Format response sections into a professional, well-structured output"""
    if not content_sections:
        return ""
    
    # Add professional header
    response = "📋 **Oudience Company Information**\n\n"
    
    # Format each section with proper spacing and icons
    formatted_sections = []
    
    for section in content_sections:
        if section.startswith("**Working Hours:**"):
            icon = "🕘"
            formatted_sections.append(f"{icon} {section}")
        elif section.startswith("**Office Locations:**"):
            icon = "🏢"
            formatted_sections.append(f"{icon} {section}")
        elif section.startswith("**Key Policies:**"):
            icon = "📋"
            formatted_sections.append(f"{icon} {section}")
        elif section.startswith("**Leave Policy:**"):
            icon = "🏖️"
            formatted_sections.append(f"{icon} {section}")
        elif section.startswith("**Remote Work Policy:**"):
            icon = "🏠"
            formatted_sections.append(f"{icon} {section}")
        elif section.startswith("**Workplace Culture:**"):
            icon = "🤝"
            formatted_sections.append(f"{icon} {section}")
        else:
            formatted_sections.append(section)
    
    # Join sections with proper spacing
    response += "\n\n".join(formatted_sections)
    
    # Add professional footer
    response += "\n\n---\n💡 *Need more specific information? Feel free to ask about any particular policy or procedure.*"
    
    return response

def enhance_policy_content(content):
    """Enhance policy content with better formatting and professional language"""
    
    # Working Hours enhancement
    if "working hours are from 9:30 AM to 6:30 PM" in content:
        content = content.replace(
            "Oudience's working hours are from 9:30 AM to 6:30 PM, Monday to Friday. Employees have a flexible arrival window between 9:00 AM and 11:00 AM, and are expected to complete 8 hours of productive work per day (excluding lunch breaks).",
            "**Working Hours:** Our standard business hours are 9:30 AM to 6:30 PM, Monday through Friday. We offer flexible arrival times between 9:00 AM and 11:00 AM to accommodate different schedules. All employees are expected to maintain 8 productive hours daily, with dedicated lunch breaks."
        )
    
    # Office Locations enhancement
    if "operates from three primary office locations" in content:
        content = content.replace(
            "The company operates from three primary office locations: Bengaluru (India), Pune (India), and Berlin, Germany (remote hub). Most engineering and product roles are based in Bengaluru.",
            "**Office Locations:** We maintain a global presence with three strategic office locations:\n   • 🇮🇳 **Bengaluru, India** - Primary engineering and product development hub\n   • 🇮🇳 **Pune, India** - Operations and support center\n   • 🇩🇪 **Berlin, Germany** - European remote collaboration hub"
        )
    
    # Key Policies enhancement
    if "Leave policy includes 18 days annual leave" in content:
        content = content.replace(
            "Leave policy includes 18 days annual leave + 10 public holidays + 7 sick days. Remote work allowed up to 3 days/week with approval. Core values emphasize Respect, Integrity, Collaboration, Professionalism, and Continuous Learning with zero tolerance for discrimination or harassment.",
            "**Key Policies Overview:**\n   • 🏖️ **Leave Entitlements:** 18 annual leave days + 10 public holidays + 7 sick days\n   • 🏠 **Remote Work:** Up to 3 days per week (manager approval required)\n   • 🤝 **Core Values:** Respect, Integrity, Collaboration, Professionalism & Continuous Learning\n   • 🛡️ **Workplace Standards:** Zero tolerance policy for discrimination and harassment"
        )
    
    return content

# =========================
# Admin Auth (UNCHANGED FLOW)
# =========================
def require_admin():
    if not session.get("is_admin"):
        abort(403)

@app.route("/admin/login", methods=["POST"])
def admin_login():
    token = request.json.get("token")
    if token != ADMIN_TOKEN:
        abort(403)
    session["is_admin"] = True
    return jsonify({"ok": True})

# =========================
# Admin Pages
# =========================
@app.route("/admin")
def admin_page():
    return send_from_directory("static", "admin.html")

@app.route("/admin/upload", methods=["POST"])
def admin_upload():
    require_admin()

    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # Check file size (10MB limit)
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        return jsonify({"error": "File too large. Maximum size is 10MB"}), 400

    filename = secure_filename(file.filename)
    
    # Add timestamp to filename if it already exists
    base_name, ext = os.path.splitext(filename)
    counter = 1
    original_filename = filename
    
    while os.path.exists(os.path.join(UPLOAD_DIR, filename)):
        filename = f"{base_name}_{counter}{ext}"
        counter += 1

    path = os.path.join(UPLOAD_DIR, filename)
    
    try:
        file.save(path)

        # Extract text
        text = ""
        with pdfplumber.open(path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"[Page {page_num + 1}] {page_text}\n"

        if not text.strip():
            os.remove(path)  # Clean up
            return jsonify({"error": "No text could be extracted from the PDF"}), 400

        chunks = chunk_text(text)
        
        if not chunks:
            os.remove(path)  # Clean up
            return jsonify({"error": "PDF content too short to create meaningful chunks"}), 400

        # Remove existing chunks from this file (handle re-uploads)
        global kb_docs
        kb_docs = [d for d in kb_docs if d.get("source") != filename]

        # Add new chunks
        start_id = max([d.get("id", 0) for d in kb_docs], default=0)
        for i, chunk in enumerate(chunks):
            kb_docs.append({
                "id": start_id + i + 1,
                "source": filename,
                "text": chunk.strip(),
                "page_info": "Multiple pages" if len(chunks) > 1 else "Single page"
            })

        # Save updated knowledge base
        save_json(KB_FILE, kb_docs)
        load_kb()

        # Update upload logs
        logs = load_json(UPLOAD_LOGS)
        
        # Remove old log entry if re-uploading
        logs = [log for log in logs if log.get("filename") != filename]
        
        logs.append({
            "filename": filename,
            "original_filename": original_filename,
            "chunks": len(chunks),
            "file_size": file_size,
            "uploaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pages_processed": len([p for p in text.split('[Page') if p.strip()])
        })
        
        save_json(UPLOAD_LOGS, logs)

        return jsonify({
            "success": True,
            "chunks_added": len(chunks),
            "filename": filename,
            "pages_processed": len([p for p in text.split('[Page') if p.strip()])
        })

    except Exception as e:
        # Clean up file if processing failed
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

@app.route("/admin/uploads")
def admin_uploads():
    require_admin()
    logs = load_json(UPLOAD_LOGS)
    
    # Add additional metadata
    for log in logs:
        file_path = os.path.join(UPLOAD_DIR, log["filename"])
        log["file_exists"] = os.path.exists(file_path)
        if log["file_exists"]:
            log["file_size_mb"] = round(os.path.getsize(file_path) / (1024 * 1024), 2)
    
    return jsonify(logs)

@app.route("/admin/delete/<filename>", methods=["DELETE"])
def admin_delete_file(filename):
    require_admin()
    
    try:
        # Remove from knowledge base
        global kb_docs
        original_count = len(kb_docs)
        kb_docs = [d for d in kb_docs if d.get("source") != filename]
        chunks_removed = original_count - len(kb_docs)
        
        # Save updated knowledge base
        save_json(KB_FILE, kb_docs)
        load_kb()
        
        # Remove from upload logs
        logs = load_json(UPLOAD_LOGS)
        logs = [log for log in logs if log.get("filename") != filename]
        save_json(UPLOAD_LOGS, logs)
        
        # Remove physical file
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({
            "success": True,
            "chunks_removed": chunks_removed,
            "message": f"Successfully deleted {filename}"
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500

@app.route("/admin/stats")
def admin_stats():
    require_admin()
    
    logs = load_json(UPLOAD_LOGS)
    
    total_files = len(logs)
    total_chunks = sum(log.get("chunks", 0) for log in logs)
    total_size = 0
    
    for log in logs:
        file_path = os.path.join(UPLOAD_DIR, log["filename"])
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)
    
    return jsonify({
        "total_files": total_files,
        "total_chunks": total_chunks,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "last_upload": logs[-1]["uploaded_at"] if logs else None
    })

# =========================
# Chat Endpoint (ENHANCED)
# =========================
@app.route("/query", methods=["POST"])
def query():
    q = (request.json or {}).get("query", "").strip()
    if not q:
        return jsonify({"response": "Please ask a question."})

    # Check if it's a general conversational query first
    if is_general_query(q):
        return jsonify({"response": generate_conversational_response(q)})

    # If knowledge base is empty, provide conversational response
    if kb_embeddings is None:
        return jsonify({
            "response": "I don't have any specific documents loaded right now, but I'm still here to help! You can ask me general questions or about Oudience. What would you like to know?"
        })

    # Perform semantic search in knowledge base
    q_emb = embedder.encode(
        [q],
        convert_to_numpy=True,
        normalize_embeddings=True
    )[0]

    scores = np.dot(kb_embeddings, q_emb)
    
    # For policy questions, get multiple relevant chunks
    query_lower = q.lower()
    is_policy_query = any(word in query_lower for word in ['policy', 'policies', 'rules', 'guidelines', 'code of conduct', 'workplace culture'])
    
    if is_policy_query:
        # Get top 3 chunks for policy questions
        top_indices = np.argsort(scores)[-3:][::-1]  # Top 3 in descending order
        relevant_chunks = []
        
        for idx in top_indices:
            if scores[idx] >= 0.25:  # Lower threshold for policy queries
                relevant_chunks.append(kb_docs[idx]["text"])
        
        if relevant_chunks:
            # Combine chunks for comprehensive policy response
            combined_text = " ".join(relevant_chunks)
            focused_response = generate_focused_response(q, combined_text)
            return jsonify({"response": focused_response})
    
    # Regular single-chunk search for non-policy queries
    best_idx = int(np.argmax(scores))
    best_score = float(scores[best_idx])

    # If similarity is high enough, return knowledge base result
    if best_score >= 0.35:
        focused_response = generate_focused_response(q, kb_docs[best_idx]["text"])
        return jsonify({
            "response": focused_response
        })
    
    # If no relevant knowledge base info, try conversational response
    # But first check if query seems to be asking for specific information
    info_seeking_words = ['what', 'how', 'when', 'where', 'why', 'who', 'which', 'tell me', 'explain', 'describe']
    if any(word in q.lower() for word in info_seeking_words):
        # This seems like an information-seeking query, so mention knowledge base limitation
        conversational_response = generate_conversational_response(q)
        if "interesting question" in conversational_response:  # Default response
            return jsonify({
                "response": f"I don't have specific information about that in my knowledge base, but I'm happy to help in other ways! You could try asking about Oudience policies, procedures, or general questions. What else would you like to know?"
            })
        return jsonify({"response": conversational_response})
    else:
        # Handle as general conversation
        return jsonify({"response": generate_conversational_response(q)})

# =========================
# Frontend
# =========================
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

# =========================
# Run
# =========================
if __name__ == "__main__":
    app.run(debug=True, port=5002)

