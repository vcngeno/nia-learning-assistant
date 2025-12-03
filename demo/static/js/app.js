// API Configuration
const API_BASE_URL = 'https://web-production-5e612.up.railway.app/api/v1';

// State
let currentUser = null;
let currentChild = null;
let currentConversationId = null;
let authToken = null;
let onboardingStep = 0;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const savedToken = localStorage.getItem('authToken');
    const savedUser = localStorage.getItem('currentUser');

    if (savedToken && savedUser) {
        authToken = savedToken;
        currentUser = JSON.parse(savedUser);
        showChildSection();
    }
});

// Toast Notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `
        <span style="font-size: 1.5rem;">${icon}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('hiding');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Onboarding
function showOnboarding() {
    const steps = [
        {
            title: "Welcome to Nia! 🌟",
            content: "I'm your AI learning assistant! I help K-12 students learn using curated curriculum content."
        },
        {
            title: "Ask Me Anything! 💡",
            content: "Try questions like 'How do I add fractions?' or 'What is photosynthesis?' I'll use our curriculum to help you learn!"
        },
        {
            title: "See My Sources 📚",
            content: "I always show where my information comes from - either from our curriculum or my general knowledge."
        },
        {
            title: "Choose Your Depth 📊",
            content: "Select Level 1 for basics, Level 2 for more details, or Level 3 for comprehensive explanations!"
        }
    ];

    if (onboardingStep >= steps.length) {
        localStorage.setItem('hasSeenOnboarding', 'true');
        return;
    }

    const step = steps[onboardingStep];
    const overlay = document.createElement('div');
    overlay.className = 'onboarding-overlay';
    overlay.innerHTML = `
        <div class="onboarding-card">
            <h2>${step.title}</h2>
            <p>${step.content}</p>
            <div class="onboarding-steps">
                ${steps.map((_, i) => `<div class="step-dot ${i === onboardingStep ? 'active' : ''}"></div>`).join('')}
            </div>
            <div class="onboarding-buttons">
                <button class="btn btn-secondary" onclick="skipOnboarding()">Skip</button>
                <button class="btn btn-primary" onclick="nextOnboarding()">${onboardingStep === steps.length - 1 ? 'Get Started!' : 'Next'}</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
}

function nextOnboarding() {
    document.querySelector('.onboarding-overlay')?.remove();
    onboardingStep++;
    if (onboardingStep < 4) {
        setTimeout(showOnboarding, 300);
    } else {
        localStorage.setItem('hasSeenOnboarding', 'true');
    }
}

function skipOnboarding() {
    document.querySelector('.onboarding-overlay')?.remove();
    localStorage.setItem('hasSeenOnboarding', 'true');
}

// Auth Functions
async function login() {
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorDiv = document.getElementById('login-error');

    try {
        const response = await fetch(`${API_BASE_URL}/auth/parent/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            authToken = data.access_token;
            currentUser = { email, name: data.name || email };
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            showToast('Welcome back! 👋', 'success');
            showChildSection();
        } else {
            errorDiv.textContent = data.detail || 'Login failed';
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        showToast('Connection error', 'error');
    }
}

