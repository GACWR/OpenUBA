import React from 'react';
import { Switch, Route, IndexRoute } from 'react-router-dom';
import Home from './views/Home/';
import Settings from './views/Settings/';

/*
@name
@description
This is because a Route will match for any URL that contains its path by default
*/
const Content = () => (
  <Switch>
    <Route exact path='/home' component={Home}></Route>
    <Route exact path='/settings' component={Settings}></Route>
  </Switch>
);

export default Content;
