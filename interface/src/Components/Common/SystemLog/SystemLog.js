import React from 'react';
import {SystemLogContext} from './Contexts/SystemLogContext'


class SystemLogStatus extends React.Component {
  render(){
    console.log("rendering system log")
    return (
      <SystemLogContext.Consumer>
        {({system_log_status}) => (
          <p className="systemlogp">
            System Status: {system_log_status}
          </p>
        )}
      </SystemLogContext.Consumer>
    )
  }
}

/*
@name
@ddescription
*/
class SystemLog extends React.Component {

  constructor(props) {
    super(props);
    this.API_SERVER = "http://localhost:5000"
    this.state = {
      system_log_status: 1
    }
  }

  async loadSystemStatus() {
    try{
      let complete_endpoint = this.API_SERVER+"/display/get_all_entities"
      const res = await fetch(complete_endpoint)
      const json_response = await res.json()
      this.setState({
        system_log_status: this.state.system_log_status + 1
      });
    }catch(e){
      console.log(e);
      this.setState({
        system_log_status: this.state.system_log_status + 1
      });
    }
  }

  async componentDidMount() {
    /*
    let complete_endpoint = this.API_SERVER+"/display/get_all_entities"
    let complete_endpoint = this.API_SERVER+"/display/get_all_users"
    let complete_endpoint = this.API_SERVER+"/display/get_system_log"
    */
    try {
      setInterval(async () => {
        // async call to load system status
        //this.loadSystemStatus()
      }, 1000);
    } catch(e) {
      console.log(e);
    }
  }

  render(){
    console.log("rendering system log")
    return (
      <SystemLogContext.Provider value={this.state}>
          <div className="container systemLogContainer">
            <div className="row">
              <div className="col-sm" id="system_log">
                <div className="card">
                  <div className="card-body">
                  <SystemLogStatus/>
                  </div>
                </div>
              </div>
            </div>
          </div>
      </SystemLogContext.Provider>
    )
  }
}

export default SystemLog;
