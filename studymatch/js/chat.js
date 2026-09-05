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
    let conversations = [];
    let activeConversation = null;
    let realtimeChannel = null;

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

    function formatTime(value) {
        if (!value) {
            return '';
        }

        const date = new Date(value);

        if (Number.isNaN(date.getTime())) {
            return '';
        }

        return date.toLocaleString([], {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
        });
    }

    function setVisible(id, visible) {
        const element = document.getElementById(id);

        if (element) {
            element.hidden = !visible;
        }
    }

    function showChatMessage(message) {
        const element = document.getElementById('chatMessage');

        if (element) {
            element.textContent = message || '';
        }
    }

    async function requireUser() {
        const { data, error } = await supabaseClient.auth.getSession();

        if (error) {
            console.error('Session check failed:', error);
            alert(error.message);
            return false;
        }

        if (!data.session) {
            window.location.href = 'login.html';
            return false;
        }

        currentUser = data.session.user;
        return true;
    }

    async function loadPartnerProfiles(userIds) {
        if (!userIds.length) {
            return {};
        }

        const { data, error } = await supabaseClient
            .from('profiles')
            .select('id, display_name, country, state_region, city, bio')
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

    async function loadConversations() {
        setVisible('conversationLoading', true);
        setVisible('conversationEmpty', false);

        const { data, error } = await supabaseClient
            .from('conversations')
            .select('id, user_a, user_b, created_at')
            .or(`user_a.eq.${currentUser.id},user_b.eq.${currentUser.id}`)
            .order('created_at', { ascending: false });

        if (error) {
            console.error('Conversation load failed:', error);
            setVisible('conversationLoading', false);
            showChatMessage(error.message);
            return;
        }

        conversations = data || [];

        const container = document.getElementById('conversationList');

        if (!conversations.length) {
            container.innerHTML = '';
            setVisible('conversationLoading', false);
            setVisible('conversationEmpty', true);
            return;
        }

        const partnerIds = conversations.map(conversation =>
            conversation.user_a === currentUser.id
                ? conversation.user_b
                : conversation.user_a
        );

        const profiles = await loadPartnerProfiles(partnerIds);

        container.innerHTML = conversations.map(conversation => {
            const partnerId =
                conversation.user_a === currentUser.id
                    ? conversation.user_b
                    : conversation.user_a;

            const profile = profiles[partnerId];
            const name = profile?.display_name || 'Study Partner';

            return `
                <button
                    type="button"
                    class="sm-conversation-item"
                    data-conversation-id="${escapeHtml(conversation.id)}"
                >
                    <span class="sm-conversation-avatar">
                        ${escapeHtml(initials(name))}
                    </span>

                    <span class="sm-conversation-info">
                        <strong>${escapeHtml(name)}</strong>
                        <small>${escapeHtml(formatLocation(profile))}</small>
                    </span>
                </button>
            `;
        }).join('');

        setVisible('conversationLoading', false);
        setVisible('conversationEmpty', false);

        await Promise.all(
            conversations.map(async conversation => {
                conversation.partnerId =
                    conversation.user_a === currentUser.id
                        ? conversation.user_b
                        : conversation.user_a;

                conversation.partnerProfile =
                    profiles[conversation.partnerId] || {};
            })
        );
    }

    async function openConversation(conversationId) {
        const conversation = conversations.find(
            item => item.id === conversationId
        );

        if (!conversation) {
            return;
        }

        activeConversation = conversation;

        const profile = conversation.partnerProfile || {};
        const name = profile.display_name || 'Study Partner';

        document.getElementById('chatAvatar').textContent = initials(name);
        document.getElementById('chatPartnerName').textContent = name;
        document.getElementById('chatPartnerLocation').textContent =
            formatLocation(profile);

        setVisible('chatEmptyState', false);
        setVisible('chatPanel', true);
        showChatMessage('');

        document
            .querySelectorAll('.sm-conversation-item')
            .forEach(item => {
                item.classList.toggle(
                    'active',
                    item.dataset.conversationId === conversationId
                );
            });

        await loadMessages();
        subscribeToMessages();
    }

    async function loadMessages() {
        if (!activeConversation) {
            return;
        }

        setVisible('messageLoading', true);

        const { data, error } = await supabaseClient
            .from('messages')
            .select('id, conversation_id, sender_id, body, created_at')
            .eq('conversation_id', activeConversation.id)
            .order('created_at', { ascending: true });

        if (error) {
            console.error('Message load failed:', error);
            setVisible('messageLoading', false);
            showChatMessage(error.message);
            return;
        }

        renderMessages(data || []);
        setVisible('messageLoading', false);
    }

    function renderMessages(messages) {
        const container = document.getElementById('messageList');

        if (!messages.length) {
            container.innerHTML = `
                <div class="sm-chat-no-messages">
                    <p>No messages yet. Start the conversation.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = messages.map(message => {
            const mine = message.sender_id === currentUser.id;

            return `
                <div class="sm-message-row ${mine ? 'mine' : 'theirs'}">
                    <div class="sm-message-bubble">
                        <div class="sm-message-body">
                            ${escapeHtml(message.body)}
                        </div>

                        <time class="sm-message-time">
                            ${escapeHtml(formatTime(message.created_at))}
                        </time>
                    </div>
                </div>
            `;
        }).join('');

        container.scrollTop = container.scrollHeight;
    }

    function subscribeToMessages() {
        if (realtimeChannel) {
            supabaseClient.removeChannel(realtimeChannel);
            realtimeChannel = null;
        }

        if (!activeConversation) {
            return;
        }

        realtimeChannel = supabaseClient
            .channel(`messages:${activeConversation.id}`)
            .on(
                'postgres_changes',
                {
                    event: 'INSERT',
                    schema: 'public',
                    table: 'messages',
                    filter: `conversation_id=eq.${activeConversation.id}`
                },
                function () {
                    loadMessages();
                }
            )
            .subscribe();
    }

    async function sendMessage(event) {
        event.preventDefault();

        if (!activeConversation) {
            return;
        }

        const input = document.getElementById('messageInput');
        const button = document.getElementById('sendMessageButton');

        const body = input.value.trim();

        if (!body) {
            return;
        }

        input.disabled = true;
        button.disabled = true;
        button.textContent = 'Sending...';
        showChatMessage('');

        const { error } = await supabaseClient
            .from('messages')
            .insert({
                conversation_id: activeConversation.id,
                sender_id: currentUser.id,
                body
            });

        if (error) {
            console.error('Send message failed:', error);
            showChatMessage(error.message);
            input.disabled = false;
            button.disabled = false;
            button.textContent = 'Send';
            return;
        }

        input.value = '';
        input.disabled = false;
        button.disabled = false;
        button.textContent = 'Send';

        await loadMessages();
        input.focus();
    }

    async function signOut() {
        const { error } = await supabaseClient.auth.signOut();

        if (error) {
            console.error('Sign out failed:', error);
            alert(error.message);
            return;
        }

        if (realtimeChannel) {
            await supabaseClient.removeChannel(realtimeChannel);
        }

        window.location.href = 'login.html';
    }

    document.addEventListener('click', async function (event) {
        const item = event.target.closest('[data-conversation-id]');

        if (!item) {
            return;
        }

        await openConversation(item.dataset.conversationId);
    });

    document.addEventListener('DOMContentLoaded', async function () {
        const logoutLink = document.getElementById('logoutLink');
        const messageForm = document.getElementById('messageForm');

        if (logoutLink) {
            logoutLink.addEventListener('click', function (event) {
                event.preventDefault();
                signOut();
            });
        }

        if (messageForm) {
            messageForm.addEventListener('submit', sendMessage);
        }

        const authenticated = await requireUser();

        if (!authenticated) {
            return;
        }

        try {
            await loadConversations();
        } catch (error) {
            console.error('Chat page failed:', error);
            showChatMessage(
                error.message || 'Unable to load conversations.'
            );
        }
    });
})();
