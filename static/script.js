// DOM Elements
const form = document.getElementById('recommendationForm');
const jobDescription = document.getElementById('jobDescription');
const resumeFiles = document.getElementById('resumeFiles');
const uploadArea = document.getElementById('uploadArea');
const fileList = document.getElementById('fileList');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.querySelector('.btn-text');
const loadingSpinner = document.getElementById('loadingSpinner');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const processingInfo = document.getElementById('processingInfo');
const candidateResults = document.getElementById('candidateResults');
const errorText = document.getElementById('errorText');

// AI Configuration Elements
const configHeader = document.getElementById('configHeader');
const configPanel = document.getElementById('configPanel');
const configToggle = document.getElementById('configToggle');
const configStatus = document.getElementById('configStatus');
const aiConfigForm = document.getElementById('aiConfigForm');
const aiProvider = document.getElementById('aiProvider');
const apiKey = document.getElementById('apiKey');
const toggleApiKey = document.getElementById('toggleApiKey');
const customEndpoint = document.getElementById('customEndpoint');
const testConnection = document.getElementById('testConnection');
const saveConfig = document.getElementById('saveConfig');
const configMessage = document.getElementById('configMessage');
const generateAIBtn = document.getElementById('generateAIBtn');
const aiInsightsInfo = document.getElementById('aiInsightsInfo');

// State management
let selectedFiles = [];
let currentCandidates = [];
let currentJobDescription = '';
let lastAPICall = 0; // Rate limiting tracker

// Default models for each provider
const DEFAULT_MODELS = {
    'openai': 'gpt-3.5-turbo',
    'anthropic': 'claude-3-haiku-20240307',
    'google': 'gemini-pro',
    'groq': 'llama3-8b-8192',
    'ollama': 'llama2'
};

// Drag and drop functionality
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const files = Array.from(e.dataTransfer.files);
    handleFileSelection(files);
});

// File input change handler
resumeFiles.addEventListener('change', (e) => {
    const files = Array.from(e.target.files);
    handleFileSelection(files);
});

// Handle file selection
function handleFileSelection(files) {
    // Filter for allowed file types
    const allowedTypes = ['.pdf', '.docx', '.txt'];
    const validFiles = files.filter(file => {
        const extension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        return allowedTypes.includes(extension);
    });
    
    if (validFiles.length !== files.length) {
        showError('Some files were skipped. Only PDF, DOCX, and TXT files are allowed.');
        setTimeout(hideError, 3000);
    }
    
    // Add valid files to selection
    selectedFiles = [...selectedFiles, ...validFiles];
    updateFileList();
    updateResumeFilesInput();
}

