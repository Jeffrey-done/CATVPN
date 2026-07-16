const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

class MihomoManager {
  constructor(settings) {
    this.settings = settings;
    this.process = null;
  }

  get executable() {
    if (process.resourcesPath && !process.defaultApp) {
      return path.join(process.resourcesPath, 'mihomo', 'mihomo.exe');
    }
    return path.resolve(__dirname, '..', settingsPath(this.settings.corePath || 'resources/mihomo/mihomo.exe'));
  }

  get runtimeDir() {
    if (process.resourcesPath && !process.defaultApp) {
      return path.join(process.env.APPDATA || path.dirname(process.resourcesPath), 'CATVPN');
    }
    return path.resolve(__dirname, '..', 'runtime');
  }

  get configPath() {
    return path.join(this.runtimeDir, 'config.yaml');
  }

  available() {
    return fs.existsSync(this.executable);
  }

  start() {
    if (!this.available() || this.process) return false;
    this.process = spawn(this.executable, ['-d', this.runtimeDir, '-f', this.configPath], {
      windowsHide: true,
      stdio: 'ignore',
    });
    this.process.once('exit', () => { this.process = null; });
    return true;
  }

  stop() {
    if (this.process) this.process.kill();
    this.process = null;
  }
}

function settingsPath(value) {
  return value.replace(/^[/\\]+/, '');
}

module.exports = { MihomoManager };
