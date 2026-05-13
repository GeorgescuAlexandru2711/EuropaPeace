let currentUser = null;
let map = null;
let socket = null;
let currentChatRoom = null;
let allRequests = [];
let audienceCheckInterval = null;

// Initialize app on load
window.onload = () => {
    // Check if map container exists before initializing Leaflet
};

async function login() {
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errDiv = document.getElementById('login-error');
    
    const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
    });
    
    const data = await res.json();
    if (data.success) {
        currentUser = data.user;
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('app-screen').style.display = 'flex';
        
        document.getElementById('user-name-display').innerText = currentUser.fullName;
        let roleName = 'Head of State';
        if (currentUser.role === 'PeaceCouncilMember') roleName = 'Peace Council Admin';
        if (currentUser.role === 'Citizen') roleName = 'Citizen (Public Access)';
        document.getElementById('user-role-display').innerText = roleName;
        
        if (currentUser.role === 'PeaceCouncilMember') {
            document.getElementById('audience-request-form').style.display = 'none';
            document.getElementById('audiences-list-panel').style.display = 'block';
            document.getElementById('end-session-btn').style.display = 'block'; // Council can end session
            document.getElementById('nav-requests').style.display = 'block';
            document.getElementById('nav-audience').style.display = 'block';
            fetchAudiences();
        } else if (currentUser.role === 'Citizen') {
            document.getElementById('nav-requests').style.display = 'none';
            document.getElementById('nav-audience').style.display = 'none';
            document.getElementById('end-session-btn').style.display = 'none';
        } else {
            // Head of State
            document.getElementById('nav-requests').style.display = 'none';
            document.getElementById('nav-audience').style.display = 'block';
            document.getElementById('audience-request-form').style.display = 'block';
            document.getElementById('audiences-list-panel').style.display = 'none';
            document.getElementById('end-session-btn').style.display = 'none'; // Only council ends and writes report
        }
        
        initMap();
        fetchRequests();
        fetchReports();
        errDiv.style.display = 'none';
        
        // Setup Socket.IO
        socket = io();
        socket.on('message', (data) => displayChatMessage(data));
        socket.on('report_generated', () => {
            alert('Session ended and report generated.');
            showSection('reports-section');
            fetchReports();
        });
    } else {
        errDiv.style.display = 'block';
        errDiv.innerText = data.message;
    }
}

function logout() {
    currentUser = null;
    document.getElementById('app-screen').style.display = 'none';
    document.getElementById('login-screen').style.display = 'block';
    if (audienceCheckInterval) clearInterval(audienceCheckInterval);
}

function showSection(sectionId) {
    document.querySelectorAll('section').forEach(s => s.classList.remove('active-section'));
    document.getElementById(sectionId).classList.add('active-section');
    
    document.querySelectorAll('.nav-links a').forEach(a => a.classList.remove('active'));
    event.target.classList.add('active');
    
    if (sectionId === 'map-section' && map) {
        setTimeout(() => map.invalidateSize(), 100);
    }
}

// --- Map Logic ---
async function initMap() {
    if (map) return; // Already initialized
    
    map = L.map('map').setView([50.0, 10.0], 4);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap contributors & CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Fetch and draw countries
    const res = await fetch('/api/countries');
    const countries = await res.json();
    
    countries.forEach(country => {
        if (country.graphicShape && country.graphicShape.length > 0) {
            // Draw Polygon
            const polygon = L.polygon(country.graphicShape, {color: '#3b82f6', fillOpacity: 0.2}).addTo(map);
            polygon.bindPopup(`<b>${country.name}</b><br>Historical: ${country.isHistorical ? 'Yes' : 'No'}`);
            
            // Draw SubRegions as text or small markers
            country.subRegions.forEach((sub, idx) => {
                const center = country.graphicShape[idx % country.graphicShape.length];
                L.marker(center).addTo(map).bindPopup(`Sub-region: ${sub.name} (${sub.status})`);
            });
            
            // Draw Borders (CF_2)
            country.borders.forEach(border => {
                const polyline = L.polyline(border.curveCoordinates, {color: '#ef4444', weight: 4}).addTo(map);
                polyline.bindPopup(`Border: ${border.name}<br>Length: ${border.lengthKm} km`);
            });
        }
    });
}

// --- Requests Logic ---
async function fetchRequests() {
    const res = await fetch('/api/requests');
    allRequests = await res.json();
    renderRequests();
}

