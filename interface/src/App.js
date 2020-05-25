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
import React from 'react';
import logo from './logo.svg';
import './App.css';
import { NavLink, Switch, Route } from 'react-router-dom';
import Navigation from './Components/Navigation/';
import Content from './Components/Content/'
import SystemLog from './Components/Common/SystemLog/'


/*
@name HeaderCSS
@ddescription
*/
class HeaderCSS extends React.Component {
  render() {
    return (
            <link
            rel="stylesheet"
            href="https://maxcdn.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
            integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh"
            crossOrigin="anonymous"
            />
        )
  }
}

/*
@name
@ddescription
*/
const GlobalCSS = <HeaderCSS />


/*
@name
@ddescription
*/
class App extends React.Component{
  render(){
    return (
      <div className="App">
        <header className="App-header">
          <script src="https://ajax.googleapis.com/ajax/libs/jquery/2.0.1/jquery.min.js"></script>
          <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"></script>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.1.0/react.min.js"></script>
          <script src="https://cdnjs.cloudflare.com/ajax/libs/react/15.1.0/react-dom.min.js"></script>

          {GlobalCSS}

          <Navigation />

          {/*system log*/}
          <SystemLog></SystemLog>
          <div className="container dashboardBaseText">
            <div className="row">
              <div className="col-sm">
                <hr/>
              </div>
            </div>
          </div>
          {/*end system log*/}

          <Content />

          <div className="container dashboardBaseText">
            <div className="row">
              <div className="col-sm">
                <hr/>
                <a
                  className="App-link lightGrayText"
                  target="_blank"
                  rel="noopener noreferrer">
                  Footer
                </a>
              </div>
            </div>
          </div>
        </header>
      </div>
    )
  }
}


export default App;
