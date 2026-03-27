const WECHAT_ARTICLE_PATTERN = /^https:\/\/mp\.weixin\.qq\.com\/\S+$/;
const GITHUB_OWNER = 'rianlu';
const GITHUB_REPO = 'xixun-parser';

export function extractWeChatUrl(text) {
  const normalized = `${text ?? ''}`.trim();
  if (!normalized || !WECHAT_ARTICLE_PATTERN.test(normalized)) {
    return null;
  }

  return normalized;
}

export function buildDispatchPayload({ ref, url, chatId }) {
  return {
    ref,
    inputs: {
      url,
      chat_id: String(chatId),
    },
  };
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
    },
  });
}

function getTelegramMessage(update) {
  return (
    update?.message ||
    update?.channel_post ||
    update?.edited_message ||
    update?.edited_channel_post ||
    null
  );
}

function extractTelegramContext(update) {
  const message = getTelegramMessage(update);
  if (!message) {
    return null;
  }

  return {
    chatId: message.chat?.id ?? null,
    messageId: message.message_id ?? null,
    text: message.text ?? '',
  };
}

async function sendTelegramMessage(env, { chatId, text, replyToMessageId }) {
  const body = new URLSearchParams();
  body.set('chat_id', String(chatId));
  body.set('text', text);
  body.set('disable_web_page_preview', 'true');
  if (replyToMessageId) {
    body.set('reply_to_message_id', String(replyToMessageId));
  }

  const response = await fetch(
    `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`,
    {
      method: 'POST',
      headers: {
        'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
      body,
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Telegram sendMessage failed: ${response.status} ${errorText}`);
  }
}

async function dispatchGitHubWorkflow(env, payload) {
  const workflowFile = env.GITHUB_WORKFLOW_FILE || 'sync.yml';
  const endpoint =
    `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}` +
    `/actions/workflows/${workflowFile}/dispatches`;

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'xixun-parser-worker',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`GitHub dispatch failed: ${response.status} ${errorText}`);
  }
}

function validateEnvironment(env) {
  const requiredKeys = [
    'TELEGRAM_BOT_TOKEN',
    'TELEGRAM_SECRET_TOKEN',
    'GITHUB_TOKEN',
  ];

  const missingKeys = requiredKeys.filter((key) => !env[key]);
  if (missingKeys.length > 0) {
    throw new Error(`Missing required env keys: ${missingKeys.join(', ')}`);
  }
}

async function handleWebhook(request, env) {
  validateEnvironment(env);

  const requestSecret = request.headers.get('X-Telegram-Bot-Api-Secret-Token');
  if (requestSecret !== env.TELEGRAM_SECRET_TOKEN) {
    return jsonResponse({ ok: false, error: 'unauthorized' }, 401);
  }

  let update;
  try {
    update = await request.json();
  } catch {
    return jsonResponse({ ok: false, error: 'invalid_json' }, 400);
  }

  const context = extractTelegramContext(update);
  if (!context?.chatId) {
    return jsonResponse({ ok: true, ignored: 'unsupported_update' });
  }

  const url = extractWeChatUrl(context.text);
  if (!url) {
    if (context.text?.trim()) {
      await sendTelegramMessage(env, {
        chatId: context.chatId,
        replyToMessageId: context.messageId,
        text: '请直接发送一个微信公众号文章链接，我会为你触发解析同步。',
      });
    }

    return jsonResponse({ ok: true, ignored: 'unsupported_message' });
  }

  const ref = env.GITHUB_REF || 'main';
  const payload = buildDispatchPayload({
    ref,
    url,
    chatId: context.chatId,
  });

  try {
    await dispatchGitHubWorkflow(env, payload);
    await sendTelegramMessage(env, {
      chatId: context.chatId,
      replyToMessageId: context.messageId,
      text: `⌛ 已接收链接，正在解析同步中：\n${url}`,
    });
  } catch (error) {
    console.error(error);
    await sendTelegramMessage(env, {
      chatId: context.chatId,
      replyToMessageId: context.messageId,
      text: `❌ 触发解析失败，请检查 Worker 或 GitHub 配置：\n${url}`,
    });
    return jsonResponse({ ok: false, error: 'dispatch_failed' }, 500);
  }

  return jsonResponse({ ok: true, accepted: true, url });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === 'GET' && url.pathname === '/health') {
      return jsonResponse({ ok: true, service: 'xixun-parser-worker' });
    }

    if (request.method !== 'POST') {
      return jsonResponse({ ok: false, error: 'method_not_allowed' }, 405);
    }

    return handleWebhook(request, env);
  },
};
