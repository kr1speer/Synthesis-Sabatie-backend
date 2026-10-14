local sessions = {}

for _, session_key in ipairs(redis.call('KEYS', 'session:*')) do

    local session_id = string.sub(session_key, 9)
    local chemist_login = redis.call('HGET', session_key, 'chemist_login')
    table.insert(sessions, {session_id, chemist_login})

end

return sessions
