/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : scheduler.js

PATH    : core\scheduler.js

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
*/

const cron = require('node-cron');
const { exec } = require('child_process');

// Har 1 ghante mein system ki safai (Temporary files delete karna)
cron.schedule('0 * * * *', () => {
  console.log('[SCHEDULER] Running System Maintenance...');
  exec('del /q/f/s %TEMP%\\*', (err) => {
    if (err) console.log('Bhai, cleaning mein error aaya.');
    else console.log('System Cleaned Successfully!');
  });
});

// Subah 9 baje aapko "Good Morning" bolne ke liye Python ko trigger karna
cron.schedule('0 9 * * *', () => {
  exec('python core/voice.py "Good Morning Bhai! System is ready for use."');
});