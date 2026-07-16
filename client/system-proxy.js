const { execFile } = require('child_process');

const INTERNET_SETTINGS = 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings';

function runReg(args) {
  return new Promise((resolve, reject) => {
    execFile('reg.exe', args, { windowsHide: true }, (error, stdout, stderr) => {
      if (error) reject(new Error(stderr.trim() || error.message));
      else resolve(stdout);
    });
  });
}

async function getSystemProxy() {
  try {
    const output = await runReg(['query', INTERNET_SETTINGS, '/v', 'ProxyEnable']);
    return /ProxyEnable\s+REG_DWORD\s+0x1/i.test(output);
  } catch (_) {
    return false;
  }
}

async function setSystemProxy(enabled, server = '127.0.0.1:7890') {
  await runReg(['add', INTERNET_SETTINGS, '/v', 'ProxyEnable', '/t', 'REG_DWORD', '/d', enabled ? '1' : '0', '/f']);
  if (enabled) {
    await runReg(['add', INTERNET_SETTINGS, '/v', 'ProxyServer', '/t', 'REG_SZ', '/d', server, '/f']);
  }
  return enabled;
}

module.exports = { getSystemProxy, setSystemProxy };
