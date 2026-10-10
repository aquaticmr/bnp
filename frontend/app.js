document.addEventListener('DOMContentLoaded', () => {
    // Navigation
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('.page-section');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active button
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // Show target section
            const targetId = btn.getAttribute('data-target');
            sections.forEach(sec => sec.classList.remove('active'));
            document.getElementById(targetId).classList.add('active');
        });
    });

    // API Config
    const RULES_API = 'http://localhost:8002/api/v1';
    const SEARCH_API = 'http://localhost:8001/api/v1';

    // Dashboard Data Loading
    async function loadDashboard() {
        try {
            // Load Alerts
            const alertsRes = await fetch(`${RULES_API}/alerts`);
            if (alertsRes.ok) {
                const alertsData = await alertsRes.json();
                const container = document.getElementById('alerts-container');
                const badge = document.getElementById('dashboard-alerts');
                
                badge.textContent = alertsData.length || 0;
                
                if (alertsData.length === 0) {
                    container.innerHTML = '<p class="text-muted">No recent alerts.</p>';
                } else {
                    container.innerHTML = alertsData.slice(0, 3).map(alert => `
                        <div class="alert-item">
                            <div class="alert-title">${alert.document_title}</div>
                            <div class="alert-desc">${alert.diff_summary}</div>
                            <span class="tag">${alert.impact_level}</span>
                        </div>
                    `).join('');
                }
            }
        } catch (e) {
            document.getElementById('alerts-container').innerHTML = '<p class="text-muted" style="color: #ef4444;">Failed to connect to Rules API.</p>';
        }

        try {
            // Load Impact Matrix Preview
            const impactRes = await fetch(`${RULES_API}/rules`);
            if (impactRes.ok) {
                const impactData = await impactRes.json();
                const container = document.getElementById('impact-container');
                container.innerHTML = `
                    <div style="background: rgba(255,255,255,0.02); padding: 16px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                        <p style="color: #9ba1b0; font-size: 13px; margin-bottom: 12px;">Active rules tracking for regulatory changes.</p>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <span>Rules Scanned</span>
                            <strong style="color: white;">${impactData.length || 0}</strong>
                        </div>
                        <div style="width: 100%; background: rgba(255,255,255,0.1); height: 6px; border-radius: 3px; overflow: hidden;">
                            <div style="width: 75%; background: var(--accent-blue); height: 100%;"></div>
                        </div>
                        <p style="font-size: 11px; color: #9ba1b0; margin-top: 8px;">System operating nominally.</p>
                    </div>
                `;
            }
        } catch (e) {
            document.getElementById('impact-container').innerHTML = '<p class="text-muted" style="color: #ef4444;">API Unavailable</p>';
        }
    }

    loadDashboard();
    document.getElementById('refresh-impact').addEventListener('click', loadDashboard);

    // RAG Search Logic
    const ragSubmit = document.getElementById('rag-submit');
    const ragInput = document.getElementById('rag-input');
    const ragChat = document.getElementById('rag-chat');

    async function submitRagQuery() {
        const query = ragInput.value.trim();
        if (!query) return;

        // Add user message
        ragChat.innerHTML += `
            <div class="message user">
                <div class="message-content">${query}</div>
            </div>
        `;
        ragInput.value = '';
        
        // Add loading state
        const loadingId = 'loading-' + Date.now();
        ragChat.innerHTML += `
            <div class="message system" id="${loadingId}">
                <div class="message-content"><div class="loader" style="width: 16px; height: 16px; margin: 0; display: inline-block; vertical-align: middle;"></div> Analyzing regulations...</div>
            </div>
        `;
        ragChat.scrollTop = ragChat.scrollHeight;

        try {
            // Note: Since this is mock/demo, we handle fetch correctly if API exists
            const res = await fetch(`${SEARCH_API}/rag/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    filters: {},
                    top_k: 3,
                    stream: false
                })
            });

            document.getElementById(loadingId).remove();

            if (res.ok) {
                const data = await res.json();
                ragChat.innerHTML += `
                    <div class="message system">
                        <div class="message-content">${data.answer || data.response || "I couldn't find specific references, but based on general regulatory knowledge..."}</div>
                    </div>
                `;
            } else {
                throw new Error("API Error");
            }
        } catch (e) {
            document.getElementById(loadingId)?.remove();
            ragChat.innerHTML += `
                <div class="message system">
                    <div class="message-content" style="color: #ef4444;">Connection failed. Is the Search Service (port 8001) running?</div>
                </div>
            `;
        }
        ragChat.scrollTop = ragChat.scrollHeight;
    }

    ragSubmit.addEventListener('click', submitRagQuery);
    ragInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') submitRagQuery();
    });

    // Rules Gap Analysis Logic
    const gapBtn = document.getElementById('run-gap-btn');
    gapBtn.addEventListener('click', async () => {
        const category = document.getElementById('gap-category').value;
        const jurisdiction = document.getElementById('gap-jurisdiction').value;
        const resultsDiv = document.getElementById('gap-results');

        resultsDiv.innerHTML = '<div class="loader"></div>';

        try {
            const res = await fetch(`${RULES_API}/gap-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    category: category,
                    jurisdiction: jurisdiction,
                    baseline_version: "current",
                    target_version: "new"
                })
            });

            if (res.ok) {
                const data = await res.json();
                
                // Assuming data has gaps array
                if (data.gaps && data.gaps.length > 0) {
                    resultsDiv.innerHTML = data.gaps.map(gap => `
                        <div class="alert-item" style="border-left: 3px solid ${gap.severity === 'HIGH' ? '#ef4444' : '#f59e0b'};">
                            <div class="alert-title">${gap.field_name || gap.rule_id}</div>
                            <div class="alert-desc">${gap.description}</div>
                        </div>
                    `).join('');
                } else {
                    resultsDiv.innerHTML = `
                        <div style="padding: 20px; text-align: center; color: #10b981;">
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-bottom: 12px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                            <h4>No Compliance Gaps Detected</h4>
                            <p style="font-size: 13px; color: var(--text-secondary); margin-top: 4px;">Your current implementation covers all required rules.</p>
                        </div>
                    `;
                }
            } else {
                throw new Error("API Error");
            }
        } catch (e) {
            resultsDiv.innerHTML = '<p class="text-muted" style="color: #ef4444;">Failed to run gap analysis. Ensure Rules Engine (port 8002) is running.</p>';
        }
    });
});
