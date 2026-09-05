(function () {
    'use strict';

    const config = window.STUDYMATCH_CONFIG;

    if (!config || !config.supabaseUrl || !config.supabaseKey) {
        console.error('StudyMatch Supabase configuration is missing.');
        return;
    }

    const { createClient } = window.supabase;

    const supabaseClient = createClient(
        config.supabaseUrl,
        config.supabaseKey
    );

    let currentUser = null;

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function initials(name) {
        const clean = String(name || 'Student').trim();

        if (!clean) {
            return 'S';
        }

        return clean
            .split(/\s+/)
            .slice(0, 2)
            .map(part => part.charAt(0).toUpperCase())
            .join('');
    }

    function formatLocation(profile) {
        return [profile?.city, profile?.state_region, profile?.country]
            .filter(Boolean)
            .join(', ') || 'Location not provided';
    }

    function formatExam(studyProfile) {
        return studyProfile?.exam || 'Exam not specified';
    }

    function setLoading(id, visible) {
        const element = document.getElementById(id);

        if (element) {
            element.hidden = !visible;
        }
    }

    function showEmpty(id, visible) {
        const element = document.getElementById(id);

        if (element) {
            element.hidden = !visible;
        }
    }

    function showMessage(message) {
        const existing = document.getElementById('connectionMessage');

        if (existing) {
            existing.textContent = message;
            return;
        }

        const messageElement = document.createElement('div');
        messageElement.id = 'connectionMessage';
        messageElement.className = 'sm-form-message';
        messageElement.textContent = message;

        const pageIntro = document.querySelector('.sm-page-intro');

        if (pageIntro) {
            pageIntro.insertAdjacentElement('afterend', messageElement);
        }
    }

    async function requireUser() {
        const { data, error } = await supabaseClient.auth.getSession();

        if (error) {
            console.error('Session check failed:', error);
            showMessage('Unable to verify your session.');
            return false;
        }

        if (!data.session) {
            window.location.href = 'login.html';
            return false;
        }

        currentUser = data.session.user;
        return true;
    }

    async function getProfiles(userIds) {
        if (!userIds.length) {
            return {};
        }

        const { data, error } = await supabaseClient
            .from('profiles')
            .select('id, display_name, country, state_region, city, timezone, bio')
            .in('id', userIds);

        if (error) {
            throw error;
        }

        const profileMap = {};

        (data || []).forEach(profile => {
            profileMap[profile.id] = profile;
        });

        return profileMap;
    }

    async function getStudyProfiles(userIds) {
        if (!userIds.length) {
            return {};
        }

        const { data, error } = await supabaseClient
            .from('study_profiles')
            .select('user_id, exam, exam_date, study_mode, available_days, subjects, study_styles')
            .in('user_id', userIds);

        if (error) {
            throw error;
        }

        const studyMap = {};

        (data || []).forEach(profile => {
            studyMap[profile.user_id] = profile;
        });

        return studyMap;
    }

    function renderPersonCard(profile, studyProfile, extraHtml) {
        const name = profile?.display_name || 'StudyMatch Student';

        return `
            <article class="sm-request-card">
                <div class="sm-match-card-header">
                    <div class="sm-match-person">
                        <div class="sm-match-avatar">
                            ${escapeHtml(initials(name))}
                        </div>

                        <div>
                            <h3 class="sm-match-name">
                                ${escapeHtml(name)}
                            </h3>

                            <p class="sm-match-location">
                                ${escapeHtml(formatLocation(profile))}
                            </p>
                        </div>
                    </div>
                </div>

                <div class="sm-match-details">
                    <span class="sm-match-tag">
                        ${escapeHtml(formatExam(studyProfile))}
                    </span>

                    ${studyProfile?.study_mode ? `
                        <span class="sm-match-tag">
                            ${escapeHtml(
                                studyProfile.study_mode === 'online'
                                    ? 'Online'
                                    : studyProfile.study_mode === 'in_person'
                                        ? 'In Person'
                                        : 'Online & In Person'
                            )}
                        </span>
                    ` : ''}

                    ${studyProfile?.exam_date ? `
                        <span class="sm-match-tag">
                            Exam: ${escapeHtml(studyProfile.exam_date)}
                        </span>
                    ` : ''}
                </div>

                ${profile?.bio ? `
                    <p class="sm-match-bio">
                        ${escapeHtml(profile.bio)}
                    </p>
                ` : ''}

                ${extraHtml || ''}
            </article>
        `;
    }

    async function loadIncomingRequests() {
        setLoading('incomingLoading', true);
        showEmpty('incomingEmpty', false);

        const { data, error } = await supabaseClient
            .from('connection_requests')
            .select('id, sender_id, status, created_at')
            .eq('receiver_id', currentUser.id)
            .eq('status', 'pending')
            .order('created_at', { ascending: false });

        if (error) {
            console.error('Incoming requests failed:', error);
            setLoading('incomingLoading', false);
            showMessage(error.message);
            return;
        }

        const requests = data || [];
        const container = document.getElementById('incomingRequests');

        if (!requests.length) {
            container.innerHTML = '';
            setLoading('incomingLoading', false);
            showEmpty('incomingEmpty', true);
            return;
        }

        const userIds = requests.map(request => request.sender_id);

        const [profiles, studyProfiles] = await Promise.all([
            getProfiles(userIds),
            getStudyProfiles(userIds)
        ]);

        container.innerHTML = requests.map(request => {
            const profile = profiles[request.sender_id];
            const studyProfile = studyProfiles[request.sender_id];

            return renderPersonCard(
                profile,
                studyProfile,
                `
                    <div class="sm-request-actions">
                        <button
                            class="sm-btn sm-btn-primary sm-request-action"
                            data-action="accept"
                            data-request-id="${escapeHtml(request.id)}"
                        >
                            Accept
                        </button>

                        <button
                            class="sm-btn sm-btn-secondary sm-request-action"
                            data-action="reject"
                            data-request-id="${escapeHtml(request.id)}"
                        >
                            Reject
                        </button>
                    </div>
                `
            );
        }).join('');

        setLoading('incomingLoading', false);
        showEmpty('incomingEmpty', false);
    }

    async function loadSentRequests() {
        setLoading('sentLoading', true);
        showEmpty('sentEmpty', false);

        const { data, error } = await supabaseClient
            .from('connection_requests')
            .select('id, receiver_id, status, created_at')
            .eq('sender_id', currentUser.id)
            .order('created_at', { ascending: false });

        if (error) {
            console.error('Sent requests failed:', error);
            setLoading('sentLoading', false);
            showMessage(error.message);
            return;
        }

        const requests = data || [];
        const container = document.getElementById('sentRequests');

        if (!requests.length) {
            container.innerHTML = '';
            setLoading('sentLoading', false);
            showEmpty('sentEmpty', true);
            return;
        }

        const userIds = requests.map(request => request.receiver_id);

        const [profiles, studyProfiles] = await Promise.all([
            getProfiles(userIds),
            getStudyProfiles(userIds)
        ]);

        container.innerHTML = requests.map(request => {
            const profile = profiles[request.receiver_id];
            const studyProfile = studyProfiles[request.receiver_id];

            const statusClass =
                request.status === 'accepted'
                    ? 'sm-status-success'
                    : request.status === 'rejected'
                        ? 'sm-status-danger'
                        : 'sm-status-pending';

            return renderPersonCard(
                profile,
                studyProfile,
                `
                    <div class="sm-request-actions">
                        <span class="sm-request-status ${statusClass}">
                            ${escapeHtml(request.status)}
                        </span>
                    </div>
                `
            );
        }).join('');

        setLoading('sentLoading', false);
        showEmpty('sentEmpty', false);
    }

    async function loadConnections() {
        setLoading('connectionsLoading', true);
        showEmpty('connectionsEmpty', false);

        const { data, error } = await supabaseClient
            .from('connections')
            .select('id, user_a, user_b, created_at')
            .or(`user_a.eq.${currentUser.id},user_b.eq.${currentUser.id}`)
            .order('created_at', { ascending: false });

        if (error) {
            console.error('Connections failed:', error);
            setLoading('connectionsLoading', false);
            showMessage(error.message);
            return;
        }

        const connections = data || [];
        const container = document.getElementById('connectionsList');

        if (!connections.length) {
            container.innerHTML = '';
            setLoading('connectionsLoading', false);
            showEmpty('connectionsEmpty', true);
            return;
        }

        const partnerIds = connections.map(connection =>
            connection.user_a === currentUser.id
                ? connection.user_b
                : connection.user_a
        );

        const [profiles, studyProfiles] = await Promise.all([
            getProfiles(partnerIds),
            getStudyProfiles(partnerIds)
        ]);

        container.innerHTML = connections.map(connection => {
            const partnerId =
                connection.user_a === currentUser.id
                    ? connection.user_b
                    : connection.user_a;

            const profile = profiles[partnerId];
            const studyProfile = studyProfiles[partnerId];

            return renderPersonCard(
                profile,
                studyProfile,
                `
                    <div class="sm-request-actions">
                        <button
                            class="sm-btn sm-btn-primary"
                            data-action="message"
                            data-user-id="${escapeHtml(partnerId)}"
                        >
                            Message
                        </button>
                    </div>
                `
            );
        }).join('');

        setLoading('connectionsLoading', false);
        showEmpty('connectionsEmpty', false);
    }

    async function acceptRequest(requestId, button) {
        button.disabled = true;
        button.textContent = 'Accepting...';

        const { error } = await supabaseClient
            .rpc('accept_connection_request', {
                p_request_id: requestId
            });

        if (error) {
            console.error('Accept request failed:', error);
            button.disabled = false;
            button.textContent = 'Accept';
            alert(error.message);
            return;
        }

        await Promise.all([
            loadIncomingRequests(),
            loadSentRequests(),
            loadConnections()
        ]);
    }

    async function rejectRequest(requestId, button) {
        button.disabled = true;
        button.textContent = 'Rejecting...';

        const { error } = await supabaseClient
            .from('connection_requests')
            .update({ status: 'rejected' })
            .eq('id', requestId)
            .eq('receiver_id', currentUser.id);

        if (error) {
            console.error('Reject request failed:', error);
            button.disabled = false;
            button.textContent = 'Reject';
            alert(error.message);
            return;
        }

        await loadIncomingRequests();
    }

    async function signOut() {
        const { error } = await supabaseClient.auth.signOut();

        if (error) {
            console.error('Sign out failed:', error);
            alert(error.message);
            return;
        }

        window.location.href = 'login.html';
    }

    document.addEventListener('click', async function (event) {
        const actionButton = event.target.closest('[data-action]');

        if (!actionButton) {
            return;
        }

        const action = actionButton.dataset.action;

        if (action === 'accept') {
            await acceptRequest(
                actionButton.dataset.requestId,
                actionButton
            );
        }

        if (action === 'reject') {
            await rejectRequest(
                actionButton.dataset.requestId,
                actionButton
            );
        }

        if (action === 'message') {
            window.location.href = 'chat.html';
        }
    });

    document.addEventListener('DOMContentLoaded', async function () {
        const logoutLink = document.getElementById('logoutLink');

        if (logoutLink) {
            logoutLink.addEventListener('click', function (event) {
                event.preventDefault();
                signOut();
            });
        }

        const authenticated = await requireUser();

        if (!authenticated) {
            return;
        }

        try {
            await Promise.all([
                loadIncomingRequests(),
                loadSentRequests(),
                loadConnections()
            ]);
        } catch (error) {
            console.error('Connections page failed:', error);
            showMessage(error.message || 'Unable to load connections.');
        }
    });
})();
