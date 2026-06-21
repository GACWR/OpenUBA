/*
Copyright (c) 2019–present GACWR
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
const { app, BrowserWindow } = require('electron')
const { ipcMain } = require('electron')
const path = require('path');
const url = require('url');
var fs = require('fs');

let win

//const express = require('express');
// const app = express();
//const path = require('path');
//const router = express.Router();


// ELECTRON

const DEFAULT_GLOBAL_STATE = {
  main: ''
}

let GLOBAL_STATE = {}

function createWindow () {
  win = new BrowserWindow({
              width: 1400,
              height: 700,
              resizable: false,
              webPreferences: {
                  webSecurity: false,
                  nodeIntegration: false,
                  preload: __dirname + '/preload.js'
                }
            })

  const startUrl = process.env.ELECTRON_START_URL || url.format({
    pathname: path.join(__dirname, 'build/index.html'),
    protocol: 'file:',
    slashes: true,
  });

  win.loadURL(startUrl);

  // Open the DevTools.
  win.webContents.openDevTools()
  win.on('closed', () => {
    win = null
  })
}

app.on('ready', (function(){
  // win.webContents.on('did-finish-load', function() {
  //   win.webContents.executeJavaScript("alert('Hello There!');");
  // });
  console.log(win)
  createWindow()
}))


app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (win === null) {
    createWindow()
  }
})

ipcMain.on('global_call_message', (event, arg) => {
  console.log("global_call_message")
  event.sender.send('global_call_reply', { "Result":  result });
})

ipcMain.on('model_library_search_call_message', (event, arg) => {
  console.log("model_library_search_call_message")
  console.log(arg)
  event.sender.send('model_library_search_call_reply', { "Result":  "RESULT" });
})

ipcMain.on('local_search_call_message', (event, arg) => {
  console.log("local_search_call_message")
  console.log(arg)
  event.sender.send('local_search_call_reply', { "Result":  "RESULT" });
})

console.log('Running UI server at 3001');
