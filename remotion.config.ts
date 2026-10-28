import {Config} from '@remotion/cli/config';

Config.setEntryPoint('./remotion/src/index.ts');
Config.setPublicDir('./remotion/public');

// remotion.media (Remotion's browser download) is blocked here; use the preinstalled headless shell.
const fs = require('node:fs');
const localShell = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
if (fs.existsSync(localShell)) Config.setBrowserExecutable(localShell);
