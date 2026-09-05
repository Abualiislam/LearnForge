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
    let currentProfile = null;
    let allMatches = [];

    const WEIGHTS = {
        exam: 25,
        location: 25,
        examDate: 15,
        availability: 15,
        studyMode: 10,
        subjects: 5,
        studyStyles: 5
    };

    function normalize(value) {
        return String(value || '').trim().toLowerCase();
    }

    function arrayIntersection(a, b) {
        const first = Array.isArray(a) ? a : [];
        const second = new Set(
            (Array.isArray(b) ? b : []).map(normalize)
        );

        return first.filter(item => second.has(normalize(item)));
    }

    function overlapScore(a, b) {
        const first = Array.isArray(a) ? a : [];
        const second = Array.isArray(b) ? b : [];

        if (!first.length || !second.length) {
            return 0;
        }

        const overlap = arrayIntersection(first, second).length;
        const denominator = Math.max(first.length, second.length);

        return denominator ? overlap / denominator : 0;
    }

    function calculateExamScore(myProfile, otherProfile) {
        return normalize(myProfile.exam) === normalize(otherProfile.exam)
            ? WEIGHTS.exam
            : 0;
    }

    function calculateLocationScore(myProfile, otherProfile) {
        const myCountry = normalize(myProfile.country);
        const otherCountry = normalize(otherProfile.country);

        const myCity = normalize(myProfile.city);
        const otherCity = normalize(otherProfile.city);

        if (myCountry && otherCountry && myCountry === otherCountry) {
            if (myCity && otherCity && myCity === otherCity) {
                return WEIGHTS.location;
            }

            return WEIGHTS.location * 0.6;
        }

        return 0;
    }

    function calculateExamDateScore(myProfile, otherProfile) {
        if (!myProfile.exam_date || !otherProfile.exam_date) {
            return 0;
        }

        const dateA = new Date(myProfile.exam_date);
        const dateB = new Date(otherProfile.exam_date);

        if (Number.isNaN(dateA.getTime()) || Number.isNaN(dateB.getTime())) {
            return 0;
        }

        const days = Math.abs(
            (dateA.getTime() - dateB.getTime()) /
            (1000 * 60 * 60 * 24)
        );

        if (days <= 14) {
            return WEIGHTS.examDate;
        }

        if (days <= 30) {
            return WEIGHTS.examDate * 0.8;
        }

        if (days <= 90) {
            return WEIGHTS.examDate * 0.5;
        }

        if (days <= 180) {
            return WEIGHTS.examDate * 0.25;
        }

        return 0;
    }

    function calculateAvailabilityScore(myProfile, otherProfile) {
        const dayScore = overlapScore(
            myProfile.available_days,
            otherProfile.available_days
        );

        let timeScore = 0;

        if (
            myProfile.start_time &&
            myProfile.end_time &&
            otherProfile.start_time &&
            otherProfile.end_time
        ) {
            const myStart = myProfile.start_time.slice(0, 5);
            const myEnd = myProfile.end_time.slice(0, 5);
            const otherStart = otherProfile.start_time.slice(0, 5);
            const otherEnd = otherProfile.end_time.slice(0, 5);

            const startA = new Date(`2000-01-01T${myStart}:00`);
            const endA = new Date(`2000-01-01T${myEnd}:00`);
            const startB = new Date(`2000-01-01T${otherStart}:00`);
            const endB = new Date(`2000-01-01T${otherEnd}:00`);

            const overlapStart = Math.max(
                startA.getTime(),
                startB.getTime()
            );

            const overlapEnd = Math.min(
                endA.getTime(),
                endB.getTime()
            );

            if (overlapEnd > overlapStart) {
                timeScore = 1;
            }
        }

        if (dayScore === 0) {
            return 0;
        }

        if (timeScore === 1) {
            return WEIGHTS.availability;
        }

        return WEIGHTS.availability * dayScore;
    }

    function calculateStudyModeScore(myProfile, otherProfile) {
        const mine = normalize(myProfile.study_mode);
        const theirs = normalize(otherProfile.study_mode);

        if (!mine || !theirs) {
            return 0;
        }

        if (mine === theirs) {
            return WEIGHTS.studyMode;
        }

        if (mine === 'both' || theirs === 'both') {
            return WEIGHTS.studyMode * 0.7;
        }

        return 0;
    }

    function calculateScore(myProfile, otherProfile) {
        const subjects = overlapScore(
            myProfile.subjects,
            otherProfile.subjects
        );

        const styles = overlapScore(
            myProfile.study_styles,
            otherProfile.study_styles
        );

        const score =
            calculateExamScore(myProfile, otherProfile) +
            calculateLocationScore(myProfile, otherProfile) +
            calculateExamDateScore(myProfile, otherProfile) +
            calculateAvailabilityScore(myProfile, otherProfile) +
            calculateStudyModeScore(myProfile, otherProfile) +
            (WEIGHTS.subjects * subjects) +
            (WEIGHTS.studyStyles * styles);

        return Math.round(Math.max(0, Math.min(100, score)));
    }

    function getInitials(name) {
        const text = String(name || '').trim();

        if (!text) {
            return '?';
        }

        return text
            .split(/\s+/)
            .slice(0, 2)
            .map(part => part.charAt(0).toUpperCase())
            .join('');
    }

    function formatDate(dateString) {
        if (!dateString) {
            return 'Exam date not set';
        }

        const date = new Date(`${dateString}T00:00:00`);

        if (Number.isNaN(date.getTime())) {
            return dateString;
        }

        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    function formatStudyMode(mode) {
        const values = {
            online: 'Online',
            in_person: 'In Person',
            both: 'Online & In Person'
        };

        return values[mode] || mode || 'Not specified';
    }

    function getLocation(profile) {
        const parts = [
            profile.city,
            profile.state_region,
            profile.country
        ].filter(Boolean);

        return parts.length
            ? parts.join(', ')
            : 'Location not specified';
    }

    function getMatchReason(match) {
        const reasons = [];

        if (match.score >= 80) {
            reasons.push('Strong overall compatibility');
        }

        if (
            normalize(currentProfile.exam) ===
            normalize(match.exam)
        ) {
            reasons.push('Same exam');
        }

        if (
            normalize(currentProfile.city) &&
            normalize(currentProfile.city) === normalize(match.city)
        ) {
            reasons.push('Same city');
        }

        if (arrayIntersection(
            currentProfile.study_profile.available_days,
            match.available_days
        ).length) {
            reasons.push('Shared availability');
        }

        return reasons.slice(0, 3);
    }

    function createMatchCard(match) {
        const article = document.createElement('article');
        article.className = 'sm-match-card';

        const reasons = getMatchReason(match);

        article.innerHTML = `
            <div class="sm-match-card-header">
                <div class="sm-match-person">
                    <div class="sm-match-avatar">
                        ${getInitials(match.display_name)}
                    </div>

                    <div>
                        <h3 class="sm-match-name">
                            ${escapeHtml(match.display_name || 'StudyMatch Student')}
                        </h3>

                        <p class="sm-match-location">
                            ${escapeHtml(getLocation(match))}
                        </p>
                    </div>
                </div>

                <div class="sm-match-score">
                    ${match.score}% Match
                </div>
            </div>

            <div class="sm-match-details">
                <span class="sm-match-tag">
                    ${escapeHtml(match.exam || 'Exam not specified')}
                </span>

                <span class="sm-match-tag">
                    ${escapeHtml(formatStudyMode(match.study_mode))}
                </span>

                <span class="sm-match-tag">
                    Exam: ${escapeHtml(formatDate(match.exam_date))}
                </span>
            </div>

            ${
                reasons.length
                    ? `<div class="sm-match-details">
                        ${reasons.map(reason =>
                            `<span class="sm-match-tag">${escapeHtml(reason)}</span>`
                        ).join('')}
                       </div>`
                    : ''
            }

            ${
                match.bio
                    ? `<p class="sm-match-bio">
                        ${escapeHtml(match.bio)}
                       </p>`
                    : ''
            }

            <div class="sm-match-actions">
                <button
                    type="button"
                    class="sm-btn sm-btn-secondary"
                    data-profile-id="${escapeHtml(match.id)}"
                >
                    View Profile
                </button>

                <button
                    type="button"
                    class="sm-btn sm-btn-primary"
                    data-connect-id="${escapeHtml(match.id)}"
                >
                    Connect
                </button>
            </div>
        `;

        return article;
    }

    async function sendConnectionRequest(receiverId, button) {
        if (!currentUser || !receiverId) {
            return;
        }

        const originalText = button.textContent;
        button.disabled = true;
        button.textContent = 'Sending...';

        const { error } = await supabaseClient
            .from('connection_requests')
            .insert({
                sender_id: currentUser.id,
                receiver_id: receiverId,
                status: 'pending'
            });

        if (error) {
            console.error('Connection request failed:', error);

            if (error.code === '23505') {
                button.textContent = 'Already Sent';
                button.disabled = true;
                return;
            }

            button.disabled = false;
            button.textContent = originalText;
            alert(error.message);
            return;
        }

        button.textContent = 'Request Sent';
        button.disabled = true;
    }

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function renderMatches() {
        const results = document.getElementById('matchResults');
        const loading = document.getElementById('matchLoading');
        const empty = document.getElementById('noMatches');
        const summary = document.getElementById('matchSummary');

        if (!results || !loading || !empty || !summary) {
            return;
        }

        loading.hidden = true;
        results.innerHTML = '';

        if (!allMatches.length) {
            empty.hidden = false;
            summary.textContent = 'No compatible students found.';
            return;
        }

        empty.hidden = true;

        allMatches.forEach(match => {
            results.appendChild(createMatchCard(match));
        });

        summary.textContent =
            `${allMatches.length} compatible ${allMatches.length === 1 ? 'student' : 'students'} found.`;
    }

    function applyFilters() {
        if (!currentProfile) {
            return;
        }

        const exam = normalize(
            document.getElementById('examFilter').value
        );

        const country = normalize(
            document.getElementById('countryFilter').value
        );

        const city = normalize(
            document.getElementById('cityFilter').value
        );

        const mode = normalize(
            document.getElementById('modeFilter').value
        );

        let filtered = allMatches.slice();

        if (exam) {
            filtered = filtered.filter(
                match => normalize(match.exam) === exam
            );
        }

        if (country) {
            filtered = filtered.filter(
                match => normalize(match.country).includes(country)
            );
        }

        if (city) {
            filtered = filtered.filter(
                match => normalize(match.city).includes(city)
            );
        }

        if (mode) {
            filtered = filtered.filter(match => {
                const matchMode = normalize(match.study_mode);

                return (
                    matchMode === mode ||
                    matchMode === 'both' ||
                    mode === 'both'
                );
            });
        }

        renderFilteredMatches(filtered);
    }

    function renderFilteredMatches(matches) {
        const results = document.getElementById('matchResults');
        const empty = document.getElementById('noMatches');
        const summary = document.getElementById('matchSummary');

        results.innerHTML = '';

        if (!matches.length) {
            empty.hidden = false;
            summary.textContent = 'No students match your filters.';
            return;
        }

        empty.hidden = true;

        matches.forEach(match => {
            results.appendChild(createMatchCard(match));
        });

        summary.textContent =
            `${matches.length} compatible ${matches.length === 1 ? 'student' : 'students'} found.`;
    }

    function sortMatches() {
        const sortBy = document.getElementById('sortMatches').value;

        if (sortBy === 'score') {
            allMatches.sort((a, b) => b.score - a.score);
        }

        if (sortBy === 'name') {
            allMatches.sort((a, b) =>
                String(a.display_name || '').localeCompare(
                    String(b.display_name || '')
                )
            );
        }

        if (sortBy === 'date') {
            allMatches.sort((a, b) => {
                if (!a.exam_date) return 1;
                if (!b.exam_date) return -1;

                return a.exam_date.localeCompare(b.exam_date);
            });
        }

        applyFilters();
    }

    async function loadCurrentUser() {
        const { data, error } =
            await supabaseClient.auth.getSession();

        if (error || !data.session) {
            window.location.href = 'login.html';
            return false;
        }

        currentUser = data.session.user;
        return true;
    }

    async function loadMyProfile() {
        const { data, error } = await supabaseClient
            .from('profiles')
            .select(`
                id,
                display_name,
                country,
                state_region,
                city,
                timezone,
                bio
            `)
            .eq('id', currentUser.id)
            .single();

        if (error) {
            throw error;
        }

        const { data: studyData, error: studyError } =
            await supabaseClient
                .from('study_profiles')
                .select(`
                    exam,
                    exam_date,
                    study_mode,
                    available_days,
                    start_time,
                    end_time,
                    subjects,
                    study_styles,
                    is_active
                `)
                .eq('user_id', currentUser.id)
                .single();

        if (studyError) {
            throw studyError;
        }

        currentProfile = {
            ...data,
            study_profile: studyData
        };
    }

    async function loadCandidates() {
        const { data, error } =
            await supabaseClient
                .from('study_profiles')
                .select(`
                    user_id,
                    exam,
                    exam_date,
                    study_mode,
                    available_days,
                    start_time,
                    end_time,
                    subjects,
                    study_styles,
                    is_active
                `)
                .eq('is_active', true)
                .neq('user_id', currentUser.id);

        if (error) {
            throw error;
        }

        const { data: blockedRows, error: blockedError } =
            await supabaseClient
                .from('blocks')
                .select('blocked_id')
                .eq('blocker_id', currentUser.id);

        if (blockedError) {
            throw blockedError;
        }

        const blockedIds = new Set(
            (blockedRows || []).map(row => row.blocked_id)
        );

        const userIds = (data || [])
            .map(item => item.user_id)
            .filter(userId => !blockedIds.has(userId));

        if (!userIds.length) {
            allMatches = [];
            return;
        }

        const { data: profiles, error: profileError } =
            await supabaseClient
                .from('profiles')
                .select(`
                    id,
                    display_name,
                    country,
                    state_region,
                    city,
                    timezone,
                    bio
                `)
                .in('id', userIds);

        if (profileError) {
            throw profileError;
        }

        const profileMap = new Map(
            (profiles || []).map(profile => [profile.id, profile])
        );

        allMatches = data
            .map(studyProfile => {
                const profile = profileMap.get(studyProfile.user_id);

                if (!profile) {
                    return null;
                }

                return {
                    ...profile,
                    ...studyProfile,
                    score: calculateScore(
                        currentProfile.study_profile,
                        studyProfile
                    )
                };
            })
            .filter(Boolean)
            .sort((a, b) => b.score - a.score);
    }

    function setupEvents() {
        [
            'examFilter',
            'countryFilter',
            'cityFilter',
            'modeFilter'
        ].forEach(id => {
            const element = document.getElementById(id);

            if (element) {
                element.addEventListener(
                    element.tagName === 'INPUT'
                        ? 'input'
                        : 'change',
                    applyFilters
                );
            }
        });

        const reset = document.getElementById('resetFilters');

        if (reset) {
            reset.addEventListener('click', function () {
                document.getElementById('examFilter').value = '';
                document.getElementById('countryFilter').value = '';
                document.getElementById('cityFilter').value = '';
                document.getElementById('modeFilter').value = '';

                applyFilters();
            });
        }

        const sort = document.getElementById('sortMatches');

        if (sort) {
            sort.addEventListener('change', sortMatches);
        }

        document.addEventListener('click', async function (event) {
            const profileButton =
                event.target.closest('[data-profile-id]');

            const connectButton =
                event.target.closest('[data-connect-id]');

            if (profileButton) {
                const id = profileButton.dataset.profileId;

                if (id) {
                    window.location.href =
                        'profile-view.html?user=' + encodeURIComponent(id);
                }
            }

            if (connectButton) {
                const id = connectButton.dataset.connectId;
                await sendConnectionRequest(id, connectButton);
            }
        });

        const logout = document.getElementById('logoutLink');

        if (logout) {
            logout.addEventListener('click', async function (event) {
                event.preventDefault();

                await supabaseClient.auth.signOut();

                window.location.href = 'login.html';
            });
        }
    }

    async function initialize() {
        try {
            const authenticated = await loadCurrentUser();

            if (!authenticated) {
                return;
            }

            await loadMyProfile();
            await loadCandidates();

            setupEvents();
            renderMatches();
        } catch (error) {
            console.error('StudyMatch loading failed:', error);

            const loading = document.getElementById('matchLoading');
            const message = document.getElementById('matchMessage');

            if (loading) {
                loading.hidden = true;
            }

            if (message) {
                message.textContent =
                    error.message ||
                    'Unable to load study partners right now.';
            }
        }
    }

    document.addEventListener(
        'DOMContentLoaded',
        initialize
    );
})();
