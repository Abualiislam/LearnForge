(function () {
    'use strict';

    const config = window.STUDYMATCH_CONFIG;

    if (!config || !window.supabase) {
        console.error('StudyMatch configuration or Supabase library is missing.');
        return;
    }

    const supabaseClient = window.studyMatchSupabase ||
        window.supabase.createClient(
            config.supabaseUrl,
            config.supabaseKey
        );

    const form = document.getElementById('profileForm');
    const message = document.getElementById('profileMessage');
    const logoutLink = document.getElementById('logoutLink');

    async function requireUser() {
        const { data, error } = await supabaseClient.auth.getSession();

        if (error || !data.session) {
            window.location.href = 'login.html';
            return null;
        }

        return data.session.user;
    }

    function getCheckedValues(name) {
        return Array.from(
            document.querySelectorAll(
                'input[name="' + name + '"]:checked'
            )
        ).map(function (input) {
            return input.value;
        });
    }

    function setCheckedValues(name, values) {
        const selected = new Set(values || []);

        document
            .querySelectorAll('input[name="' + name + '"]')
            .forEach(function (input) {
                input.checked = selected.has(input.value);
            });
    }

    async function loadBasicProfile(user) {
        const { data, error } = await supabaseClient
            .from('profiles')
            .select(
                'display_name, country, state_region, city, timezone, bio'
            )
            .eq('id', user.id)
            .maybeSingle();

        if (error) {
            console.error('Profile load failed:', error);
            throw new Error('Could not load your profile.');
        }

        if (!data) {
            return;
        }

        document.getElementById('displayName').value =
            data.display_name || '';

        document.getElementById('country').value =
            data.country || '';

        document.getElementById('region').value =
            data.state_region || '';

        document.getElementById('city').value =
            data.city || '';

        document.getElementById('timezone').value =
            data.timezone ||
            Intl.DateTimeFormat().resolvedOptions().timeZone ||
            '';

        document.getElementById('bio').value =
            data.bio || '';
    }

    async function loadStudyProfile(user) {
        const { data, error } = await supabaseClient
            .from('study_profiles')
            .select(
                'exam, exam_date, study_mode, available_days, ' +
                'start_time, end_time, subjects, study_styles, is_active'
            )
            .eq('user_id', user.id)
            .maybeSingle();

        if (error) {
            console.error('Study profile load failed:', error);
            throw new Error('Could not load your study preferences.');
        }

        if (!data) {
            return;
        }

        document.getElementById('exam').value =
            data.exam || '';

        document.getElementById('examDate').value =
            data.exam_date || '';

        document.getElementById('studyMode').value =
            data.study_mode || 'online';

        document.getElementById('startTime').value =
            data.start_time
                ? data.start_time.slice(0, 5)
                : '';

        document.getElementById('endTime').value =
            data.end_time
                ? data.end_time.slice(0, 5)
                : '';

        setCheckedValues(
            'availableDays',
            data.available_days
        );

        setCheckedValues(
            'subjects',
            data.subjects
        );

        setCheckedValues(
            'studyStyles',
            data.study_styles
        );

        document.getElementById('isActive').checked =
            data.is_active !== false;
    }

    async function loadAll(user) {
        try {
            await loadBasicProfile(user);
            await loadStudyProfile(user);
        } catch (error) {
            console.error(error);
            message.textContent = error.message;
        }
    }

    async function saveBasicProfile(user) {
        const profile = {
            id: user.id,
            display_name:
                document.getElementById('displayName').value.trim(),
            country:
                document.getElementById('country').value.trim(),
            state_region:
                document.getElementById('region').value.trim(),
            city:
                document.getElementById('city').value.trim(),
            timezone:
                document.getElementById('timezone').value.trim(),
            bio:
                document.getElementById('bio').value.trim()
        };

        if (!profile.display_name || !profile.country) {
            throw new Error(
                'Display name and country are required.'
            );
        }

        const { error } = await supabaseClient
            .from('profiles')
            .upsert(profile, {
                onConflict: 'id'
            });

        if (error) {
            console.error('Basic profile save failed:', error);
            throw new Error(error.message);
        }
    }

    async function saveStudyProfile(user) {
        const exam =
            document.getElementById('exam').value;

        const examDate =
            document.getElementById('examDate').value || null;

        const studyMode =
            document.getElementById('studyMode').value;

        const availableDays =
            getCheckedValues('availableDays');

        const subjects =
            getCheckedValues('subjects');

        const studyStyles =
            getCheckedValues('studyStyles');

        const startTime =
            document.getElementById('startTime').value || null;

        const endTime =
            document.getElementById('endTime').value || null;

        const isActive =
            document.getElementById('isActive').checked;

        if (!exam) {
            throw new Error('Please select your exam.');
        }

        if (!availableDays.length) {
            throw new Error(
                'Please select at least one available day.'
            );
        }

        if (!subjects.length) {
            throw new Error(
                'Please select at least one subject.'
            );
        }

        if (!studyStyles.length) {
            throw new Error(
                'Please select at least one study style.'
            );
        }

        if (
            startTime &&
            endTime &&
            startTime >= endTime
        ) {
            throw new Error(
                'Available Until must be later than Available From.'
            );
        }

        const studyProfile = {
            user_id: user.id,
            exam: exam,
            exam_date: examDate,
            study_mode: studyMode,
            available_days: availableDays,
            start_time: startTime,
            end_time: endTime,
            subjects: subjects,
            study_styles: studyStyles,
            is_active: isActive
        };

        const { error } = await supabaseClient
            .from('study_profiles')
            .upsert(studyProfile, {
                onConflict: 'user_id'
            });

        if (error) {
            console.error(
                'Study profile save failed:',
                error
            );
            throw new Error(error.message);
        }
    }

    async function saveAll(event) {
        event.preventDefault();

        const user = await requireUser();

        if (!user) {
            return;
        }

        const button =
            form.querySelector('button[type="submit"]');

        button.disabled = true;
        button.textContent = 'Saving...';
        message.textContent = '';

        try {
            await saveBasicProfile(user);
            await saveStudyProfile(user);

            message.textContent =
                'Profile and study preferences saved successfully.';
        } catch (error) {
            console.error('Save failed:', error);
            message.textContent = error.message;
        } finally {
            button.disabled = false;
            button.textContent = 'Save Study Profile';
        }
    }

    async function logout(event) {
        event.preventDefault();

        const { error } =
            await supabaseClient.auth.signOut();

        if (error) {
            console.error('Sign out failed:', error);
            return;
        }

        window.location.href = 'login.html';
    }

    document.addEventListener(
        'DOMContentLoaded',
        async function () {
            if (!form) {
                return;
            }

            form.addEventListener('submit', saveAll);

            if (logoutLink) {
                logoutLink.addEventListener(
                    'click',
                    logout
                );
            }

            const user = await requireUser();

            if (user) {
                await loadAll(user);
            }
        }
    );
})();
