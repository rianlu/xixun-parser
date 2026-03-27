import test from 'node:test';
import assert from 'node:assert/strict';

import worker, {
  buildDispatchPayload,
  extractWeChatUrl,
} from './worker.mjs';

test('extractWeChatUrl only accepts a standalone WeChat link', () => {
  assert.equal(
    extractWeChatUrl('https://mp.weixin.qq.com/s/example'),
    'https://mp.weixin.qq.com/s/example',
  );
  assert.equal(extractWeChatUrl(' hello https://mp.weixin.qq.com/s/example'), null);
  assert.equal(extractWeChatUrl('https://example.com/not-wechat'), null);
});

test('buildDispatchPayload maps telegram fields to workflow inputs', () => {
  assert.deepEqual(
    buildDispatchPayload({
      ref: 'main',
      url: 'https://mp.weixin.qq.com/s/example',
      chatId: 123456,
    }),
    {
      ref: 'main',
      inputs: {
        url: 'https://mp.weixin.qq.com/s/example',
        chat_id: '123456',
      },
    },
  );
});

test('webhook handler does not require owner/repo env vars anymore', async () => {
  const request = new Request('https://example.com/', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'X-Telegram-Bot-Api-Secret-Token': 'wrong-secret',
    },
    body: JSON.stringify({ message: { text: 'hello', chat: { id: 1 } } }),
  });

  const response = await worker.fetch(request, {
    TELEGRAM_BOT_TOKEN: 'token',
    TELEGRAM_SECRET_TOKEN: 'expected-secret',
    GITHUB_TOKEN: 'github-token',
  });

  assert.equal(response.status, 401);
  assert.deepEqual(await response.json(), { ok: false, error: 'unauthorized' });
});
