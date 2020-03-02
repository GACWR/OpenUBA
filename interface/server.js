const express = require('express');
const app = express();
const path = require('path');
const router = express.Router();

app.use(express.static('html'))

router.get('/',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/index.html'));
  //__dirname : It will resolve to your project folder.
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

//add the router
app.use('/', router);
app.listen(process.env.port || 3000);

console.log('Running UI server at 3000');
