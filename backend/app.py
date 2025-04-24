from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token, verify_jwt_in_request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import logging
from pymongo.errors import ConnectionFailure
import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from models.user import User, db
from models.chat import Chat
from utils.ai_models import AIModel
from utils.auth import Auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chatbot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_COOKIE_SECURE'] = False  # Set to True in production
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'
app.config['JWT_ERROR_MESSAGE_KEY'] = 'error'

# Initialize SQLAlchemy
db.init_app(app)

# Initialize MongoDB
try:
    mongodb_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    logger.info(f"Attempting to connect to MongoDB at: {mongodb_uri}")
    mongo_client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Test the connection
    mongo_client.admin.command('ping')
    mongo_db = mongo_client.chatbot_db
    conversations = mongo_db.conversations
    logger.info("Successfully connected to MongoDB")
except ConnectionFailure as e:
    logger.error(f"Could not connect to MongoDB: {e}")
    conversations = None

# Initialize other extensions
jwt = JWTManager(app)
ai_model = AIModel()
socketio = SocketIO(app, cors_allowed_origins="*")

# JWT error handlers
@jwt.unauthorized_loader
def unauthorized_callback(callback):
    logger.error(f"Unauthorized access attempt: {callback}")
    return jsonify({'error': 'Missing or invalid token'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(callback):
    logger.error(f"Invalid token attempt: {callback}")
    return jsonify({'error': 'Invalid token'}), 422

@jwt.expired_token_loader
def expired_token_callback(callback):
    logger.error(f"Expired token attempt: {callback}")
    return jsonify({'error': 'Token has expired'}), 401

# Create database tables
with app.app_context():
    db.create_all()
    # Create default admin user if not exists
    if not db.session.query(User).filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=User.hash_password('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        logger.info("Created default admin user")

# Initialize the model and tokenizer with a more suitable model
model_name = "microsoft/DialoGPT-medium"  # Using DialoGPT which is specifically trained for dialogue
logger.info(f"Loading model: {model_name}")
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Create a text generation pipeline with specific parameters
text_generator = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    device=0 if torch.cuda.is_available() else -1  # Use GPU if available
)

def generate_response(user_message):
    try:
        # Prepare the input with a specific format for better responses
        prompt = f"User: {user_message}\nAssistant:"
        
        # Generate response using the model with specific parameters
        response = text_generator(
            prompt,
            max_length=150,  # Increased max length for more complete answers
            num_return_sequences=1,
            temperature=0.7,  # Lower temperature for more focused responses
            top_p=0.9,
            do_sample=True,
            truncation=True,
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=3,  # Prevent repetition
            length_penalty=1.0,  # Balance between length and quality
            repetition_penalty=1.2  # Discourage repetition
        )
        
        # Extract and clean the response
        generated_text = response[0]['generated_text']
        # Remove the prompt from the response
        assistant_response = generated_text.split("Assistant:")[-1].strip()
        
        # Ensure the response is not empty
        if not assistant_response:
            return "I apologize, but I couldn't generate a proper response. Could you please rephrase your question?"
            
        return assistant_response
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"I apologize, but I encountered an error: {str(e)}"

@app.route('/')
def index():
    return "Chatbot API is running"

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    try:
        current_user = Auth.get_current_user()
        if not current_user:
            emit('error', {'message': 'Unauthorized'})
            return

        message = data.get('message')
        model = data.get('model', 'gemini')

        if not message:
            emit('error', {'message': 'Message is required'})
            return

        response = ai_model.generate_response(message)
        
        # Store chat history
        chat = Chat(
            user_id=current_user.id,
            message=message,
            response=response,
            model_used=model
        )
        db.session.add(chat)
        db.session.commit()

        emit('response', {
            'response': response,
            'model': model,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        emit('error', {'message': str(e)})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if db.session.query(User).filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    user = Auth.create_user(username, password, role)
    # Create token with string identity
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = Auth.authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Create token with string identity
    token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role
        }
    })

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        user_id = get_jwt_identity()
        logger.info(f"Current user ID: {user_id}")
        
        user = db.session.get(User, int(user_id))
        if not user:
            logger.error(f"User not found for ID: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json()
        message = data.get('message')
        model = 'gemini'

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Use a fallback model if Gemini is not available
        if model == 'gemini':
            try:
                print(model)
                response = ai_model.generate_response(message)
            except Exception as e:
                logger.error(f"Error with Gemini model: {str(e)}")
                # Fallback to a different model
                model = 'gpt2'
                response = ai_model.generate_response(message, model=model)
        else:
            response = ai_model.generate_response(message, model=model)
        
        # Store chat history
        chat = Chat(
            user_id=user.id,
            message=message,
            response=response,
            model_used=model
        )
        db.session.add(chat)
        db.session.commit()

        return jsonify({
            'response': response,
            'model': model,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/history', methods=['GET', 'DELETE'])
@jwt_required()
def chat_history():
    try:
        user_id = get_jwt_identity()
        logger.info(f"Current user ID: {user_id}")
        
        user = db.session.get(User, int(user_id))
        if not user:
            logger.error(f"User not found for ID: {user_id}")
            return jsonify({'error': 'User not found'}), 404

        if request.method == 'DELETE':
            # Delete from SQLite
            Chat.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            
            # Delete from MongoDB if available
            try:
                if mongo_client is not None and mongo_db is not None:
                    conversations.delete_many({'user_id': str(user.id)})
                    logger.info(f"Deleted chat history for user {user.id} from MongoDB")
                else:
                    logger.warning("MongoDB connection not available, skipping MongoDB deletion")
            except Exception as e:
                logger.error(f"Error deleting from MongoDB: {str(e)}")
            
            return jsonify({'message': 'Chat history deleted successfully'})

        # GET method - return chat history
        chats = db.session.query(Chat).filter_by(user_id=user.id).order_by(Chat.timestamp.desc()).all()
        
        return jsonify([{
            'id': chat.id,
            'message': chat.message,
            'response': chat.response,
            'model': chat.model_used,
            'timestamp': chat.timestamp.isoformat()
        } for chat in chats])
    except Exception as e:
        logger.error(f"Error in chat history endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/bot-icon', methods=['POST'])
@jwt_required()
def update_bot_icon():
    current_user = Auth.get_current_user()
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    icon_url = data.get('icon_url')
    
    # Here you would typically save the icon URL to a configuration file or database
    # For now, we'll just return success
    return jsonify({'message': 'Bot icon updated successfully'})

@app.route('/api/models', methods=['GET'])
@jwt_required()
def get_available_models():
    try:
        user_id = get_jwt_identity()
        logger.info(f"Current user ID: {user_id}")
        return jsonify(ai_model.get_available_models())
    except Exception as e:
        logger.error(f"Error in models endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting server...")
    socketio.run(app, debug=True) 