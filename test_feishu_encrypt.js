const crypto = require('crypto');

function encrypt(data, key) {
    const keyHash = crypto.createHash('sha256').update(key).digest();
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-cbc', keyHash, iv);
    let encrypted = cipher.update(data);
    encrypted = Buffer.concat([encrypted, cipher.final()]);
    return Buffer.concat([iv, encrypted]).toString('base64');
}

const key = "8STKgJfPBjie3zOm46I2KhBF3edf0vZk";
const payload = JSON.stringify({
    type: "url_verification",
    challenge: "test_challenge_123456789"
});

const encryptedData = encrypt(payload, key);
console.log(JSON.stringify({ encrypt: encryptedData }));
