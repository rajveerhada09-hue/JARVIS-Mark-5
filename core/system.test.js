/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : system.test.js

PATH    : core\system.test.js

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
*/

const { execSync } = require('child_process');

test('Node Engine should be responsive', () => {
  const output = execSync('node core/automation.js test_ping').toString();
  expect(output).toBeDefined();
});