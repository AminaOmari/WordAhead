"""
WordAhead Backend API
Flask server that wraps GP-TSM functionality
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": os.getenv('FRONTEND_URL', 'http://localhost:5173')
    }
})

# Check for OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.warning("⚠️  OPENAI_API_KEY not found in environment!")
else:
    logger.info("✅ OpenAI API key loaded")

# Try to import GP-TSM
GP_TSM_AVAILABLE = False
try:
    # Add GP-TSM to path if it exists
    gp_tsm_path = os.path.join(os.path.dirname(__file__), 'GP-TSM')
    if os.path.exists(gp_tsm_path):
        sys.path.insert(0, gp_tsm_path)
        from gp_tsm_simple import process_paragraph
        GP_TSM_AVAILABLE = True
        logger.info("✅ GP-TSM loaded successfully")
    else:
        logger.warning("⚠️  GP-TSM folder not found. Please clone and symlink it.")
        logger.warning("   Run: git clone https://github.com/ZiweiGu/GP-TSM.git")
        logger.warning("   Then: ln -s ../GP-TSM ./GP-TSM")
except ImportError as e:
    logger.warning(f"⚠️  GP-TSM not available: {e}")
    logger.warning("   The app will run with mock data for testing")

# Mock GP-TSM function for testing without the actual library
def mock_process_paragraph(paragraph):
    """
    Mock function that returns fake importance scores
    This lets you test the frontend without GP-TSM
    """
    words = paragraph.split()
    result = []
    
    for word in words:
        # Simple heuristic: longer words = more important
        word_len = len(word.strip('.,!?;:'))
        if word_len > 10:
            importance = 4
        elif word_len > 7:
            importance = 3
        elif word_len > 5:
            importance = 2
        elif word_len > 3:
            importance = 1
        else:
            importance = 0
        
        result.append({
            'word': word,
            'importance': importance
        })
    
    return result


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'gp_tsm_available': GP_TSM_AVAILABLE,
        'openai_configured': bool(OPENAI_API_KEY)
    })


@app.route('/api/process-text', methods=['POST'])
def process_text():
    """
    Process text with GP-TSM to get word importance scores
    
    Request body:
    {
        "text": "The paragraph to process..."
    }
    
    Response:
    {
        "words": [
            {"word": "The", "importance": 0},
            {"word": "paragraph", "importance": 3},
            ...
        ],
        "using_mock": false
    }
    """
    try:
        # Get text from request
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Empty text'}), 400
        
        logger.info(f"Processing text: {text[:100]}...")
        
        # Process with GP-TSM or mock
        if GP_TSM_AVAILABLE and OPENAI_API_KEY:
            logger.info("Using real GP-TSM")
            words_data = process_paragraph(text)
            using_mock = False
        else:
            logger.info("Using mock GP-TSM (for testing)")
            words_data = mock_process_paragraph(text)
            using_mock = True
        
        # Convert importance to opacity
        # importance 0-4 -> opacity 0.25-1.0
        importance_to_opacity = {
            4: 1.0,   # Most important - full black
            3: 0.75,  # Important - dark gray
            2: 0.5,   # Medium - medium gray
            1: 0.35,  # Less important - light gray
            0: 0.25   # Least important - very light gray
        }
        
        result_words = []
        for item in words_data:
            word = item['word']
            importance = item.get('importance', 0)
            opacity = importance_to_opacity.get(importance, 0.5)
            
            result_words.append({
                'word': word,
                'importance': importance,
                'opacity': opacity
            })
        
        logger.info(f"✅ Processed {len(result_words)} words")
        
        return jsonify({
            'words': result_words,
            'using_mock': using_mock,
            'warning': 'Using mock data - GP-TSM not available' if using_mock else None
        })
    
    except Exception as e:
        logger.error(f"❌ Error processing text: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate/word/<word>', methods=['GET'])
def translate_word(word):
    """
    Get Hebrew translation and details for a word
    
    Response:
    {
        "word": "deforestation",
        "translation": "כריתת יערות",
        "transliteration": "kriitat ye'arot",
        "root": "forest + de-",
        "cefr_level": "C1",
        "example_sentences": [...]
    }
    """
    try:
        # TODO: Integrate real translation API (Morfix, Google Translate)
        # For now, return mock data
        
        mock_translations = {
            'deforestation': {
                'translation': 'כריתת יערות',
                'transliteration': 'kriitat ye\'arot',
                'root': 'forest (יער) + de- (prefix)',
                'cefr_level': 'C1',
                'example_sentences': [
                    {
                        'english': 'Deforestation is a major environmental issue.',
                        'hebrew': 'כריתת יערות היא בעיה סביבתית גדולה.'
                    }
                ]
            },
            'forest': {
                'translation': 'יער',
                'transliteration': 'ya\'ar',
                'root': 'forest',
                'cefr_level': 'A2',
                'example_sentences': [
                    {
                        'english': 'We walked through the forest.',
                        'hebrew': 'הלכנו דרך היער.'
                    }
                ]
            }
        }
        
        # Get translation or return generic data
        word_lower = word.lower().strip('.,!?;:')
        translation_data = mock_translations.get(word_lower, {
            'translation': f'[{word}]',
            'transliteration': f'[{word}]',
            'root': 'Unknown',
            'cefr_level': 'B1',
            'example_sentences': [
                {
                    'english': f'This is an example with {word}.',
                    'hebrew': f'זו דוגמה עם {word}.'
                }
            ]
        })
        
        return jsonify({
            'word': word,
            **translation_data,
            'note': 'Mock data - real translation API not yet integrated'
        })
    
    except Exception as e:
        logger.error(f"❌ Error translating word: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/translate/sentence', methods=['POST'])
def translate_sentence():
    """
    Translate a sentence to Hebrew
    
    Request body:
    {
        "sentence": "The forest is beautiful."
    }
    
    Response:
    {
        "english": "The forest is beautiful.",
        "hebrew": "היער יפה.",
        "transliteration": "haya'ar yafe"
    }
    """
    try:
        data = request.get_json()
        sentence = data.get('sentence', '')
        
        # TODO: Integrate real translation API
        # For now, return mock data
        
        return jsonify({
            'english': sentence,
            'hebrew': '[Hebrew translation]',
            'transliteration': '[Transliteration]',
            'note': 'Mock data - real translation API not yet integrated'
        })
    
    except Exception as e:
        logger.error(f"❌ Error translating sentence: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info("=" * 60)
    logger.info("🚀 Starting WordAhead Backend Server")
    logger.info("=" * 60)
    logger.info(f"📍 Port: {port}")
    logger.info(f"🔧 Debug: {debug}")
    logger.info(f"🤖 GP-TSM Available: {GP_TSM_AVAILABLE}")
    logger.info(f"🔑 OpenAI Configured: {bool(OPENAI_API_KEY)}")
    logger.info("=" * 60)
    
    if not GP_TSM_AVAILABLE:
        logger.warning("")
        logger.warning("⚠️  WARNING: GP-TSM not available!")
        logger.warning("   The app will use MOCK data for testing.")
        logger.warning("")
        logger.warning("   To enable real GP-TSM:")
        logger.warning("   1. git clone https://github.com/ZiweiGu/GP-TSM.git")
        logger.warning("   2. ln -s ../GP-TSM ./GP-TSM")
        logger.warning("   3. Restart the server")
        logger.warning("")
    
    if not OPENAI_API_KEY:
        logger.warning("")
        logger.warning("⚠️  WARNING: OPENAI_API_KEY not set!")
        logger.warning("   Add it to your .env file")
        logger.warning("")
    
    logger.info("✅ Server ready! Open http://localhost:5173 in your browser")
    logger.info("")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )