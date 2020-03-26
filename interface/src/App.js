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
    return (<link rel="stylesheet"
          href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
          integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossOrigin="anonymous"/>)
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
          {GlobalCSS}
          <Navigation />

          {/*system log*/}
          <SystemLog></SystemLog>
          {/*end system log*/}

          <Content />
          <p>test paragraph</p>
          <a
            className="App-link"
            target="_blank"
            rel="noopener noreferrer">
            test
          </a>
        </header>
      </div>
    )
  }
}

// // App component
// const App = () => (
//
// );

export default App;
