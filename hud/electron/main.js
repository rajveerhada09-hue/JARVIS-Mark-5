/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : main.js

PATH    : hud\electron\main.js

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
*/

const { BrowserWindow, app } = require("electron");
const path = require("path");

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

    win.loadFile(
        path.join(
            __dirname,
            "../ui/index.html"
        )
    );
}

app.whenReady().then(() => {

    createWindow();

});