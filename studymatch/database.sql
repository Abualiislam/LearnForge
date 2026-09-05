-- ============================================================
-- LearnForge StudyMatch — Database Foundation
-- ============================================================

create extension if not exists pgcrypto;

-- ============================================================
-- 1. PROFILES
-- ============================================================

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text not null check (char_length(display_name) between 2 and 80),
    country text,
    state_region text,
    city text,
    timezone text,
    bio text check (bio is null or char_length(bio) <= 500),
    avatar_url text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ============================================================
-- 2. STUDY PROFILES
-- ============================================================

create table if not exists public.study_profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique references public.profiles(id) on delete cascade,

    exam text not null,
    exam_date date,

    study_mode text not null default 'online'
        check (study_mode in ('online', 'in_person', 'both')),

    available_days text[] not null default '{}',
    start_time time,
    end_time time,

    subjects text[] not null default '{}',
    study_styles text[] not null default '{}',

    is_active boolean not null default true,

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- ============================================================
-- 3. CONNECTION REQUESTS
-- ============================================================

create table if not exists public.connection_requests (
    id uuid primary key default gen_random_uuid(),

    sender_id uuid not null references public.profiles(id) on delete cascade,
    receiver_id uuid not null references public.profiles(id) on delete cascade,

    status text not null default 'pending'
        check (status in ('pending', 'accepted', 'rejected', 'cancelled')),

    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    check (sender_id <> receiver_id)
);

-- ============================================================
-- 4. CONNECTIONS
-- ============================================================

create table if not exists public.connections (
    id uuid primary key default gen_random_uuid(),

    user_a uuid not null references public.profiles(id) on delete cascade,
    user_b uuid not null references public.profiles(id) on delete cascade,

    created_at timestamptz not null default now(),

    check (user_a <> user_b),
    check (user_a < user_b),

    unique (user_a, user_b)
);

-- ============================================================
-- 5. CONVERSATIONS
-- ============================================================

create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),

    user_a uuid not null references public.profiles(id) on delete cascade,
    user_b uuid not null references public.profiles(id) on delete cascade,

    created_at timestamptz not null default now(),

    check (user_a <> user_b),
    check (user_a < user_b),

    unique (user_a, user_b)
);

-- ============================================================
-- 6. MESSAGES
-- ============================================================

create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),

    conversation_id uuid not null
        references public.conversations(id) on delete cascade,

    sender_id uuid not null
        references public.profiles(id) on delete cascade,

    message text not null
        check (char_length(message) between 1 and 2000),

    created_at timestamptz not null default now(),
    read_at timestamptz
);

-- ============================================================
-- 7. BLOCKS
-- ============================================================

create table if not exists public.blocks (
    id uuid primary key default gen_random_uuid(),

    blocker_id uuid not null references public.profiles(id) on delete cascade,
    blocked_id uuid not null references public.profiles(id) on delete cascade,

    created_at timestamptz not null default now(),

    check (blocker_id <> blocked_id),

    unique (blocker_id, blocked_id)
);

-- ============================================================
-- 8. REPORTS
-- ============================================================

create table if not exists public.reports (
    id uuid primary key default gen_random_uuid(),

    reporter_id uuid not null references public.profiles(id) on delete cascade,
    reported_id uuid not null references public.profiles(id) on delete cascade,

    reason text not null
        check (reason in (
            'spam',
            'harassment',
            'scam',
            'fake_profile',
            'inappropriate',
            'other'
        )),

    details text
        check (details is null or char_length(details) <= 2000),

    status text not null default 'open'
        check (status in ('open', 'reviewing', 'resolved', 'dismissed')),

    created_at timestamptz not null default now(),

    check (reporter_id <> reported_id)
);

-- ============================================================
-- 9. INDEXES
-- ============================================================

create index if not exists idx_profiles_city
    on public.profiles(city);

create index if not exists idx_profiles_state_region
    on public.profiles(state_region);

create index if not exists idx_study_profiles_exam
    on public.study_profiles(exam);

create index if not exists idx_study_profiles_active
    on public.study_profiles(is_active);

create index if not exists idx_connection_requests_receiver
    on public.connection_requests(receiver_id);

create index if not exists idx_connection_requests_sender
    on public.connection_requests(sender_id);

create index if not exists idx_messages_conversation
    on public.messages(conversation_id, created_at);

create index if not exists idx_blocks_blocker
    on public.blocks(blocker_id);

create index if not exists idx_reports_status
    on public.reports(status);

-- ============================================================
-- 10. ROW LEVEL SECURITY
-- ============================================================

alter table public.profiles enable row level security;
alter table public.study_profiles enable row level security;
alter table public.connection_requests enable row level security;
alter table public.connections enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.blocks enable row level security;
alter table public.reports enable row level security;

-- ============================================================
-- 11. PROFILE POLICIES
-- ============================================================

create policy "profiles_select_authenticated"
on public.profiles
for select
to authenticated
using (true);

create policy "profiles_insert_own"
on public.profiles
for insert
to authenticated
with check (auth.uid() = id);

create policy "profiles_update_own"
on public.profiles
for update
to authenticated
using (auth.uid() = id)
with check (auth.uid() = id);