async function register() {
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const errorDiv = document.getElementById('register-error');

    try {
        const response = await fetch(`${API_BASE_URL}/auth/parent/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: name, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Account created successfully! 🎉', 'success');
            document.getElementById('login-email').value = email;
            document.getElementById('login-password').value = password;
            showTab('login');
            setTimeout(() => login(), 500);
        } else {
            errorDiv.textContent = data.detail || 'Registration failed';
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        showToast('Connection error', 'error');
    }
}

function logout() {
    localStorage.clear();
    location.reload();
}

function showTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(form => form.style.display = 'none');

    if (tab === 'login') {
        document.querySelector('.tab-btn:first-child').classList.add('active');
        document.getElementById('login-form').style.display = 'flex';
    } else {
        document.querySelector('.tab-btn:last-child').classList.add('active');
        document.getElementById('register-form').style.display = 'flex';
    }
}

async function showChildSection() {
    document.getElementById('auth-section').style.display = 'none';
    document.getElementById('child-section').style.display = 'flex';
    document.getElementById('user-info').style.display = 'flex';
    document.getElementById('user-name').textContent = currentUser.name || currentUser.email;
    await loadChildren();
}

async function loadChildren() {
    try {
        const response = await fetch(`${API_BASE_URL}/children/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await response.json();
        const childrenList = document.getElementById('children-list');
        const children = Array.isArray(data) ? data : (data.children || []);

        if (children.length > 0) {
            childrenList.innerHTML = children.map(child => `
                <div class="child-card" onclick="selectChild(${child.id}, '${child.first_name}', '${child.grade_level}')">
                    <h3>${child.first_name} ${child.nickname ? `"${child.nickname}"` : ''}</h3>
                    <p>Grade: ${child.grade_level}</p>
                    <p>Language: ${child.preferred_language === 'es' ? 'Spanish' : 'English'}</p>
                </div>
            `).join('');
        } else {
            childrenList.innerHTML = '<p style="text-align: center; color: #6b7280;">No children yet. Add your first child!</p>';
        }
    } catch (error) {
        console.error('Error loading children:', error);
        showToast('Error loading children', 'error');
    }
}

function showAddChild() {
    document.getElementById('add-child-modal').style.display = 'flex';
}

function closeAddChild() {
    document.getElementById('add-child-modal').style.display = 'none';
}

async function createChild() {
    const name = document.getElementById('child-name').value;
    const nickname = document.getElementById('child-nickname').value;
    const dob = document.getElementById('child-dob').value;
    const grade = document.getElementById('child-grade').value;
    const language = document.getElementById('child-language').value;
    const pin = document.getElementById('child-pin').value;
    const errorDiv = document.getElementById('child-error');

    if (!name || !dob || !grade || !pin) {
        errorDiv.textContent = 'Please fill in all required fields';
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/children/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                first_name: name,
                nickname: nickname || null,
                date_of_birth: dob,
                grade_level: grade,
                preferred_language: language,
                pin: pin
            })
        });

        if (response.ok) {
            showToast(`${name}'s profile created! 🎉`, 'success');
            closeAddChild();

            document.getElementById('child-name').value = '';
            document.getElementById('child-nickname').value = '';
            document.getElementById('child-dob').value = '';
            document.getElementById('child-grade').value = '';
            document.getElementById('child-pin').value = '';
            document.getElementById('child-error').textContent = '';

            await loadChildren();
        } else {
            const data = await response.json();
            errorDiv.textContent = data.detail || 'Failed to create child';
        }
    } catch (error) {
        errorDiv.textContent = 'Connection error. Please try again.';
        showToast('Connection error', 'error');
    }
}

async function selectChild(childId, childName, gradeLevel) {
    currentChild = { id: childId, name: childName, grade_level: gradeLevel };
    await showChatSection();
}

function switchChild() {
    document.getElementById('chat-section').style.display = 'none';
    document.getElementById('child-section').style.display = 'flex';
    currentChild = null;
}

async function showChatSection() {
    document.getElementById('child-section').style.display = 'none';
    document.getElementById('chat-section').style.display = 'flex';
    document.getElementById('current-child-name').textContent = currentChild.name;
    await loadFolders();

    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');
    if (!hasSeenOnboarding) {
        setTimeout(showOnboarding, 500);
    }
}

async function loadFolders() {
    try {
        const response = await fetch(`${API_BASE_URL}/conversation/folders/${currentChild.id}`);
        const data = await response.json();
        const foldersList = document.getElementById('folders-list');

        if (data.folders && data.folders.length > 0) {
            foldersList.innerHTML = data.folders.map(folder => `
                <div class="folder-item" onclick="showConversationsInFolder('${folder}')">
                    ${getFolderIcon(folder)} ${folder}
                </div>
            `).join('');
        } else {
            foldersList.innerHTML = '<p style="text-align: center; color: #6b7280; font-size: 0.875rem;">No conversations yet</p>';
        }
    } catch (error) {
        console.error('Error loading folders:', error);
    }
}

function getFolderIcon(folder) {
    const icons = {
        'Math': '📐', 'Science': '🔬', 'History': '📜',
        'English': '✍️', 'Geography': '🌍', 'Travel': '✈️', 'General': '💬'
    };
    return icons[folder] || '📁';
}

