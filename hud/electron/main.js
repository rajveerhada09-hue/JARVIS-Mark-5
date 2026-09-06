/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : main.js

PATH    : hud\electron\main.js

PURPOSE :
Electron main process - launches HUD and WebSocket bridge
============================================================
*/

const { BrowserWindow, app, ipcMain } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let wsServer = null;

function startWebSocketServer() {
    const wsPath = path.join(__dirname, "..", "websocket", "server.js");
    wsServer = spawn("node", [wsPath], {
        cwd: path.join(__dirname, ".."),
        stdio: "inherit"
    });

    wsServer.on("error", (err) => {
        console.error("[HUD] WebSocket server error:", err);
    });

    wsServer.on("close", (code) => {
        console.log("[HUD] WebSocket server exited with code:", code);
    });

    console.log("[HUD] WebSocket bridge started");
}

function createWindow() {
    const win = new BrowserWindow({
        width: 1600,
        height: 900,
        frame: false,
        fullscreen: true,
        transparent: false,
        backgroundColor: "#050b14",
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    // Load built HUD
    win.loadFile(
        path.join(
            __dirname,
            "..",
            "dist",
            "index.html"
        )
    );

    // DevTools in development
    if (process.argv.includes("--dev")) {
        win.webContents.openDevTools();
    }
}

app.whenReady().then(() => {
    startWebSocketServer();
    createWindow();

    app.on("activate", () => {
        if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
});

app.on("window-all-closed", () => {
    if (wsServer) {
        wsServer.kill();
    }
    if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
    if (wsServer) {
        wsServer.kill();
    }
});