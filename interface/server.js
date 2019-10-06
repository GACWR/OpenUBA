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
  //__dirname : It will resolve to your project folder.
});

router.get('/modeling',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/modeling.html'));
  //__dirname : It will resolve to your project folder.
});

router.get('/anomalies',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/anomalies.html'));
  //__dirname : It will resolve to your project folder.
});

router.get('/cases',function(req,res){
  console.log(__dirname)
  res.sendFile(path.join(__dirname+'/html/cases.html'));
  //__dirname : It will resolve to your project folder.
});

//add the router
app.use('/', router);
app.listen(process.env.port || 3000);

console.log('Running at Port 3000');
