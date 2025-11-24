# 🌟 Nia Learning Assistant

> A COPPA-compliant AI learning assistant that makes education accessible, transparent, and personalized for every K-12 student.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Deployment: Railway](https://img.shields.io/badge/Deployed%20on-Railway-blueviolet.svg)](https://railway.app/)

## 🎯 What Makes Nia Different?

Unlike traditional AI tutors, Nia:

- **📚 Uses Curated Content** - Prioritizes verified curriculum materials over general knowledge
- **🔍 Shows Its Sources** - "From our curriculum" vs "From what I know" transparency
- **📁 Auto-Organizes** - Conversations automatically sorted by subject (Math, Science, etc.)
- **🌈 Inclusive by Design** - Built-in accommodations for autism, dyslexia, ADHD, and more
- **🔒 COPPA Compliant** - Parent-controlled accounts with comprehensive safety features

## ✨ Key Features

### For Students
- 🎓 **3-Level Depth Tutoring** - Progressively deeper explanations based on engagement
- 🌍 **Bilingual Support** - English and Spanish
- 🎯 **Grade-Appropriate** - Content matched to student's grade level (K-12)
- 💬 **Natural Conversations** - Ask questions in your own words
- 🏆 **Source Attribution** - Always know where information comes from

### For Parents
- 👨‍👩‍👧‍👦 **Parent Dashboard** - Monitor learning activity and progress
- 🔐 **Full Control** - Manage child accounts, set preferences
- 📊 **Usage Analytics** - Track engagement and learning patterns
- 🛡️ **Safety First** - Content filtering and activity logs
- ✅ **COPPA Compliant** - Built with child privacy regulations in mind

### For Educators
- 📚 **Curriculum-Aligned** - Uses Common Core standards
- 📝 **Conversation History** - Review student questions and understanding
- 🎯 **Learning Insights** - See which topics need reinforcement
- 🔧 **Customizable** - Add your own curriculum content

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL
- Anthropic API key

### Installation
```bash
# Clone the repository
git clone https://github.com/yourusername/nia-learning-assistant.git
cd nia-learning-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Run database migrations (automatic on startup)
# Add educational content (automatic on startup)

# Start the server
uvicorn main:app --reload
```

### Environment Variables
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/nia
ANTHROPIC_API_KEY=your_api_key_here
JWT_SECRET_KEY=your_secret_key_here
```

## 📚 Educational Content Library

Nia currently includes 8 comprehensive curriculum documents:

### Mathematics
- Understanding Fractions (Grades 3-5)
- Multiplication Tables (Grades 2-4)

### Science
- Photosynthesis: How Plants Make Food (Grades 3-5)
- The Water Cycle (Grades 3-5)

### History
- The American Revolution (Grades 4-5)
- George Washington: Father of Our Country (Grades 3-5)

### English Language Arts
- Parts of Speech (Grades 3-5)
- Types of Sentences (Grades 3-5)

### Geography
- United States: States and Regions (Grades 3-5)
- World Geography: Continents and Oceans (Grades 3-5)

**Want to add more content?** Just add markdown files to `educational_content/` and they'll be automatically ingested!

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Parent Dashboard (Web)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     Auth     │  │ Conversation │  │   Dashboard   │     │
│  │   Service    │  │   Service    │  │   Service     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                              │                               │
│                    ┌─────────▼──────────┐                   │
│                    │   RAG Service       │                   │
│                    │ (Content Retrieval) │                   │
│                    └─────────┬──────────┘                   │
└──────────────────────────────┼───────────────────────────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                              ▼
        ┌───────────────┐            ┌──────────────────┐
        │  PostgreSQL   │            │  Anthropic API   │
        │   Database    │            │ (Claude Sonnet)  │
        └───────────────┘            └──────────────────┘
```

## 📖 API Documentation

Once running, visit:
- **Interactive docs**: http://localhost:8000/docs
- **OpenAPI spec**: http://localhost:8000/openapi.json

### Example API Usage

**Create a child profile:**
```bash
curl -X POST "http://localhost:8000/api/v1/children/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Alex",
    "grade_level": "3rd grade",
    "preferred_language": "en"
  }'
```

**Ask a question:**
```bash
curl -X POST "http://localhost:8000/api/v1/conversation/message" \
  -H "Content-Type: application/json" \
  -d '{
    "child_id": 1,
    "text": "How do I add fractions?",
    "current_depth": 1
  }'
```

## 🧪 Testing
```bash
# Run all tests
python test_nia_features.py

# Test content library specifically
python test_content_library.py

# Test RAG search
python test_rag_search.py
```

## 🛣️ Roadmap

### Phase 1: Core Enhancements ✅ (Current)
- [x] Authentication system
- [x] Educational content library
- [x] RAG with source attribution
- [x] Auto-folder categorization
- [x] 3-level depth system
- [ ] Expand content library to 50+ documents

### Phase 2: Parent Dashboard (Next 4-8 weeks)
- [ ] React frontend application
- [ ] Real-time activity monitoring
- [ ] Usage analytics dashboard
- [ ] Notification system

### Phase 3: Advanced Features (Weeks 9-16)
- [ ] Voice interaction support
- [ ] Image understanding (homework help)
- [ ] Gamification and badges
- [ ] Progress tracking visualization

### Phase 4: Launch (Weeks 17-22)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Beta testing program
- [ ] Public launch

## 🔒 Security & Privacy

Nia takes child safety seriously:

- ✅ **COPPA Compliant** - Built following Children's Online Privacy Protection Act
- ✅ **Parent Consent** - Parents must create and control child accounts
- ✅ **Audit Logging** - All interactions are logged for safety
- ✅ **Content Filtering** - Age-appropriate content only
- ✅ **Secure Authentication** - JWT tokens, password hashing
- ✅ **Data Privacy** - No data sold or shared with third parties

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Adding Educational Content

1. Create markdown file in `educational_content/[subject]/[grade_level]/`
2. Follow the existing format (see examples)
3. Content will auto-ingest on next deployment
4. Test with `python scripts/ingest_content.py`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Built with:
- [Anthropic Claude](https://www.anthropic.com/) - AI model
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [PostgreSQL](https://www.postgresql.org/) - Database
- [Railway](https://railway.app/) - Deployment platform
- Love for education and children's learning ❤️

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/nia-learning-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/nia-learning-assistant/discussions)
- **Email**: your.email@example.com

## 🌟 Star History

If you find Nia helpful, please consider giving it a star! ⭐

---

**Built with ❤️ for children's education**

*Nia - Making AI-powered learning safe, effective, and accessible for every child.*
