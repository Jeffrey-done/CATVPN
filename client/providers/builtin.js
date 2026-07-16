const fs = require('fs/promises');
const path = require('path');
const { registerProvider } = require('./index');

async function loadRaw(url) {
  const response = await fetch(url, { headers: { 'User-Agent': 'CATVPN-Client/0.1' } });
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.text();
}

async function loadFile(source) {
  const filePath = path.resolve(__dirname, '..', source.path);
  return fs.readFile(filePath, 'utf8');
}

registerProvider('github-raw', { load: (source) => loadRaw(source.url) });
registerProvider('file', { load: loadFile });
