import os
import google.generativeai as genai
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import logging
import requests
import json

logger = logging.getLogger(__name__)

class AIModel:
    def __init__(self):
        # Initialize Gemini
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                # Try to initialize with the correct model name
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Successfully initialized Gemini model")
            except Exception as e:
                logger.error(f"Error initializing Gemini: {str(e)}")
                self.gemini_model = None
        else:
            logger.warning("GEMINI_API_KEY not found in environment variables")
            self.gemini_model = None

        # Initialize GPT-2 as fallback
        try:
            self.gpt2_model = pipeline(
                "text-generation",
                model="gpt2",
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("Successfully initialized GPT-2 model")
        except Exception as e:
            logger.error(f"Error initializing GPT-2: {str(e)}")
            self.gpt2_model = None

    def get_available_models(self):
        models = []
        if self.gemini_model:
            models.append('gemini')
        if self.gpt2_model:
            models.append('gpt2')
        return models

    def generate_response(self, message, model='gemini'):
        try:
            if model == 'gemini' and self.gemini_api_key:
                try:
                    # Try direct API call first
                    response = self._call_gemini_api(message)
                    if response:
                        return response
                    
                    # If direct API call fails, try using the SDK
                    if self.gemini_model:
                        response = self.gemini_model.generate_content(message)
                        return response.text
                except Exception as e:
                    logger.error(f"Error with Gemini model: {str(e)}")
                    if self.gpt2_model:
                        logger.info("Falling back to GPT-2 model")
                        return self._generate_gpt2_response(message)
                    raise
            elif model == 'gpt2' and self.gpt2_model:
                return self._generate_gpt2_response(message)
            else:
                raise ValueError(f"Model {model} is not available")
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def _call_gemini_api(self, message):
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_api_key}"
            headers = {
                'Content-Type': 'application/json'
            }
            data = {
                "contents": [{
                    "parts": [{"text": message}]
                }]
            }
            
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            return None
        except Exception as e:
            logger.error(f"Error calling Gemini API directly: {str(e)}")
            return None

    def _generate_gpt2_response(self, message):
        try:
            response = self.gpt2_model(
                message,
                max_length=100,
                num_return_sequences=1,
                temperature=0.7,
                top_p=0.9,
                do_sample=True
            )
            return response[0]['generated_text']
        except Exception as e:
            logger.error(f"Error generating GPT-2 response: {str(e)}")
            raise 