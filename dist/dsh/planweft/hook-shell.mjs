// Only the official command-hook bridge sees this shell facade. Delegating
// resolve/run preserves the host's sandbox and all non-context decisions.
export function hookShell(shell) {
  const reminded = new Map();
  const payloadOf = (spec) => {
    try {
      const payload = JSON.parse(spec.stdin);
      return typeof payload.session_id === 'string' && /^[A-Za-z0-9_-]{1,128}$/.test(payload.session_id)
        ? payload : null;
    } catch { return null; }
  };
  return {
    resolve(request) {
      const payload = payloadOf(request);
      return shell.resolve(payload ? {...request, env: {...request.env, PWF_SESSION_ID: payload.session_id}} : request);
    },
    async run(spec) {
      const payload = payloadOf(spec);
      if (['SessionStart', 'UserPromptSubmit'].includes(payload?.hook_event_name)) reminded.delete(payload.session_id);
      const result = await shell.run(spec);
      if (!payload || payload.hook_event_name !== 'PostToolUse' || result.exitCode !== 0) return result;
      let output;
      try { output = JSON.parse(result.stdout.text); } catch { return result; }
      if (!output || typeof output !== 'object' || Array.isArray(output)) return result;
      const context = output.hookSpecificOutput?.additionalContext;
      if (output.hookSpecificOutput?.hookEventName !== 'PostToolUse' || typeof context !== 'string' || !context.startsWith('[planweft]')) return result;
      if (!reminded.has(payload.session_id)) {
        reminded.set(payload.session_id, true);
        if (reminded.size > 1024) reminded.delete(reminded.keys().next().value);
        return result;
      }
      // Keep errors, permissions, other output keys and stream metadata intact.
      delete output.hookSpecificOutput.additionalContext;
      return {...result, stdout: {...result.stdout, text: JSON.stringify(output)}};
    },
  };
}
