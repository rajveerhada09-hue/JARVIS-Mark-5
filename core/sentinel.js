/*
============================================================
PROJECT : JARVIS MARK 5

FILE    : sentinel.js

PATH    : core\sentinel.js

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
*/

const notifier = require('node-notifier');
const osu = require('node-os-utils');
const cpu = osu.cpu;

// 1. Live CPU Alert (Monitoring)
setInterval(() => {
    cpu.usage().then(info => {
        if (info > 80) { // Agar CPU 80% se upar gaya
            notifier.notify({
                title: 'JARVIS CRITICAL ALERT',
                message: `Sir, CPU usage is at ${info}%. Closing background apps...`,
                sound: true, // Windows default sound
                wait: true
            });
        }
    });
}, 5000); // Har 5 second mein check karega

// 2. Hardware Connectivity (SerialPort Placeholder)
const { SerialPort } = require('serialport');
console.log("Searching for connected hardware (Arduino/Robots)...");

// 3. Simple Notification for Start
notifier.notify('JARVIS Sentinel Mode Active, Sir!');