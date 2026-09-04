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

    async function loadProfile(user) {
        const { data, error } = await supabaseClient
            .from('profiles')
            .select('display_name, country, state_region, city, timezone, bio')
            .eq('id', user.id)
            .maybeSingle();

        if (error) {
            console.error('Profile load failed:', error);
            message.textContent = 'Could not load your profile.';
            return;
        }

        if (!data) {
            return;
        }

        document.getElementById('displayName').value = data.display_name || '';
        document.getElementById('country').value = data.country || '';
        document.getElementById('region').value = data.state_region || '';
        document.getElementById('city').value = data.city || '';
        document.getElementById('timezone').value =
            data.timezone || Intl.DateTimeFormat().resolvedOptions().timeZone || '';
        document.getElementById('bio').value = data.bio || '';
    }

    async function saveProfile(event) {
        event.preventDefault();

        const user = await requireUser();
        if (!user) return;

        const button = form.querySelector('button[type="submit"]');

        const profile = {
            id: user.id,
            display_name: document.getElementById('displayName').value.trim(),
            country: document.getElementById('country').value.trim(),
            state_region: document.getElementById('region').value.trim(),
            city: document.getElementById('city').value.trim(),
            timezone: document.getElementById('timezone').value.trim(),
            bio: document.getElementById('bio').value.trim()
        };

        if (!profile.display_name || !profile.country) {
            message.textContent = 'Display name and country are required.';
            return;
        }

        button.disabled = true;
        button.textContent = 'Saving...';
        message.textContent = '';

        const { error } = await supabaseClient
            .from('profiles')
            .upsert(profile, { onConflict: 'id' });

        if (error) {
            console.error('Profile save failed:', error);
            message.textContent = error.message;
            button.disabled = false;
            button.textContent = 'Save Profile';
            return;
        }

        message.textContent = 'Profile saved successfully.';
        button.disabled = false;
        button.textContent = 'Save Profile';
    }

    async function logout(event) {
        event.preventDefault();

        const { error } = await supabaseClient.auth.signOut();

        if (error) {
            console.error('Sign out failed:', error);
            return;
        }

        window.location.href = 'login.html';
    }

    document.addEventListener('DOMContentLoaded', async function () {
        if (!form) return;

        form.addEventListener('submit', saveProfile);

        if (logoutLink) {
            logoutLink.addEventListener('click', logout);
        }

        const user = await requireUser();

        if (user) {
            await loadProfile(user);
        }
    });
})();
