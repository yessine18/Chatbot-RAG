// Global State
let chatHistory = [];
let charts = {};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing RAG Chatbot Interface...');
    
    // Initialize tabs
    initializeTabs();
    
    // Initialize event listeners
    initializeEventListeners();
    
    // Load initial data
    loadInitialData();
    
    // Check backend health
    checkHealth();
});

// Tab Management
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => switchTab(button.dataset.tab));
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.id === `${tabName}Tab`) {
            content.classList.add('active');
        }
    });
}

// Event Listeners
function initializeEventListeners() {
    // Chat input
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
    
    // Quick question buttons
    document.querySelectorAll('.quick-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            chatInput.value = btn.textContent;
            sendMessage();
        });
    });
    
    // Top-K slider
    const topKSlider = document.getElementById('topK');
    const topKValue = document.getElementById('topKValue');
    topKSlider.addEventListener('input', (e) => {
        topKValue.textContent = e.target.value;
    });
    
    // Search functionality
    const searchButton = document.getElementById('searchButton');
    const searchInput = document.getElementById('searchInput');
    
    searchButton.addEventListener('click', performSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') performSearch();
    });
    
    // Clear history button
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    clearHistoryBtn.addEventListener('click', clearHistory);
}

// Load Initial Data
async function loadInitialData() {
    try {
        console.log('Loading initial data...');
        showLoading('Loading dashboard data...');
        
        // Load stats
        await fetchStats();
        
        // Load chat history
        await loadHistory();
        
        // Initialize charts
        initializeCharts();
        
        hideLoading();
        console.log('Initial data loaded successfully');
    } catch (error) {
        console.error('Error loading initial data:', error);
        hideLoading();
        showError('Failed to load initial data: ' + error.message);
    }
}