async function showConversationsInFolder(folder) {
    try {
        const response = await fetch(`${API_BASE_URL}/conversation/conversations/${currentChild.id}?folder=${folder}`);
        const data = await response.json();

        document.getElementById('modal-folder-name').textContent = `${folder} Conversations`;
        const conversationList = document.getElementById('conversation-list');

        if (data.conversations && data.conversations.length > 0) {
            conversationList.innerHTML = data.conversations.map(conv => `
                <div class="conversation-item">
                    <h5>${conv.title}</h5>
                    <p>${new Date(conv.updated_at).toLocaleDateString()}</p>
                    <div class="conversation-actions">
                        <button class="icon-btn" onclick="loadConversation(${conv.id})">📖 Open</button>
                    </div>
                </div>
            `).join('');
        } else {
            conversationList.innerHTML = '<p style="text-align: center; color: #6b7280;">No conversations in this folder yet</p>';
        }

        document.getElementById('conversation-modal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading conversations:', error);
        showToast('Error loading conversations', 'error');
    }
}

function closeConversationModal() {
    document.getElementById('conversation-modal').style.display = 'none';
}

async function loadConversation(conversationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/conversation/conversations/${conversationId}/messages`);
        const data = await response.json();

        closeConversationModal();
        currentConversationId = conversationId;

        const container = document.getElementById('messages-container');
        container.innerHTML = '';

        if (data.messages) {
            data.messages.forEach(msg => {
                if (msg.role === 'user') {
                    addMessage('user', msg.content);
                } else {
                    addMessage('assistant', msg.content, null, null, msg.id);
                }
            });
        }

        showToast('Conversation loaded! 📖', 'success');
    } catch (error) {
        console.error('Error loading conversation:', error);
        showToast('Error loading conversation', 'error');
    }
}

function askExample(question) {
    document.getElementById('message-input').value = question;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('message-input');
    const message = input.value.trim();
    if (!message) return;

    const depthLevel = parseInt(document.getElementById('depth-level').value);
    const sendBtn = document.getElementById('send-btn');

    input.disabled = true;
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<span class="loading"></span>';

    addMessage('user', message);
    input.value = '';

    showTypingIndicator();

    try {
        const response = await fetch(`${API_BASE_URL}/conversation/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_id: currentChild.id,
                conversation_id: currentConversationId,
                text: message,
                current_depth: depthLevel
            })
        });

        const data = await response.json();

        removeTypingIndicator();

        if (response.ok) {
            currentConversationId = data.conversation_id;
            addMessage('assistant', data.text, data.source_label, data.sources, data.id);
            loadFolders();
        } else {
            addMessage('assistant', `Sorry, error: ${data.detail}`);
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage('assistant', 'Connection error. Please try again.');
        showToast('Connection error', 'error');
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = 'Send';
        input.focus();
    }
}

function showTypingIndicator() {
    const container = document.getElementById('messages-container');
    const indicator = document.createElement('div');
    indicator.className = 'message message-assistant';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    container.appendChild(indicator);
    container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
    document.getElementById('typing-indicator')?.remove();
}

function addMessage(role, text, sourceLabel = null, sources = null, messageId = null) {
    const container = document.getElementById('messages-container');
    const welcome = container.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${role}`;

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `<div class="sources-list"><h5>📚 Sources:</h5>${sources.map(s =>
            `<div class="source-item">${s.title}</div>`
        ).join('')}</div>`;
    }

    let feedbackHtml = '';
    if (role === 'assistant' && messageId) {
        feedbackHtml = `
            <div class="feedback-buttons">
                <button class="feedback-btn" onclick="submitFeedback(${messageId}, true, this)">
                    👍 Helpful
                </button>
                <button class="feedback-btn" onclick="submitFeedback(${messageId}, false, this)">
                    👎 Not Helpful
                </button>
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-content">
            ${sourceLabel ? `<div class="source-label">${sourceLabel}</div>` : ''}
            ${text.replace(/\n/g, '<br>')}
            ${sourcesHtml}
            ${feedbackHtml}
        </div>
    `;

    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

async function submitFeedback(messageId, isHelpful, button) {
    try {
        const response = await fetch(`${API_BASE_URL}/conversation/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_id: messageId,
                child_id: currentChild.id,
                is_helpful: isHelpful
            })
        });

        if (response.ok) {
            const buttons = button.parentElement.querySelectorAll('.feedback-btn');
            buttons.forEach(btn => {
                btn.classList.add('disabled');
                btn.disabled = true;
            });

            button.classList.add('selected');

            showToast(isHelpful ? 'Thanks for your feedback! 👍' : 'Thanks! We\'ll improve. 👍', 'success');
        }
    } catch (error) {
        console.error('Error submitting feedback:', error);
        showToast('Could not submit feedback', 'error');
    }
}