create policy "profiles_delete_own"
on public.profiles
for delete
to authenticated
using (auth.uid() = id);

-- ============================================================
-- 12. STUDY PROFILE POLICIES
-- ============================================================

create policy "study_profiles_select_active"
on public.study_profiles
for select
to authenticated
using (is_active = true or auth.uid() = user_id);

create policy "study_profiles_insert_own"
on public.study_profiles
for insert
to authenticated
with check (auth.uid() = user_id);

create policy "study_profiles_update_own"
on public.study_profiles
for update
to authenticated
using (auth.uid() = user_id)
with check (auth.uid() = user_id);

create policy "study_profiles_delete_own"
on public.study_profiles
for delete
to authenticated
using (auth.uid() = user_id);

-- ============================================================
-- 13. CONNECTION REQUEST POLICIES
-- ============================================================

create policy "connection_requests_select_participant"
on public.connection_requests
for select
to authenticated
using (
    auth.uid() = sender_id
    or auth.uid() = receiver_id
);

create policy "connection_requests_insert_sender"
on public.connection_requests
for insert
to authenticated
with check (
    auth.uid() = sender_id
    and sender_id <> receiver_id
);

create policy "connection_requests_update_participant"
on public.connection_requests
for update
to authenticated
using (
    auth.uid() = sender_id
    or auth.uid() = receiver_id
)
with check (
    auth.uid() = sender_id
    or auth.uid() = receiver_id
);

-- ============================================================
-- 14. CONNECTION POLICIES
-- ============================================================

create policy "connections_select_participant"
on public.connections
for select
to authenticated
using (
    auth.uid() = user_a
    or auth.uid() = user_b
);

-- ============================================================
-- 15. CONVERSATION POLICIES
-- ============================================================

create policy "conversations_select_participant"
on public.conversations
for select
to authenticated
using (
    auth.uid() = user_a
    or auth.uid() = user_b
);

-- ============================================================
-- 16. MESSAGE POLICIES
-- ============================================================

create policy "messages_select_participant"
on public.messages
for select
to authenticated
using (
    exists (
        select 1
        from public.conversations c
        where c.id = conversation_id
        and (c.user_a = auth.uid() or c.user_b = auth.uid())
    )
);

create policy "messages_insert_participant"
on public.messages
for insert
to authenticated
with check (
    auth.uid() = sender_id
    and exists (
        select 1
        from public.conversations c
        where c.id = conversation_id
        and (c.user_a = auth.uid() or c.user_b = auth.uid())
    )
);

-- ============================================================
-- 17. BLOCK POLICIES
-- ============================================================

create policy "blocks_select_own"
on public.blocks
for select
to authenticated
using (auth.uid() = blocker_id);

create policy "blocks_insert_own"
on public.blocks
for insert
to authenticated
with check (auth.uid() = blocker_id);

create policy "blocks_delete_own"
on public.blocks
for delete
to authenticated
using (auth.uid() = blocker_id);

-- ============================================================
-- 18. REPORT POLICIES
-- ============================================================

create policy "reports_insert_own"
on public.reports
for insert
to authenticated
with check (auth.uid() = reporter_id);

create policy "reports_select_own"
on public.reports
for select
to authenticated
using (auth.uid() = reporter_id);

-- ============================================================
-- END
-- ============================================================

-- ============================================================
-- SECURITY PATCH / MVP HARDENING
-- ============================================================

drop policy if exists "connection_requests_update_participant"
on public.connection_requests;

create policy "connection_requests_update_receiver"
on public.connection_requests
for update
to authenticated
using (auth.uid() = receiver_id)
with check (
    auth.uid() = receiver_id
    and status in ('accepted', 'rejected')
);

create policy "connection_requests_cancel_sender"
on public.connection_requests
for update
to authenticated
using (auth.uid() = sender_id)
with check (
    auth.uid() = sender_id
    and status = 'cancelled'
);

create unique index if not exists idx_unique_pending_connection
on public.connection_requests(sender_id, receiver_id)
where status = 'pending';

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists profiles_set_updated_at
on public.profiles;

create trigger profiles_set_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

drop trigger if exists study_profiles_set_updated_at
on public.study_profiles;

create trigger study_profiles_set_updated_at
before update on public.study_profiles
for each row
execute function public.set_updated_at();

drop trigger if exists connection_requests_set_updated_at
on public.connection_requests;

create trigger connection_requests_set_updated_at
before update on public.connection_requests
for each row
execute function public.set_updated_at();

-- ============================================================
-- END SECURITY PATCH
-- ============================================================

-- ============================================================
-- SECURE CONNECTION ACCEPTANCE RPC
-- ============================================================

create or replace function public.accept_connection_request(
    p_request_id uuid
)
returns table (
    connection_id uuid,
    conversation_id uuid
)
language plpgsql
security definer
set search_path = public, pg_catalog
as $$
declare
    v_sender uuid;
    v_receiver uuid;
    v_user_a uuid;
    v_user_b uuid;
    v_connection_id uuid;
    v_conversation_id uuid;
