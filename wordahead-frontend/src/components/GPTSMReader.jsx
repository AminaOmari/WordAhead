import { useState } from 'react'
import './GPTSMReader.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000'

function GPTSMReader() {
  const [inputText, setInputText] = useState('')
  const [processedWords, setProcessedWords] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedWord, setSelectedWord] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleAnalyze = async () => {
    if (!inputText.trim()) {
      setError('Please enter some text to analyze')
      return
    }

    setIsLoading(true)
    setError(null)
    
    try {
      console.log('Sending request to:', `${API_URL}/api/process-text`)
      
      const response = await fetch(`${API_URL}/api/process-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText })
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`)
      }

      const data = await response.json()
      console.log('Received data:', data)
      
      if (data.words && data.words.length > 0) {
        setProcessedWords(data.words)
        setError(null)
      } else {
        setError('No words returned from server')
      }
    } catch (err) {
      console.error('Error:', err)
      setError(`Failed to process text: ${err.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  const handleWordClick = async (wordData) => {
    setSelectedWord(wordData)
    setSidebarOpen(true)
    
    // Fetch translation data
    try {
      const response = await fetch(`${API_URL}/api/translate/word/${encodeURIComponent(wordData.word)}`)
      const translationData = await response.json()
      setSelectedWord({ ...wordData, ...translationData })
    } catch (err) {
      console.error('Translation error:', err)
    }
  }

  const closeSidebar = () => {
    setSidebarOpen(false)
    setTimeout(() => setSelectedWord(null), 300)
  }

  return (
    <div className="gptsm-reader">
      {/* Header */}
      <div className="reader-header">
        <h1>📚 WordAhead</h1>
        <p>Reading Assistant with GP-TSM</p>
      </div>

      {/* Input Section */}
      <div className="input-section">
        <textarea
          className="text-input"
          placeholder="Paste your English text here..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          rows={6}
        />
        <button 
          className="analyze-button"
          onClick={handleAnalyze}
          disabled={isLoading}
        >
          {isLoading ? '⏳ Processing...' : '✨ Analyze Text'}
        </button>
        {error && <div className="error-message">❌ {error}</div>}
      </div>

      {/* Results Section */}
      {processedWords.length > 0 && (
        <div className="results-section">
          <h2>📖 Processed Text</h2>
          <div className="processed-text">
            {processedWords.map((wordData, index) => (
              <span
                key={index}
                className={`word importance-${wordData.importance}`}
                style={{ opacity: wordData.opacity }}
                onClick={() => handleWordClick(wordData)}
              >
                {wordData.word}{' '}
              </span>
            ))}
          </div>
          <div className="legend">
            <span className="legend-item">
              <span style={{ opacity: 1 }}>■</span> Most Important (4)
            </span>
            <span className="legend-item">
              <span style={{ opacity: 0.75 }}>■</span> Important (3)
            </span>
            <span className="legend-item">
              <span style={{ opacity: 0.5 }}>■</span> Medium (2)
            </span>
            <span className="legend-item">
              <span style={{ opacity: 0.35 }}>■</span> Less Important (1)
            </span>
            <span className="legend-item">
              <span style={{ opacity: 0.25 }}>■</span> Skippable (0)
            </span>
          </div>
        </div>
      )}

      {/* Sidebar */}
      {sidebarOpen && selectedWord && (
        <>
          <div className="sidebar-overlay" onClick={closeSidebar}></div>
          <div className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
            <button className="close-button" onClick={closeSidebar}>✕</button>
            
            <div className="sidebar-content">
              <h3 className="word-title">{selectedWord.word}</h3>
              
              <div className="section">
                <h4>🇮🇱 Hebrew Translation</h4>
                <p className="hebrew-text">{selectedWord.translation || 'טוען...'}</p>
                <p className="transliteration">{selectedWord.transliteration || ''}</p>
              </div>

              <div className="section">
                <h4>📊 Details</h4>
                <div className="detail-item">
                  <strong>Importance:</strong> {selectedWord.importance}/4
                </div>
                <div className="detail-item">
                  <strong>CEFR Level:</strong> 
                  <span className={`cefr-badge cefr-${selectedWord.cefr_level || 'B1'}`}>
                    {selectedWord.cefr_level || 'B1'}
                  </span>
                </div>
                <div className="detail-item">
                  <strong>Root:</strong> {selectedWord.root || 'Unknown'}
                </div>
              </div>

              {selectedWord.example_sentences && selectedWord.example_sentences.length > 0 && (
                <div className="section">
                  <h4>📝 Examples</h4>
                  {selectedWord.example_sentences.map((example, idx) => (
                    <div key={idx} className="example">
                      <p className="example-english">{example.english}</p>
                      <p className="example-hebrew">{example.hebrew}</p>
                    </div>
                  ))}
                </div>
              )}

              {selectedWord.note && (
                <div className="note">
                  <small>ℹ️ {selectedWord.note}</small>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default GPTSMReader
