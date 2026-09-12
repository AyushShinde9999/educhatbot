/**
 * K.K. Wagh Polytechnic Institutional AI Chatbot Widget
 * Embeddable pure Vanilla JavaScript Widget
 */
(function () {
  // Prevent duplicate initialization
  if (window.KKWaghChatbotLoaded) return;
  window.KKWaghChatbotLoaded = true;

  // Configuration
  const scriptTag = document.currentScript || document.querySelector('script[src*="widget.js"]');
  const API_BASE_URL = (scriptTag && scriptTag.getAttribute('data-api-url')) || 'http://localhost:8000';

  // State Management
  let isOpen = false;
  let isLoading = false;
  let sessionId = localStorage.getItem('kkw_chat_session_id');
  if (!sessionId) {
    sessionId = 'kkw_sess_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
    localStorage.setItem('kkw_chat_session_id', sessionId);
  }

  // Inject Widget HTML
  function initWidget() {
    const container = document.createElement('div');
    container.id = 'kkw-chatbot-container';
    container.innerHTML = `
      <div class="kkw-chat-window" id="kkwChatWindow">
        <div class="kkw-chat-header">
          <div class="kkw-header-title">
            <div class="kkw-header-avatar">KKW</div>
            <div class="kkw-header-info">
              <h4>K.K. Wagh Assistant</h4>
              <p>Official Institute AI Support</p>
            </div>
          </div>
          <button class="kkw-close-btn" id="kkwCloseBtn" title="Close chat">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="kkw-chat-body" id="kkwChatBody">
          <div class="kkw-msg bot">
            Hello! 👋 Welcome to K.K. Wagh Polytechnic, Nashik. Ask me anything about admissions, courses, timings, examination rules, or notices!
          </div>
        </div>

        <div class="kkw-chat-footer">
          <input type="text" class="kkw-chat-input" id="kkwChatInput" placeholder="Ask a question..." autocomplete="off" />
          <button class="kkw-send-btn" id="kkwSendBtn" title="Send message">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>

      <button class="kkw-chat-trigger" id="kkwChatTrigger" title="Chat with K.K. Wagh AI Assistant">
        <span class="kkw-badge-dot"></span>
        <svg viewBox="0 0 24 24">
          <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"></path>
        </svg>
      </button>
    `;

    document.body.appendChild(container);

    // Event Listeners
    const triggerBtn = document.getElementById('kkwChatTrigger');
    const closeBtn = document.getElementById('kkwCloseBtn');
    const sendBtn = document.getElementById('kkwSendBtn');
    const inputField = document.getElementById('kkwChatInput');

    triggerBtn.addEventListener('click', toggleChat);
    closeBtn.addEventListener('click', toggleChat);

    sendBtn.addEventListener('click', handleSendMessage);
    inputField.addEventListener('keypress', function (e) {
      if (e.key === 'Enter') handleSendMessage();
    });
  }

  function toggleChat() {
    isOpen = !isOpen;
    const windowEl = document.getElementById('kkwChatWindow');
    if (isOpen) {
      windowEl.classList.add('open');
      document.getElementById('kkwChatInput').focus();
    } else {
      windowEl.classList.remove('open');
    }
  }

  function handleSendMessage() {
    const inputField = document.getElementById('kkwChatInput');
    const question = inputField.value.trim();

    if (!question || isLoading) return;

    // Append User Message
    appendMessage(question, 'user');
    inputField.value = '';

    // Show Loading Dot Indicator
    const loadingId = showLoadingIndicator();
    isLoading = true;
    toggleSendButton(false);

    // Call Backend API
    fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question: question,
        session_id: sessionId
      })
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`Server returned status ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        removeLoadingIndicator(loadingId);
        appendMessage(data.answer, 'bot', data.sources, data.fallback_used);
      })
      .catch(error => {
        console.error('K.K. Wagh Chatbot Error:', error);
        removeLoadingIndicator(loadingId);
        appendMessage(
          'I apologize, but I am unable to connect to the institute server right now. Please check your internet connection or try again later.',
          'bot',
          [],
          true
        );
      })
      .finally(() => {
        isLoading = false;
        toggleSendButton(true);
      });
  }

  function appendMessage(text, sender, sources = [], fallbackUsed = false) {
    const chatBody = document.getElementById('kkwChatBody');
    const msgDiv = document.createElement('div');
    msgDiv.className = `kkw-msg ${sender}`;

    // Format newlines
    let formattedText = text.replace(/\n/g, '<br/>');
    msgDiv.innerHTML = formattedText;

    // Append Sources if Bot Message & available
    if (sender === 'bot' && sources && sources.length > 0 && !fallbackUsed) {
      const sourcesDiv = document.createElement('div');
      sourcesDiv.className = 'kkw-sources-container';
      
      let sourcesHtml = '<div class="kkw-sources-title">📌 Sources:</div>';
      sources.forEach(src => {
        const pageText = src.page_number ? ` (Page ${src.page_number})` : '';
        sourcesHtml += `<span class="kkw-source-tag">${escapeHtml(src.document_name)}${pageText}</span>`;
      });

      sourcesDiv.innerHTML = sourcesHtml;
      msgDiv.appendChild(sourcesDiv);
    }

    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  function showLoadingIndicator() {
    const chatBody = document.getElementById('kkwChatBody');
    const loadingDiv = document.createElement('div');
    const id = 'loading_' + Date.now();
    loadingDiv.id = id;
    loadingDiv.className = 'kkw-msg bot';
    loadingDiv.innerHTML = `
      <div class="kkw-loading-dots">
        <div class="kkw-loading-dot"></div>
        <div class="kkw-loading-dot"></div>
        <div class="kkw-loading-dot"></div>
      </div>
    `;
    chatBody.appendChild(loadingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
    return id;
  }

  function removeLoadingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function toggleSendButton(enabled) {
    const sendBtn = document.getElementById('kkwSendBtn');
    sendBtn.disabled = !enabled;
  }

  function escapeHtml(string) {
    return String(string)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Run initialization on DOM load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    initWidget();
  }
})();
