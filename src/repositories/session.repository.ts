import { pool } from '../infrastructure/database.js';

export async function listSessions(): Promise<Record<string, unknown>[]> {
    return (await pool.query('SELECT * FROM sessions ORDER BY updated_at DESC'))
        .rows;
}

export async function findSessionDetails(sessionId: string): Promise<{
    session: Record<string, unknown> | undefined;
    messages: Record<string, unknown>[];
    runs: Record<string, unknown>[];
}> {
    const [session, messages, runs,toolCalls] = await Promise.all([
        pool.query('SELECT * FROM sessions WHERE id = $1', [sessionId]),
        pool.query(
            'SELECT * FROM messages WHERE session_id = $1 ORDER BY created_at',
            [sessionId],
        ),
        pool.query(
            'SELECT * FROM runs WHERE session_id = $1 ORDER BY created_at',
            [sessionId],
        ),
        pool.query(
            `SELECT tool_calls.*
                               FROM tool_calls
                               JOIN runs ON runs.id = tool_calls.run_id
                               WHERE runs.session_id = $1
                               ORDER BY tool_calls.created_at`,
            [sessionId],
        ),
    ]);

    const toolCallsByRunId = new Map<string, Record<string, unknown>[]>();
    for (const toolCall of toolCalls.rows){
        const runId = String(toolCall.run_id);
        const items = toolCallsByRunId.get(runId) ?? [];
        items.push(toolCall);
        toolCallsByRunId.set(runId, items);
    }

    const runsWithToolCalls = runs.rows.map((run) => ({
        ...run,
        tool_calls: toolCallsByRunId.get(String(run.id)) ?? [],
    }));
    return {
        session: session.rows[0],
        messages: messages.rows,
        runs: runsWithToolCalls,
    };
}
