import React from 'react';
import { Switch, Route, IndexRoute } from 'react-router-dom';
import Home from './views/Home/';
import Data from './views/Data/';
import Models from './views/Models/';
import Anomalies from './views/Anomalies/';
import Cases from './views/Cases/';
import Settings from './views/Settings/';


/*
@name Content
@description content component containing the main navigation router
This is because a Route will match for any URL that contains its path by default
*/
const Content = () => (
  <Switch>
    <Route exact path='/home' component={Home}></Route>
    <Route exact path='/data' component={Data}></Route>
    <Route exact path='/models' component={Models}></Route>
    <Route exact path='/anomalies' component={Anomalies}></Route>
    <Route exact path='/cases' component={Cases}></Route>
    <Route exact path='/settings' component={Settings}></Route>
  </Switch>
);

export default Content;