// Update file list display
function updateFileList() {
    if (selectedFiles.length === 0) {
        fileList.innerHTML = '';
        return;
    }
    
    fileList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <span class="file-name">${file.name}</span>
            <div>
                <span class="file-size">${formatFileSize(file.size)}</span>
                <button type="button" onclick="removeFile(${index})" style="margin-left: 10px; background: none; border: none; color: #666; cursor: pointer;">✕</button>
            </div>
        </div>
    `).join('');
}

// Remove file from selection
function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFileList();
    updateResumeFilesInput();
}

// Update the actual file input
function updateResumeFilesInput() {
    const dt = new DataTransfer();
    selectedFiles.forEach(file => dt.items.add(file));
    resumeFiles.files = dt.files;
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validate form
    if (!jobDescription.value.trim()) {
        showError('Please enter a job description.');
        return;
    }
    
    if (selectedFiles.length === 0) {
        showError('Please upload at least one resume file.');
        return;
    }
    
    // Show loading state
    showLoading();
    hideError();
    hideResults();
    
    try {
        const formData = new FormData();
        formData.append('job_description', jobDescription.value.trim());
        
        selectedFiles.forEach(file => {
            formData.append('files', file);
        });
        
        const response = await fetch('/recommend', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'An error occurred while processing your request.');
        }
        
        if (data.success) {
            showResults(data);
        } else {
            showError(data.message);
        }
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An unexpected error occurred. Please try again.');
    } finally {
        hideLoading();
    }
});

// Show loading state
function showLoading() {
    submitBtn.disabled = true;
    submitBtn.classList.add('loading');
    btnText.textContent = 'Processing...';
    loadingSpinner.style.display = 'block';
}

// Hide loading state
function hideLoading() {
    submitBtn.disabled = false;
    submitBtn.classList.remove('loading');
    btnText.textContent = 'Find Best Candidates';
    loadingSpinner.style.display = 'none';
}

// Show results
function showResults(data) {
    resultsSection.style.display = 'block';
    
    // Store data for AI processing
    currentCandidates = data.candidates;
    currentJobDescription = jobDescription.value;
    
    // Update processing info
    processingInfo.innerHTML = `
        <strong>Processing Complete</strong><br>
        Processed ${data.total_processed} files in ${data.processing_time} seconds<br>
        Found ${data.candidates.length} matching candidates
    `;
    
    // Show AI insights button if candidates available
    if (data.candidates.length > 0) {
        generateAIBtn.style.display = 'flex';
        aiInsightsInfo.style.display = 'none'; // Hide previous insights info
    }
    
    // Display candidates
    if (data.candidates.length === 0) {
        candidateResults.innerHTML = '<p>No candidates found matching your criteria.</p>';
        generateAIBtn.style.display = 'none';
        return;
    }
    
    candidateResults.innerHTML = data.candidates.map((candidate, index) => {
        const rankNumber = index + 1;
        const hasAISummary = candidate.ai_summary && candidate.ai_summary !== "AI summary unavailable - OpenAI API key not configured";
        
        return `
            <div class="candidate-card">
                <div class="candidate-header">
                    <div class="candidate-info">
                        <h3>#${rankNumber} - ${candidate.name}</h3>
                        <div class="filename">📄 ${candidate.filename}</div>
                    </div>
                    <div class="match-percentage">${candidate.match_percentage}%</div>
                </div>
                
                <div class="similarity-score">
                    Similarity Score: ${candidate.similarity_score}
                </div>
                
                ${hasAISummary ? `
                    <div class="ai-summary">
                        <button type="button" class="summary-toggle" onclick="toggleSummary(${index})">
                            <span id="toggle-text-${index}">▶ Show AI Analysis</span>
                        </button>
                        <div id="summary-${index}" class="summary-content hidden">
                            ${candidate.ai_summary}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

// Toggle AI summary visibility
function toggleSummary(index) {
    const summaryElement = document.getElementById(`summary-${index}`);
    const toggleText = document.getElementById(`toggle-text-${index}`);
    
    if (summaryElement.classList.contains('hidden')) {
        summaryElement.classList.remove('hidden');
        toggleText.textContent = '▼ Hide AI Analysis';
    } else {
        summaryElement.classList.add('hidden');
        toggleText.textContent = '▶ Show AI Analysis';
    }
}

// Hide results
function hideResults() {
    resultsSection.style.display = 'none';
}

// Show error
function showError(message) {
    errorText.textContent = message;
    errorSection.style.display = 'block';
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

// Hide error
function hideError() {
    errorSection.style.display = 'none';
}

// AI Configuration Functions
function getDefaultModel(provider) {
    return DEFAULT_MODELS[provider] || '';
}

function toggleConfigPanel() {
    const isExpanded = configPanel.style.display !== 'none';
    
    if (isExpanded) {
        configPanel.style.display = 'none';
        configToggle.classList.remove('expanded');
    } else {
        configPanel.style.display = 'block';
        configToggle.classList.add('expanded');
    }
}

function toggleApiKeyVisibility() {
    const isPassword = apiKey.type === 'password';
    apiKey.type = isPassword ? 'text' : 'password';
    toggleApiKey.textContent = isPassword ? '🙈' : '👁️';
}

function showConfigMessage(message, type = 'info') {
    configMessage.textContent = message;
    configMessage.className = `config-message ${type}`;
    configMessage.style.display = 'block';
    
    setTimeout(() => {
        configMessage.style.display = 'none';
    }, 5000);
}

async function testAIConnection() {
    const currentProvider = aiProvider.value;
    const currentApiKey = apiKey.value;
    
    if (!currentProvider || !currentApiKey) {
        showConfigMessage('Please select a provider and enter an API key before testing', 'error');
        return;
    }
    
    // Rate limiting protection - prevent rapid API calls
    const now = Date.now();
    if (now - lastAPICall < 3000) { // 3 second minimum between calls
        const waitTime = Math.ceil((3000 - (now - lastAPICall)) / 1000);
        showConfigMessage(`⏳ Please wait ${waitTime} more second(s) before testing again to avoid rate limits`, 'info');
        
        // Disable button temporarily with countdown
        testConnection.disabled = true;
        const originalText = testConnection.textContent;
        
        const countdown = setInterval(() => {
            const remaining = Math.ceil((3000 - (Date.now() - lastAPICall)) / 1000);
            if (remaining <= 0) {
                testConnection.disabled = false;
                testConnection.textContent = originalText;
                clearInterval(countdown);
            } else {
                testConnection.textContent = `Wait ${remaining}s...`;
            }
        }, 100);
        
        return;
    }
    lastAPICall = now;
    
    const currentModel = getDefaultModel(currentProvider);
    
    testConnection.disabled = true;
    testConnection.textContent = 'Testing...';
    
    try {
        // First save the configuration
        const configData = {
            provider: currentProvider,
            model: currentModel,
            api_key: currentApiKey,
            custom_endpoint: customEndpoint.value || null
        };
        
        const configResponse = await fetch('/configure-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });
        
        const configResult = await configResponse.json();
        
        if (configResult.success) {
            // Test the connection
            const testResponse = await fetch('/test-ai-connection', {
                method: 'POST'
            });
            
            const testResult = await testResponse.json();
            
            if (testResult.success) {
                showConfigMessage('Connection successful! Configuration saved.', 'success');
                updateConfigStatus(true);
            } else {
                showConfigMessage(`Connection failed: ${testResult.message}`, 'error');
                updateConfigStatus(false);
            }
        } else {
            showConfigMessage(`Configuration error: ${configResult.message}`, 'error');
            updateConfigStatus(false);
        }
    } catch (error) {
        showConfigMessage(`Test failed: ${error.message}`, 'error');
        updateConfigStatus(false);
    } finally {
        testConnection.disabled = false;
        testConnection.textContent = 'Test Connection';
    }
}

async function saveAIConfig() {
    const configData = {
        provider: aiProvider.value,
        model: getDefaultModel(aiProvider.value),
        api_key: apiKey.value,
        custom_endpoint: customEndpoint.value || null
    };
    
    if (!configData.provider || !configData.api_key) {
        showConfigMessage('Please select a provider and enter an API key', 'error');
        return;
    }
    
    saveConfig.disabled = true;
    saveConfig.textContent = 'Saving...';
    
    try {
        const response = await fetch('/configure-ai', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(configData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showConfigMessage('Configuration saved successfully!', 'success');
            updateConfigStatus(true);
            toggleConfigPanel(); // Auto-collapse after successful save
        } else {
            showConfigMessage(`Configuration failed: ${result.message}`, 'error');
            updateConfigStatus(false);
        }
    } catch (error) {
        showConfigMessage(`Save failed: ${error.message}`, 'error');
        updateConfigStatus(false);
    } finally {
        saveConfig.disabled = false;
        saveConfig.textContent = 'Save Configuration';
    }
}

function updateConfigStatus(isConfigured) {
    if (isConfigured) {
        configStatus.className = 'config-status configured';
        configStatus.style.color = '#00aa00';
    } else {
        configStatus.className = 'config-status not-configured';
        configStatus.style.color = '#cc0000';
    }
}

async function checkAIStatus() {
    try {
        const response = await fetch('/ai-status');
        const data = await response.json();
        updateConfigStatus(data.configured);
        
        if (data.configured && data.provider_info) {
            showConfigMessage(`Using ${data.provider_info.provider} (${data.provider_info.model})`, 'info');
        }
    } catch (error) {
        console.error('Failed to check AI status:', error);
        updateConfigStatus(false);
    }
}

async function generateAIInsights() {
    if (!currentCandidates.length || !currentJobDescription) {
        showError('No candidates available for AI analysis');
        return;
    }
    
    generateAIBtn.disabled = true;
    generateAIBtn.classList.add('loading');
    generateAIBtn.querySelector('.ai-btn-text').textContent = 'Generating Insights...';
    
    try {
        // Prepare candidate data with resume text
        const candidatesWithText = currentCandidates.map(candidate => ({
            ...candidate,
            resume_text: candidate.resume_text || '' // Ensure resume text is included
        }));
        
        const summaryRequest = {
            job_description: currentJobDescription,
            candidates: candidatesWithText,
            max_summaries: 5
        };
        
        const response = await fetch('/generate-summaries', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(summaryRequest)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Update candidate display with AI summaries
            displayCandidatesWithAI(result.candidates);
            
            // Show insights info
            if (result.stats) {
                aiInsightsInfo.innerHTML = `
                    <strong>AI Insights Generated</strong><br>
                    Provider: ${result.stats.provider_info?.provider || 'Unknown'} (${result.stats.provider_info?.model || 'Unknown'})<br>
                    Summaries: ${result.stats.summaries_generated}/${result.stats.total_candidates}<br>
                    ${result.stats.estimated_cost ? `Estimated Cost: $${result.stats.estimated_cost.toFixed(4)}` : ''}
                `;
                aiInsightsInfo.style.display = 'block';
            }
            
            generateAIBtn.style.display = 'none'; // Hide button after success
        } else {
            showError(`AI generation failed: ${result.message}`);
        }
    } catch (error) {
        showError(`AI generation error: ${error.message}`);
    } finally {
        generateAIBtn.disabled = false;
        generateAIBtn.classList.remove('loading');
        generateAIBtn.querySelector('.ai-btn-text').textContent = '🤖 Generate AI Insights';
    }
}

function displayCandidatesWithAI(candidates) {
    candidateResults.innerHTML = candidates.map((candidate, index) => {
        const rankNumber = index + 1;
        const hasAISummary = candidate.ai_summary && candidate.ai_generated;
        
        return `
            <div class="candidate-card">
                <div class="candidate-header">
                    <div class="candidate-info">
                        <h3>#${rankNumber} - ${candidate.name}</h3>
                        <div class="filename">📄 ${candidate.filename}</div>
                    </div>
                    <div class="match-percentage">${candidate.match_percentage}%</div>
                </div>
                
                <div class="similarity-score">
                    Similarity Score: ${candidate.similarity_score}
                </div>
                
                ${hasAISummary || candidate.ai_summary ? `
                    <div class="ai-summary">
                        <div class="ai-summary-header">
                            <h4 class="ai-summary-title">🤖 AI Best Fit Analysis</h4>
                            ${candidate.ai_provider ? `<span class="ai-provider-badge">${candidate.ai_provider}</span>` : ''}
                        </div>
                        <button type="button" class="summary-toggle" onclick="toggleAISummary(${index})">
                            <span id="ai-toggle-text-${index}">▶ Show Analysis</span>
                        </button>
                        <div id="ai-summary-${index}" class="summary-content ${candidate.ai_generated ? 'ai-generated' : 'fallback'} hidden">
                            ${candidate.ai_summary}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

function toggleAISummary(index) {
    const summaryElement = document.getElementById(`ai-summary-${index}`);
    const toggleText = document.getElementById(`ai-toggle-text-${index}`);
    
    if (summaryElement.classList.contains('hidden')) {
        summaryElement.classList.remove('hidden');
        toggleText.textContent = '▼ Hide Analysis';
    } else {
        summaryElement.classList.add('hidden');
        toggleText.textContent = '▶ Show Analysis';
    }
}

// Event Listeners for AI Configuration
configHeader.addEventListener('click', toggleConfigPanel);
toggleApiKey.addEventListener('click', toggleApiKeyVisibility);
testConnection.addEventListener('click', testAIConnection);
saveConfig.addEventListener('click', saveAIConfig);
generateAIBtn.addEventListener('click', generateAIInsights);

aiConfigForm.addEventListener('submit', (e) => {
    e.preventDefault();
    saveAIConfig();
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    hideError();
    hideResults();
    checkAIStatus();
});