function renderRequests() {
    const tbody = document.getElementById('requests-tbody');
    tbody.innerHTML = '';
    
    const search = document.getElementById('req-search').value.toLowerCase();
    const category = document.getElementById('req-category').value;
    
    allRequests.forEach(req => {
        if (category !== 'all' && req.category !== category) return;
        if (search && !req.requestName.toLowerCase().includes(search) && !req.issuingGroup.toLowerCase().includes(search)) return;
        
        let actionBtns = '';
        if (currentUser.role === 'PeaceCouncilMember' && req.status === 'pending') {
            actionBtns = `
                <button onclick="updateRequestStatus('${req._id}', 'approved')" class="btn-success" style="padding: 6px; width: auto; font-size: 12px; margin-right: 5px;">Approve</button>
                <button onclick="updateRequestStatus('${req._id}', 'rejected')" class="btn-danger" style="padding: 6px; width: auto; font-size: 12px;">Reject</button>
            `;
        }
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${req.requestName}</td>
            <td>${req.issuingGroup}</td>
            <td>${req.country}</td>
            <td><span class="badge" style="background:rgba(255,255,255,0.1)">${req.category}</span></td>
            <td><span class="badge ${req.status}">${req.status}</span></td>
            <td>${actionBtns}</td>
        `;
        tbody.appendChild(tr);
    });
}

async function updateRequestStatus(id, status) {
    await fetch(`/api/requests/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status })
    });
    fetchRequests();
}

// --- Audience Logic ---
async function requestAudience() {
    const protocol = document.getElementById('aud-protocol').value;
    const contact = document.getElementById('aud-contact').value;
    
    const res = await fetch('/api/audiences/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: currentUser.username, protocol, contact })
    });
    
    const data = await res.json();
    if (data.success) {
        document.getElementById('aud-status').innerText = `Audience scheduled for ${data.audience.scheduledTime}. Waiting for automatic call...`;
        
        // Start polling for the call (CF_9 / REQ-5)
        audienceCheckInterval = setInterval(() => checkAudienceTime(data.audience), 10000);
    }
}

function checkAudienceTime(audience) {
    const now = new Date().getTime();
    // Simulate incoming call if time passed
    if (now >= audience.timestamp) {
        clearInterval(audienceCheckInterval);
        document.getElementById('incoming-call').style.display = 'block';
        currentChatRoom = audience._id;
    }
}

async function fetchAudiences() {
    const res = await fetch('/api/audiences');
    const auds = await res.json();
    const container = document.getElementById('audiences-list-content');
    container.innerHTML = '';
    auds.forEach(a => {
        container.innerHTML += `<div style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <strong>Requester:</strong> ${a.requester} <br>
            <strong>Time:</strong> ${a.scheduledDate} ${a.scheduledTime} <br>
            <button onclick="currentChatRoom='${a._id}'; showSection('chat-section'); socket.emit('join', { username: currentUser.fullName, room: currentChatRoom });" class="btn-success" style="margin-top:10px;">Join Chat</button>
        </div>`;
    });
}

function joinChatRoom() {
    // If council member, they can just join the latest room (simulation)
    if (!currentChatRoom) currentChatRoom = "test_room_1";
    
    document.getElementById('incoming-call').style.display = 'none';
    showSection('chat-section');
    document.getElementById('chat-room-id').innerText = `Room: ${currentChatRoom}`;
    
    socket.emit('join', { username: currentUser.fullName, room: currentChatRoom });
}

function handleChatKey(e) {
    if (e.key === 'Enter') sendMessage();
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (text && currentChatRoom) {
        socket.emit('message', { username: currentUser.fullName, text: text, room: currentChatRoom });
        input.value = '';
    }
}

function displayChatMessage(data) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    
    let type = 'other';
    if (data.user === 'System') type = 'system';
    else if (data.user === currentUser.fullName) type = 'self';
    
    div.className = `chat-message ${type}`;
    div.innerHTML = type === 'system' ? data.text : `<strong>${data.user}</strong>: ${data.text}`;
    
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function endSession() {
    document.getElementById('report-modal').style.display = 'block';
}

function submitReport() {
    const content = document.getElementById('report-content').value;
    const isPublic = document.getElementById('report-public').checked;
    
    socket.emit('generate_report', { room: currentChatRoom, content, isPublic });
    document.getElementById('report-modal').style.display = 'none';
    
    // Simulate closing chat
    document.getElementById('chat-messages').innerHTML = '';
}

// --- Reports ---
async function fetchReports() {
    const res = await fetch('/api/reports');
    const reports = await res.json();
    const container = document.getElementById('reports-container');
    container.innerHTML = '';
    
    reports.forEach(r => {
        // Enforce REQ-16: For individual audiences, report is only available to Peace Council and the Chief.
        // For simplicity in this demo, if it's public anyone sees it. If not, only council sees it.
        if (!r.isPublic && currentUser.role !== 'PeaceCouncilMember') return;
        
        const card = document.createElement('div');
        card.className = 'glass-panel report-card';
        card.innerHTML = `
            <h4>Hearing Report</h4>
            <p><strong>Date:</strong> ${r.date}</p>
            <p><strong>Visibility:</strong> ${r.isPublic ? 'Public' : 'Private'}</p>
            <hr style="border-color: rgba(255,255,255,0.1); margin: 10px 0;">
            <p>${r.content}</p>
        `;
        container.appendChild(card);
    });
}
