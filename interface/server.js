/*
Copyright 2019-Present The OpenUBA Platform Authors
This file is part of the OpenUBA Platform library.
The OpenUBA Platform is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
The OpenUBA Platform is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License
along with the OpenUBA Platform. If not, see <http://www.gnu.org/licenses/>.
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

/////////////////
ipcMain.on('global_call_message', (event, arg) => {
  console.log("")
})

///// END ELECTRON

//add the router
//app.use('/', router);
//app.listen(process.env.port || 3001);

console.log('Running UI server at 3001');
