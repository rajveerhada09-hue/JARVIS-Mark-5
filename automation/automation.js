/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : automation.js

PATH    : core\automation.js

PURPOSE :
Node.js automation bridge for fast desktop control.

LAST UPDATED :
2026-06-28

============================================================
*/

const { exec } = require("child_process");

const command = process.argv[2];
const value = process.argv[3];

async function executeCommand() {
    try {
        console.log(`[NODE] Received → Command: "${command}" | Value: "${value || 'None'}"`);

        if (!command) {
            console.log("[NODE] No command provided");
            return;
        }

        switch (command.toLowerCase()) {
            case "open":
            case "open_app":
                if (!value) {
                    console.log("[NODE] No value provided");
                    break;
                }

                console.log(`[NODE] Opening: ${value}`);

                // Windows reliable method
                const url = value.startsWith("http") ? value : `https://${value}`;
                const cmd = `start "" "${url}"`;

                exec(cmd, (error) => {
                    if (error) {
                        console.error("[NODE] Exec error:", error.message);
                    } else {
                        console.log(`[NODE] Successfully opened: ${url}`);
                    }
                });
                break;

            default:
                console.log(`[NODE] Unknown command: ${command}`);
        }
    } catch (error) {
        console.error("[NODE] Error:", error.message);
    }
}

executeCommand();