const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

function prepareRuntimeConfig(text, configPath) {
  const config = yaml.load(text) || {};
  config['external-controller'] ||= '127.0.0.1:9090';
  fs.mkdirSync(path.dirname(configPath), { recursive: true });
  fs.writeFileSync(configPath, yaml.dump(config, { noRefs: true }), 'utf8');
  return config;
}

module.exports = { prepareRuntimeConfig };
