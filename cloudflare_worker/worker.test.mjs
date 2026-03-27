import test from 'node:test';
import assert from 'node:assert/strict';

import {
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