function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Dark Mode
function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    document.getElementById('theme-toggle').textContent = isDark ? '☀️' : '🌙';
}

// Load theme on init
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        const toggle = document.getElementById('theme-toggle');
        if (toggle) toggle.textContent = '☀️';
    }
});

// Parent Dashboard Functions
async function showParentDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/parent/dashboard/overview`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await response.json();

        if (response.ok) {
            // Hide other sections
            document.getElementById('child-section').style.display = 'none';
            document.getElementById('chat-section').style.display = 'none';
            document.getElementById('child-detail-section').style.display = 'none';

            // Show dashboard
            document.getElementById('dashboard-section').style.display = 'block';

            // Update stats
            document.getElementById('stat-children').textContent = data.total_children;
            document.getElementById('stat-conversations').textContent = data.total_conversations;
            document.getElementById('stat-messages').textContent = data.total_messages;
            document.getElementById('stat-topics').textContent = data.topics_covered.length;

            // Load children analytics
            await loadChildrenAnalytics();

            // Show activity chart
            renderActivityChart(data.recent_activity);

            showToast('Dashboard loaded! 📊', 'success');
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Error loading dashboard', 'error');
    }
}

async function loadChildrenAnalytics() {
    try {
        const response = await fetch(`${API_BASE_URL}/children/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await response.json();
        const children = Array.isArray(data) ? data : (data.children || []);

        const analyticsContainer = document.getElementById('children-analytics');

        if (children.length > 0) {
            const cards = await Promise.all(children.map(async child => {
                const analytics = await getChildQuickStats(child.id);
                return `
                    <div class="child-analytics-card" onclick="showChildDetail(${child.id})">
                        <div class="child-analytics-header">
                            <h3>${child.first_name} ${child.nickname ? `"${child.nickname}"` : ''}</h3>
                            <span style="color: var(--text-secondary);">${child.grade_level}</span>
                        </div>
                        <div class="child-analytics-stats">
                            <div>
                                <strong>${analytics.conversations}</strong> conversations
                            </div>
                            <div>
                                <strong>${analytics.topics}</strong> topics
                            </div>
                            <div>
                                Last active: <strong>${analytics.lastActive}</strong>
                            </div>
                        </div>
                    </div>
                `;
            }));

            analyticsContainer.innerHTML = cards.join('');
        } else {
            analyticsContainer.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No children yet</p>';
        }
    } catch (error) {
        console.error('Error loading children analytics:', error);
    }
}

async function getChildQuickStats(childId) {
    try {
        const response = await fetch(`${API_BASE_URL}/parent/dashboard/child/${childId}?days=7`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await response.json();

        return {
            conversations: data.total_conversations,
            topics: Object.keys(data.topics_breakdown).length,
            lastActive: data.recent_conversations.length > 0
                ? new Date(data.recent_conversations[0].updated_at).toLocaleDateString()
                : 'Never'
        };
    } catch (error) {
        return { conversations: 0, topics: 0, lastActive: 'Unknown' };
    }
}

function renderActivityChart(activityData) {
    const container = document.getElementById('activity-chart');

    if (!activityData || activityData.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No activity this week</p>';
        return;
    }

    const maxMessages = Math.max(...activityData.map(a => a.messages));

    const bars = activityData.map(activity => {
        const height = (activity.messages / maxMessages) * 100;
        const date = new Date(activity.date);
        const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });

        return `
            <div class="activity-bar" style="height: ${height}%;" title="${activity.messages} messages">
                <div class="activity-bar-label">${dayName}</div>
            </div>
        `;
    }).join('');

    container.innerHTML = bars;
}

