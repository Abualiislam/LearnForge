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
    let viewedUserId = null;

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function initials(name) {
        const parts = String(name || 'Study Partner')
            .trim()
            .split(/\s+/)
            .filter(Boolean);

        if (!parts.length) {
            return 'S';
        }

        if (parts.length === 1) {
            return parts[0].slice(0, 2).toUpperCase();
        }

        return (
            parts[0].charAt(0) +
            parts[parts.length - 1].charAt(0)
        ).toUpperCase();
    }

    function formatLocation(profile) {
        return [
            profile?.city,
            profile?.state_region,
            profile?.country
        ]
            .filter(Boolean)
            .join(', ') || 'Location not provided';
    }

    function formatStudyMode(mode) {
        const labels = {
            online: 'Online',
            in_person: 'In Person',
            both: 'Online & In Person'
        };

        return labels[mode] || mode || 'Not specified';
    }

    function formatDate(value) {
        if (!value) {
            return 'Not specified';
        }

        const date = new Date(value + 'T00:00:00');

        if (Number.isNaN(date.getTime())) {
            return value;
        }

        return date.toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    function formatTime(value) {
        if (!value) {
            return '';
        }

        const parts = String(value).split(':');

        if (parts.length < 2) {
            return value;
        }

        const hours = Number(parts[0]);
        const minutes = parts[1];

        if (Number.isNaN(hours)) {
            return value;
        }

        const suffix = hours >= 12 ? 'PM' : 'AM';
        const displayHour = hours % 12 || 12;

        return `${displayHour}:${minutes} ${suffix}`;
    }

    function renderTags(elementId, values, emptyText) {
        const container = document.getElementById(elementId);

        if (!container) {
            return;
        }

        if (!Array.isArray(values) || !values.length) {
            container.innerHTML =
                `<span class="sm-match-tag">${escapeHtml(emptyText)}</span>`;
            return;
        }

        container.innerHTML = values
            .map(value =>
                `<span class="sm-match-tag">${escapeHtml(value)}</span>`
            )
            .join('');
    }

    function showError(message) {
        document.getElementById('profileLoading').hidden = true;
        document.getElementById('profileContent').hidden = true;
        document.getElementById('profileError').hidden = false;
        document.getElementById('profileErrorMessage').textContent = message;
    }

    async function requireUser() {
        const { data, error } =
            await supabaseClient.auth.getUser();

        if (error || !data.user) {
            window.location.href = 'login.html';
            return false;
        }

        currentUser = data.user;
        return true;
    }

    async function loadProfile() {
        const loadRequest = (async () => {
            const profileResult = await supabaseClient
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
                .eq('id', viewedUserId)
                .single();

            if (profileResult.error) {
                throw profileResult.error;
            }

            const studyResult = await supabaseClient
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
                .eq('user_id', viewedUserId)
                .single();

            if (studyResult.error) {
                throw studyResult.error;
            }

            if (!studyResult.data.is_active) {
                throw new Error(
                    'This study profile is currently unavailable.'
                );
            }

            renderProfile(profileResult.data, studyResult.data);
        })();

        const timeout = new Promise((_, reject) => {
            setTimeout(
                () => reject(new Error(
                    'Profile request timed out. Please refresh and try again.'
                )),
                10000
            );
        });

        await Promise.race([loadRequest, timeout]);
    }

    function renderProfile(profile, studyProfile) {
        const name = profile.display_name || 'Study Partner';

        document.title =
            `${name} — Study Profile | LearnForge StudyMatch`;

        document.getElementById('profileName').textContent = name;
        document.getElementById('profileNameCard').textContent = name;
        document.getElementById('profileLocation').textContent =
            formatLocation(profile);

        document.getElementById('profileAvatar').textContent =
            initials(name);

        document.getElementById('profileBio').textContent =
            profile.bio || 'No bio provided.';

        document.getElementById('profileExam').textContent =
            studyProfile.exam || 'Not specified';

        document.getElementById('profileExamDate').textContent =
            formatDate(studyProfile.exam_date);

        document.getElementById('profileStudyMode').textContent =
            formatStudyMode(studyProfile.study_mode);

        document.getElementById('profileTimezone').textContent =
            profile.timezone || 'Not specified';

        renderTags(
            'profileDays',
            studyProfile.available_days,
            'No days specified'
        );

        const start = formatTime(studyProfile.start_time);
        const end = formatTime(studyProfile.end_time);

        document.getElementById('profileTime').textContent =
            start && end
                ? `${start} – ${end}`
                : 'Time not specified';

        renderTags(
            'profileSubjects',
            studyProfile.subjects,
            'No subjects specified'
        );

        renderTags(
            'profileStyles',
            studyProfile.study_styles,
            'No study styles specified'
        );

        const messageButton =
            document.getElementById('messageProfileButton');

        if (messageButton) {
            messageButton.href =
                'chat.html?user=' +
                encodeURIComponent(viewedUserId);
        }

        document.getElementById('profileLoading').hidden = true;
        document.getElementById('profileContent').hidden = false;
    }

    async function signOut() {
        const { error } =
            await supabaseClient.auth.signOut();

        if (error) {
            alert(error.message);
            return;
        }

        window.location.href = 'login.html';
    }

    document.addEventListener(
        'DOMContentLoaded',
        async function () {
            const logoutLink =
                document.getElementById('logoutLink');

            if (logoutLink) {
                logoutLink.addEventListener(
                    'click',
                    function (event) {
                        event.preventDefault();
                        signOut();
                    }
                );
            }

            let authenticated;

            try {
                authenticated = await requireUser();
            } catch (error) {
                console.error(
                    'StudyMatch authentication failed:',
                    error
                );

                showError(
                    error.message ||
                    'Unable to verify your account.'
                );

                return;
            }

            if (!authenticated) {
                return;
            }

            viewedUserId =
                new URLSearchParams(window.location.search)
                    .get('user');

            if (!viewedUserId) {
                showError(
                    'No study partner was selected.'
                );
                return;
            }

            if (viewedUserId === currentUser.id) {
                window.location.href = 'profile.html';
                return;
            }

            try {
                await loadProfile();
            } catch (error) {
                console.error(
                    'Profile loading failed:',
                    error
                );

                showError(
                    error.message ||
                    'Unable to load this study profile.'
                );
            }
        }
    );
})();
