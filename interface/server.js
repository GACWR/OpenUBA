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
const express = require('express');
const app = express();
const path = require('path');
const router = express.Router();



//app.use(express.static('html'))
app.use(express.static(path.join(__dirname, 'build')));


router.get('/', function (req, res) {
  console.log(__dirname)
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
  //__dirname : It will resolve to your project folder.
});

router.get('/dev', function (req, res) {
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/index.html'));
});

router.get('/data',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/data.html'));
});

router.get('/modeling',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/modeling.html'));
});

router.get('/anomalies',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/anomalies.html'));
});

router.get('/cases',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/cases.html'));
});

router.get('/settings',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/settings.html'));
});

//add the router
app.use('/', router);
app.listen(process.env.port || 3001);

console.log('Running UI server at 3001');