begin
    -- The caller must be authenticated.
    if auth.uid() is null then
        raise exception 'Authentication required';
    end if;

    -- Lock the request row while processing it.
    select
        sender_id,
        receiver_id
    into
        v_sender,
        v_receiver
    from public.connection_requests
    where id = p_request_id
      and status = 'pending'
    for update;

    if v_sender is null then
        raise exception 'Pending connection request not found';
    end if;

    -- Only the receiver may accept the request.
    if auth.uid() <> v_receiver then
        raise exception 'Only the receiver can accept this request';
    end if;

    -- Do not allow connections when either user has blocked the other.
    if exists (
        select 1
        from public.blocks b
        where (b.blocker_id = v_sender and b.blocked_id = v_receiver)
           or (b.blocker_id = v_receiver and b.blocked_id = v_sender)
    ) then
        raise exception 'Connection blocked';
    end if;

    -- Normalize the user pair to satisfy user_a < user_b.
    if v_sender < v_receiver then
        v_user_a := v_sender;
        v_user_b := v_receiver;
    else
        v_user_a := v_receiver;
        v_user_b := v_sender;
    end if;

    -- Accept the request.
    update public.connection_requests
    set status = 'accepted',
        updated_at = now()
    where id = p_request_id;

    -- Create the connection if it does not already exist.
    insert into public.connections (user_a, user_b)
    values (v_user_a, v_user_b)
    on conflict (user_a, user_b) do nothing
    returning id into v_connection_id;

    -- If it already existed, retrieve it.
    if v_connection_id is null then
        select id
        into v_connection_id
        from public.connections
        where user_a = v_user_a
          and user_b = v_user_b;
    end if;

    -- Create the private conversation if it does not already exist.
    insert into public.conversations (user_a, user_b)
    values (v_user_a, v_user_b)
    on conflict (user_a, user_b) do nothing
    returning id into v_conversation_id;

    -- If it already existed, retrieve it.
    if v_conversation_id is null then
        select id
        into v_conversation_id
        from public.conversations
        where user_a = v_user_a
          and user_b = v_user_b;
    end if;

    return query
    select v_connection_id, v_conversation_id;
end;
$$;

-- Remove any broader/default execute permission first.
revoke all on function public.accept_connection_request(uuid)
from public;

-- Only signed-in users may call the RPC.
grant execute on function public.accept_connection_request(uuid)
to authenticated;

-- ============================================================
-- END SECURE CONNECTION ACCEPTANCE RPC
-- ============================================================

-- ============================================================
-- BLOCK-AWARE ACCESS HARDENING
-- Keep connections, conversations, and messages inaccessible
-- when either participant has blocked the other.
-- ============================================================

drop policy if exists "connections_select_participant"
on public.connections;

create policy "connections_select_participant"
on public.connections
for select
to authenticated
using (
    (auth.uid() = user_a or auth.uid() = user_b)
    and not exists (
        select 1
        from public.blocks b
        where
            (b.blocker_id = auth.uid() and b.blocked_id = case
                when auth.uid() = user_a then user_b
                else user_a
            end)
            or
            (b.blocker_id = case
                when auth.uid() = user_a then user_b
                else user_a
            end
            and b.blocked_id = auth.uid())
    )
);

drop policy if exists "conversations_select_participant"
on public.conversations;

create policy "conversations_select_participant"
on public.conversations
for select
to authenticated
using (
    (auth.uid() = user_a or auth.uid() = user_b)
    and not exists (
        select 1
        from public.blocks b
        where
            (b.blocker_id = auth.uid() and b.blocked_id = case
                when auth.uid() = user_a then user_b
                else user_a
            end)
            or
            (b.blocker_id = case
                when auth.uid() = user_a then user_b
                else user_a
            end
            and b.blocked_id = auth.uid())
    )
);

drop policy if exists "messages_select_participant"
on public.messages;

create policy "messages_select_participant"
on public.messages
for select
to authenticated
using (
    exists (
        select 1
        from public.conversations c
        where c.id = conversation_id
        and (c.user_a = auth.uid() or c.user_b = auth.uid())
        and not exists (
            select 1
            from public.blocks b
            where
                (b.blocker_id = auth.uid() and b.blocked_id = case
                    when auth.uid() = c.user_a then c.user_b
                    else c.user_a
                end)
                or
                (b.blocker_id = case
                    when auth.uid() = c.user_a then c.user_b
                    else c.user_a
                end
                and b.blocked_id = auth.uid())
        )
    )
);

drop policy if exists "messages_insert_participant"
on public.messages;

create policy "messages_insert_participant"
on public.messages
for insert
to authenticated
with check (
    auth.uid() = sender_id
    and exists (
        select 1
        from public.conversations c
        where c.id = conversation_id
        and (c.user_a = auth.uid() or c.user_b = auth.uid())
        and not exists (
            select 1
            from public.blocks b
            where
                (b.blocker_id = auth.uid() and b.blocked_id = case
                    when auth.uid() = c.user_a then c.user_b
                    else c.user_a
                end)
                or
                (b.blocker_id = case
                    when auth.uid() = c.user_a then c.user_b
                    else c.user_a
                end
                and b.blocked_id = auth.uid())
        )
    )
);
