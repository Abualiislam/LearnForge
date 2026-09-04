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

    window.studyMatchSupabase = supabaseClient;

    async function redirectIfAuthenticated() {
        const { data, error } = await supabaseClient.auth.getSession();

        if (error) {
            console.error('Session check failed:', error);
            return;
        }

        if (data.session) {
            window.location.href = 'profile.html';
        }
    }

    async function handleLogin(event) {
        event.preventDefault();

        const form = event.currentTarget;
        const email = form.email.value.trim();
        const password = form.password.value;
        const message = document.getElementById('loginMessage');
        const button = form.querySelector('button[type="submit"]');

        message.textContent = '';

        if (!email || !password) {
            message.textContent = 'Please enter your email and password.';
            return;
        }

        button.disabled = true;
        button.textContent = 'Signing in...';

        const { data, error } =
            await supabaseClient.auth.signInWithPassword({
                email,
                password
            });

        if (error) {
            console.error('Login failed:', error);
            message.textContent = error.message;
            button.disabled = false;
            button.textContent = 'Sign In';
            return;
        }

        if (data.session) {
            window.location.href = 'profile.html';
        }
    }

    async function handleSignup(event) {
        event.preventDefault();

        const form = event.currentTarget;
        const email = form.email.value.trim();
        const password = form.password.value;
        const passwordConfirm = form.passwordConfirm.value;
        const message = document.getElementById('signupMessage');
        const button = form.querySelector('button[type="submit"]');

        message.textContent = '';

        if (!email || !password || !passwordConfirm) {
            message.textContent = 'Please complete all fields.';
            return;
        }

        if (password.length < 8) {
            message.textContent =
                'Password must be at least 8 characters.';
            return;
        }

        if (password !== passwordConfirm) {
            message.textContent = 'Passwords do not match.';
            return;
        }

        button.disabled = true;
        button.textContent = 'Creating account...';

        const { data, error } = await supabaseClient.auth.signUp({
            email,
            password,
            options: {
                emailRedirectTo: 'https://abualiislam.github.io/LearnForge/studymatch/login.html'
            }
        });

        if (error) {
            console.error('Signup failed:', error);
            message.textContent = error.message;
            button.disabled = false;
            button.textContent = 'Create Account';
            return;
        }

        if (data.session) {
            window.location.href = 'profile.html';
            return;
        }

        message.textContent =
            'Account created. Please check your email to confirm your account, then sign in.';

        button.disabled = false;
        button.textContent = 'Create Account';
    }

    document.addEventListener('DOMContentLoaded', function () {
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');

        if (loginForm) {
            loginForm.addEventListener('submit', handleLogin);
            redirectIfAuthenticated();
        }

        if (signupForm) {
            signupForm.addEventListener('submit', handleSignup);
            redirectIfAuthenticated();
        }
    });
})();