// Fetch Statistics
async function fetchStats() {
    try {
        console.log('Fetching stats from API...');
        const response = await fetch('http://localhost:5000/api/stats');
        console.log('Stats response status:', response.status);
        
        const data = await response.json();
        console.log('Stats data received:', data);
        
        if (data.status === 'success') {
            const stats = data.stats;
            
            // Update stat cards
            document.getElementById('totalRecords').textContent = stats.total_records.toLocaleString();
            document.getElementById('totalFiles').textContent = stats.unique_files;
            document.getElementById('avgLength').textContent = Math.round(stats.avg_length);
            document.getElementById('chatCount').textContent = chatHistory.length;
            
            console.log('Stats updated successfully');
            
            // Update charts
            updateCharts(stats);
        } else {
            console.error('Stats API returned error:', data);
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}

// Initialize Charts
function initializeCharts() {
    // Files Distribution Chart
    const filesCtx = document.getElementById('filesChart').getContext('2d');
    charts.files = new Chart(filesCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    'rgba(79, 70, 229, 0.8)',
                    'rgba(6, 182, 212, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Update Charts
function updateCharts(stats) {
    if (stats.file_distribution) {
        const files = stats.file_distribution;
        const sortedFiles = Object.entries(files)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 10);
        
        charts.files.data.labels = sortedFiles.map(([file]) => file.split('/').pop());
        charts.files.data.datasets[0].data = sortedFiles.map(([, count]) => count);
        charts.files.update();
    }
}

// Send Message
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const question = input.value.trim();
    
    if (!question) return;
    
    const topK = parseInt(document.getElementById('topK').value);
    
    // Clear input
    input.value = '';
    
    // Hide welcome message
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) welcomeMsg.style.display = 'none';
    
    // Add user message
    addMessage(question, 'user');
    
    // Show loading
    showLoading('Génération de la réponse...');
    
    try {
        console.log('Sending request to /api/chat with:', { question, top_k: topK });
        
        const response = await fetch('http://localhost:5000/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question, top_k: topK })
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Chat response received:', data);
        hideLoading();
        
        if (data.status === 'success') {
            console.log('Success! Answer:', data.answer);
            addMessage(data.answer, 'bot', data.sources, data.response_time);
            
            // Add to history
            chatHistory.push({
                question,
                answer: data.answer,
                timestamp: new Date().toISOString()
            });
            
            // Update chat count
            document.getElementById('chatCount').textContent = chatHistory.length;
        } else {
            console.error('Error response:', data);
            addMessage('Erreur: ' + (data.error || 'Impossible de générer une réponse'), 'bot');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        hideLoading();
        addMessage('Erreur de connexion au serveur. Vérifiez que le serveur Flask est actif sur http://localhost:5000', 'bot');
    }
}

// Add Message to Chat
function addMessage(content, type, sources = null, responseTime = null) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    // Parse markdown if available, otherwise use plain text
    try {
        if (typeof marked !== 'undefined' && marked.parse) {
            bubbleDiv.innerHTML = marked.parse(content);
        } else {
            bubbleDiv.textContent = content;
        }
    } catch (error) {
        console.error('Error parsing markdown:', error);
        bubbleDiv.textContent = content;
    }
    
    const metaDiv = document.createElement('div');
    metaDiv.className = 'message-meta';
    const time = new Date().toLocaleTimeString();
    metaDiv.innerHTML = `<i class="far fa-clock"></i> ${time}`;
    if (responseTime) {
        metaDiv.innerHTML += ` | <i class="fas fa-bolt"></i> ${responseTime}s`;
    }
    
    contentDiv.appendChild(bubbleDiv);
    contentDiv.appendChild(metaDiv);
    
    // Add sources if available
    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources-container';
        sourcesDiv.innerHTML = '<h4><i class="fas fa-book"></i> Sources</h4>';
        
        sources.forEach((source, idx) => {
            const sourceItem = document.createElement('div');
            sourceItem.className = 'source-item';
            const relevance = source.relevance || source.similarity || 0;
            sourceItem.innerHTML = `
                <strong>Source ${idx + 1}</strong> (Pertinence: ${relevance}%)
                <div>${source.text.substring(0, 150)}...</div>
            `;
            sourcesDiv.appendChild(sourceItem);
        });
        
        contentDiv.appendChild(sourcesDiv);
    }
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Perform Search
async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput.value.trim();
    
    if (!query) return;
    
    showLoading('Searching corpus...');
    
    try {
        const response = await fetch('http://localhost:5000/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (data.status === 'success') {
            displaySearchResults(data.results);
        }
    } catch (error) {
        console.error('Error performing search:', error);
        hideLoading();
        showError('Search failed');
    }
}

// Display Search Results
function displaySearchResults(results) {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = '';
    
    if (results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <p>No results found</p>
            </div>
        `;
        return;
    }
    
    results.forEach((result, idx) => {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result-item';
        resultDiv.innerHTML = `
            <strong>Result ${idx + 1}</strong> - ${result.file_name}
            <div style="margin-top: 0.5rem; color: #6b7280;">${result.text}</div>
        `;
        resultsContainer.appendChild(resultDiv);
    });
}

// Load History
async function loadHistory() {
    try {
        const response = await fetch('http://localhost:5000/api/history');
        const data = await response.json();
        
        if (data.status === 'success') {
            chatHistory = data.history;
            displayHistory();
        }
    } catch (error) {
        console.error('Error loading history:', error);
    }
}

// Display History
function displayHistory() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '';
    
    if (chatHistory.length === 0) {
        historyList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-history"></i>
                <p>No chat history yet</p>
            </div>
        `;
        return;
    }
    
    chatHistory.forEach((item, idx) => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const date = new Date(item.timestamp);
        const formattedDate = date.toLocaleString();
        
        historyItem.innerHTML = `
            <div class="question"><i class="fas fa-question-circle"></i> ${item.question}</div>
            <div class="answer">${item.answer.substring(0, 150)}...</div>
            <div class="timestamp"><i class="far fa-clock"></i> ${formattedDate}</div>
        `;
        
        historyList.appendChild(historyItem);
    });
}

// Clear History
async function clearHistory() {
    if (!confirm('Are you sure you want to clear all chat history?')) {
        return;
    }
    
    try {
        const response = await fetch('http://localhost:5000/api/clear-history', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            chatHistory = [];
            displayHistory();
            document.getElementById('chatCount').textContent = '0';
        }
    } catch (error) {
        console.error('Error clearing history:', error);
        showError('Failed to clear history');
    }
}

// Check Health
async function checkHealth() {
    try {
        const response = await fetch('http://localhost:5000/api/health');
        const data = await response.json();
        
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-indicator span');
        
        if (data.status === 'healthy') {
            statusDot.style.background = '#10b981';
            statusText.textContent = 'Connected';
        } else {
            statusDot.style.background = '#ef4444';
            statusText.textContent = 'Disconnected';
        }
    } catch (error) {
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-indicator span');
        statusDot.style.background = '#ef4444';
        statusText.textContent = 'Disconnected';
    }
    
    // Check health every 30 seconds
    setTimeout(checkHealth, 30000);
}

// Loading Overlay
function showLoading(message = 'Loading...') {
    const overlay = document.getElementById('loadingOverlay');
    overlay.querySelector('p').textContent = message;
    overlay.classList.add('active');
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    overlay.classList.remove('active');
}

// Error Handling
function showError(message) {
    alert('Error: ' + message);
}