async function showChildDetail(childId) {
    try {
        const response = await fetch(`${API_BASE_URL}/parent/dashboard/child/${childId}?days=30`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await response.json();

        if (response.ok) {
            // Hide dashboard, show detail
            document.getElementById('dashboard-section').style.display = 'none';
            document.getElementById('child-detail-section').style.display = 'block';

            // Update header
            document.getElementById('child-detail-name').textContent = `${data.child.name}'s Analytics`;

            // Update stats
            document.getElementById('child-stat-conversations').textContent = data.total_conversations;
            document.getElementById('child-stat-avg-messages').textContent = data.avg_messages_per_conversation;

            // Render topics breakdown
            renderTopicsBreakdown(data.topics_breakdown);

            // Render recent conversations
            renderChildConversations(data.recent_conversations, childId);
        }
    } catch (error) {
        console.error('Error loading child detail:', error);
        showToast('Error loading child analytics', 'error');
    }
}

function renderTopicsBreakdown(topics) {
    const container = document.getElementById('topics-breakdown');

    if (Object.keys(topics).length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No topics explored yet</p>';
        return;
    }

    const maxCount = Math.max(...Object.values(topics));

    const items = Object.entries(topics).map(([topic, count]) => {
        const percentage = (count / maxCount) * 100;
        return `
            <div class="topic-item">
                <div style="flex: 1;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                        <strong>${getFolderIcon(topic)} ${topic}</strong>
                        <span>${count} conversation${count !== 1 ? 's' : ''}</span>
                    </div>
                    <div class="topic-bar" style="width: ${percentage}%;"></div>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = items;
}

function renderChildConversations(conversations, childId) {
    const container = document.getElementById('child-conversations');

    if (conversations.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No conversations yet</p>';
        return;
    }

    container.innerHTML = conversations.map(conv => `
        <div class="conversation-item">
            <h5>${conv.title}</h5>
            <p>
                ${getFolderIcon(conv.folder)} ${conv.folder} •
                ${conv.message_count} messages •
                ${new Date(conv.updated_at).toLocaleDateString()}
            </p>
            <div class="conversation-actions">
                <button class="icon-btn" onclick="viewFullConversation(${conv.id})">👁️ View</button>
                <button class="icon-btn" onclick="printConversationById(${conv.id})">🖨️ Print</button>
            </div>
        </div>
    `).join('');
}

async function viewFullConversation(conversationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/parent/dashboard/conversation/${conversationId}/full`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('full-conv-title').textContent = data.conversation.title;

            const content = data.messages.map(msg => `
                <div class="print-message">
                    <div class="print-message-header">
                        <span class="print-message-role">${msg.role === 'user' ? '👤 Student' : '🤖 Nia'}</span>
                        <span>${new Date(msg.created_at).toLocaleString()}</span>
                    </div>
                    <div style="margin-top: 0.5rem;">
                        ${msg.source_label ? `<div style="color: var(--accent-color); font-size: 0.875rem; margin-bottom: 0.5rem;">${msg.source_label}</div>` : ''}
                        ${msg.content.replace(/\n/g, '<br>')}
                    </div>
                    ${msg.feedback !== null ? `<div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--text-secondary);">Feedback: ${msg.feedback ? '👍 Helpful' : '👎 Not Helpful'}</div>` : ''}
                </div>
            `).join('');

            document.getElementById('full-conversation-content').innerHTML = content;
            document.getElementById('full-conversation-modal').style.display = 'flex';
        }
    } catch (error) {
        console.error('Error loading conversation:', error);
        showToast('Error loading conversation', 'error');
    }
}

function closeFullConversation() {
    document.getElementById('full-conversation-modal').style.display = 'none';
}

function printConversation() {
    window.print();
}

async function printConversationById(conversationId) {
    await viewFullConversation(conversationId);
    setTimeout(() => window.print(), 500);
}

function closeDashboard() {
    document.getElementById('dashboard-section').style.display = 'none';
    document.getElementById('child-detail-section').style.display = 'none';
    document.getElementById('child-section').style.display = 'flex';
}

function backToDashboard() {
    document.getElementById('child-detail-section').style.display = 'none';
    showParentDashboard();
}


// Update register function to check consent
const originalRegister = register;
register = async function() {
    const consent = document.getElementById('consent-checkbox');
    const errorDiv = document.getElementById('register-error');

    if (!consent || !consent.checked) {
        errorDiv.textContent = 'Please read and agree to the Terms and Privacy Policy';
        showToast('Please agree to Terms and Privacy Policy', 'error');
        return;
    }

    // Call original register function
    await originalRegister();
};
