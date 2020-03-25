import React from 'react';
import logo from './logo.svg';
import './App.css';
import { NavLink, Switch, Route } from 'react-router-dom';
import Navigation from './Components/Navigation/';
import Content from './Components/Content/'

class TopNavigation extends React.Component {
  render(){
    return "navi"
  }
}

class TestProp extends React.Component {
  render() {
    return (<h1>test prop: {this.props.name}</h1>)
  }
}


class HeaderCSS extends React.Component {
  render() {
    return (<link rel="stylesheet"
          href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css"
          integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous"/>)
  }
}

const GlobalCSS = <HeaderCSS />

// App component
const App = () => (
  <div className="App">
    <header className="App-header">
      {GlobalCSS}
      <Navigation />
      <Content />
      <p>test paragraph</p>
      <a
        className="App-link"
        target="_blank"
        rel="noopener noreferrer">
        test
      </a>
    </header>
    <body>

    </body>
  </div>
);

export default App;
