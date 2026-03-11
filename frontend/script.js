document.addEventListener('DOMContentLoaded', () => {
    const urlInput = document.getElementById('urlInput');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const resetBtn = document.getElementById('resetBtn');
    const statusMessage = document.getElementById('statusMessage');
    const btnText = document.querySelector('.btn-text');
    const loader = document.querySelector('.loader');

    // Result elements
    const resultSection = document.getElementById('resultSection');
    const classificationBadge = document.getElementById('classificationBadge');
    const scoreCircle = document.getElementById('scoreCircle');
    const scoreTarget = document.getElementById('scoreTarget');
    const matchedDomainVal = document.getElementById('matchedDomainVal');
    const urlVal = document.getElementById('urlVal');
    const depthVal = document.getElementById('depthVal');
    const scriptsVal = document.getElementById('scriptsVal');
    const linksVal = document.getElementById('linksVal');

    // Security elements
    const sslStatusVal = document.getElementById('sslStatusVal');
    const sslIssuerVal = document.getElementById('sslIssuerVal');
    const sslExpiryVal = document.getElementById('sslExpiryVal');
    const apiPill = document.getElementById('apiPill');
    const scriptPill = document.getElementById('scriptPill');
    const linkPill = document.getElementById('linkPill');
    const endpointList = document.getElementById('endpointList');

    const API_BASE = 'http://127.0.0.1:8000/api';

    function setStatus(msg, type = '') {
        statusMessage.textContent = msg;
        statusMessage.className = `status-message status-${type}`;
    }

    function toggleLoading(isLoading) {
        if (isLoading) {
            btnText.classList.add('hidden');
            loader.classList.remove('hidden');
            analyzeBtn.disabled = true;
        } else {
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    }

    function resetUI() {
        resultSection.classList.add('hidden');
        urlInput.value = '';
        setStatus('');
        scoreCircle.style.strokeDashoffset = 283;
        scoreTarget.textContent = '0%';
    }

    function renderResults(data) {
        // Remove hidden
        resultSection.classList.remove('hidden');

        // Setup classification badge
        const classification = data.classification;
        classificationBadge.textContent = classification;
        classificationBadge.className = 'badge'; // reset

        if (classification.includes('Legitimate')) {
            classificationBadge.classList.add('legitimate');
            scoreCircle.style.stroke = 'var(--success)';
        } else if (classification.includes('Phishing')) {
            classificationBadge.classList.add('phishing');
            scoreCircle.style.stroke = 'var(--danger)';
        } else {
            classificationBadge.classList.add('suspicious');
            scoreCircle.style.stroke = 'var(--warning)';
        }

        // Animate Score Map (0 to 1) -> (283 to 0 offset)
        const scorePct = Math.round(data.similarity_score * 100);

        // Counter animation
        let current = 0;
        const speed = 15;
        const interval = setInterval(() => {
            if (current >= scorePct) {
                clearInterval(interval);
                scoreTarget.textContent = `${scorePct}%`;
            } else {
                current++;
                scoreTarget.textContent = `${current}%`;
            }
        }, speed);

        // Circle animation (setTimeout to ensure CSS transition triggers after display:block)
        setTimeout(() => {
            const offset = 283 - (283 * data.similarity_score);
            scoreCircle.style.strokeDashoffset = offset;
        }, 50);

        // Fill Details
        matchedDomainVal.textContent = data.matched_domain || 'None';
        urlVal.textContent = data.url;

        if (data.dna_metadata) {
            depthVal.textContent = data.dna_metadata.max_depth;
            scriptsVal.textContent = data.dna_metadata.scripts;
            linksVal.textContent = data.dna_metadata.links;
        }

        // Fill Security Info (SSL)
        if (data.ssl_info) {
            if (!data.ssl_info.has_ssl) {
                sslStatusVal.innerHTML = `<span class="ssl-status-none">No SSL (HTTP)</span>`;
                sslIssuerVal.textContent = 'N/A';
                sslExpiryVal.textContent = 'N/A';
            } else if (data.ssl_info.valid_cert) {
                sslStatusVal.innerHTML = `<span class="ssl-status-valid">Valid Certificate ✓</span>`;
                sslIssuerVal.textContent = data.ssl_info.issuer || 'Unknown';
                if (data.ssl_info.days_until_expiry) {
                    sslExpiryVal.textContent = `${data.ssl_info.days_until_expiry} days`;
                    if (data.ssl_info.days_until_expiry < 30) sslExpiryVal.style.color = "var(--warning)";
                } else {
                    sslExpiryVal.textContent = 'Unknown';
                }
            } else {
                sslStatusVal.innerHTML = `<span class="ssl-status-invalid">Invalid / Failed ✗</span>`;
                sslIssuerVal.textContent = data.ssl_info.error || 'N/A';
                sslExpiryVal.textContent = 'N/A';
            }
        }

        // Fill Endpoint Info
        if (data.endpoints) {
            const ep = data.endpoints;
            apiPill.textContent = `${ep.api_endpoints ? ep.api_endpoints.length : 0} APIs`;
            scriptPill.textContent = `${ep.external_scripts ? ep.external_scripts.length : 0} Ext. Scripts`;
            linkPill.textContent = `${ep.external_links_count || 0} Ext. Links`;

            endpointList.innerHTML = '';

            // Render top API endpoints explicitly
            if (ep.api_endpoints && ep.api_endpoints.length > 0) {
                ep.api_endpoints.forEach(api => {
                    const div = document.createElement('div');
                    div.className = 'endpoint-item';
                    div.textContent = `API: ${api}`;
                    endpointList.appendChild(div);
                });
            } else {
                endpointList.innerHTML = '<div style="opacity: 0.5;">No API endpoints directly discovered.</div>';
            }

            // Also append a few external scripts securely
            if (ep.external_scripts && ep.external_scripts.length > 0) {
                ep.external_scripts.slice(0, 3).forEach(script => {
                    const div = document.createElement('div');
                    div.className = 'endpoint-item';
                    div.style.borderLeftColor = 'var(--text-secondary)';
                    div.textContent = `Script: ${script}`;
                    endpointList.appendChild(div);
                });
            }
        }
    }

    analyzeBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            setStatus('Please enter a URL', 'error');
            return;
        }

        toggleLoading(true);
        setStatus('Analyzing DOM structure...', '');
        resultSection.classList.add('hidden');

        try {
            const res = await fetch(`${API_BASE}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });
            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || 'Analysis failed');

            if (data.status === 'warning') {
                setStatus(data.message, 'warning');
                toggleLoading(false);
                return;
            }

            setStatus('Analysis complete', 'success');
            renderResults(data);

        } catch (err) {
            setStatus(err.message, 'error');
        } finally {
            toggleLoading(false);
        }
    });

    resetBtn.addEventListener('click', resetUI);
});
