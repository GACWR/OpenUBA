import React from 'react';
import logo from './logo.svg';
import './App.css';
import { NavLink, Switch, Route } from 'react-router-dom';
import Navigation from './Components/Navigation/';
import Content from './Components/Content/'
import {SystemLogContext} from './Contexts/SystemLogContext'
import {API} from './API.js'

/*
@name
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
class SystemLog extends React.Component{
  render(){

    console.log("rendering system log")
    return (
      <SystemLogContext.Consumer>
        {({system_log_status}) => (
          <div className="container systemLogContainer">
            <div className="row">
              <div className="col-sm" id="system_log">
                <div className="card">
                  <div className="card-body">
                  <p className="systemlogp">
                    {system_log_status}
                  </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </SystemLogContext.Consumer>
    )
  }
}

//SystemLog.contextType = SystemLogContext;
//const contextType = SystemLogContext;



/*
@name
@ddescription
*/
class App extends React.Component{
  constructor(props) {
    super(props);
    this.API_SERVER = "http://localhost:5000"
    this.state = {
      system_log_status: "default status"
    }
  }

  componentDidMount() {
    let complete_endpoint = this.API_SERVER+"/display/get_all_entities"
    fetch(complete_endpoint)
      .then(res => res.json())
      .then(
        (result) => {
          this.setState({
            system_log_status: "default status 2"
          });
        },
        // Note: it's important to handle errors here
        // instead of a catch() block so that we don't swallow
        // exceptions from actual bugs in components.
        (error) => {
          this.setState({
            system_log_status: "default status error"
          });
        }
      )
  }

  render(){
    return (
      <div className="App">
        <header className="App-header">
          {GlobalCSS}
          <Navigation />

          {/*system log*/}
          <SystemLogContext.Provider value={this.state}>
            <SystemLog></SystemLog>
          </SystemLogContext.Provider>
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
