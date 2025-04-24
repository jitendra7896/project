# ChatBot Project Documentation

## 1. Project Overview
This project implements a chatbot system with a frontend and backend architecture. The system allows users to interact with an AI-powered chatbot through a web interface.

## 2. Architecture Diagram
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Frontend       │────▶│  Backend        │────▶│  AI Model       │
│  (React)        │     │  (Python/Node)  │     │  Integration    │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 3. System Components

### Frontend
- Built with React
- Located in `frontend/chatbot-frontend/`
- Provides user interface for chat interactions
- Handles real-time message updates
- Manages user session state

### Backend
- Python-based server (`app.py`)
- Node.js dependencies for additional functionality
- Handles API requests from frontend
- Manages AI model integration
- Environment configuration via `.env`

## 4. Technical Stack

### Frontend Technologies
- React.js
- HTML/CSS
- JavaScript/TypeScript
- Material-UI or Tailwind CSS for enhanced UI
- React Router for navigation
- JWT for authentication

### Backend Technologies
- Python
- Node.js
- Flask (Python web framework)
- Various npm packages (see package.json)
- Google Gemini AI integration
- SQLite/PostgreSQL for user data storage

### Dependencies
- Python requirements listed in `requirements.txt`
- Node.js dependencies in `package.json`
- Google AI SDK for Gemini integration

## 5. Setup Instructions

### Prerequisites
- Python 3.x
- Node.js
- npm

### Installation Steps

1. Backend Setup:
```bash
cd backend
pip install -r requirements.txt
npm install
```

2. Frontend Setup:
```bash
cd frontend/chatbot-frontend
npm install
```

3. Environment Configuration:
- Copy `.env.example` to `.env`
- Configure necessary environment variables

### Running the Application

1. Start Backend:
```bash
cd backend
python app.py
```

2. Start Frontend:
```bash
cd frontend/chatbot-frontend
npm start
```

## 6. API Documentation

### Authentication Endpoints

#### POST /api/auth/login
- Purpose: Admin login
- Request Body:
  ```json
  {
    "username": "admin",
    "password": "password"
  }
  ```
- Response:
  ```json
  {
    "token": "jwt_token",
    "user": {
      "id": 1,
      "username": "admin",
      "role": "admin"
    }
  }
  ```

#### POST /api/auth/change-bot-icon
- Purpose: Update bot icon (admin only)
- Headers:
  ```
  Authorization: Bearer <jwt_token>
  ```
- Request Body:
  ```json
  {
    "icon_url": "https://example.com/new-icon.png"
  }
  ```

### Chat Endpoints

#### POST /api/chat
- Purpose: Send message to chatbot
- Request Body:
  ```json
  {
    "message": "user message",
    "model": "gemini" // Optional: specify AI model
  }
  ```
- Response:
  ```json
  {
    "response": "bot response",
    "model": "gemini",
    "timestamp": "2024-04-04T12:00:00Z"
  }
  ```

## 7. Future Improvements

1. Enhanced AI Model Integration
   - Integration with Google Gemini AI
   - Support for multiple AI models
   - Model selection based on query type
   - Custom model training capabilities

2. User Authentication System
   - Admin dashboard
   - User management
   - Role-based access control
   - Secure password storage
   - Session management

3. Chat History Storage
   - Persistent chat history
   - Export/import functionality
   - Search capabilities
   - Analytics dashboard

4. Multi-language Support
   - Multiple language interfaces
   - Translation capabilities
   - Language detection
   - Regional customization

5. Real-time Analytics Dashboard
   - User engagement metrics
   - Response time tracking
   - Popular queries analysis
   - Performance monitoring

6. Mobile Responsive Design
   - Progressive Web App (PWA) support
   - Mobile-first approach
   - Touch-friendly interface
   - Offline capabilities

7. Voice Input/Output Support
   - Speech-to-text integration
   - Text-to-speech capabilities
   - Voice command support
   - Multiple language voice support

8. Enhanced UI/UX Features
   - Customizable bot appearance
   - Theme customization
   - Dark/Light mode
   - Custom bot icons
   - Animated responses
   - Rich media support
   - Typing indicators
   - Message reactions

## 8. Project Structure
```
ChatBot/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   ├── package.json
│   ├── .env
│   ├── models/
│   │   ├── user.py
│   │   └── chat.py
│   ├── routes/
│   │   ├── auth.py
│   │   └── chat.py
│   └── utils/
│       ├── ai_models.py
│       └── auth.py
└── frontend/
    └── chatbot-frontend/
        ├── src/
        │   ├── components/
        │   │   ├── Chat/
        │   │   ├── Auth/
        │   │   └── Admin/
        │   ├── styles/
        │   └── utils/
        ├── public/
        └── package.json
```

## 9. Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 10. License
[Specify your project's license here]

## 11. Contact Information
[Add contact details for project maintainers] 