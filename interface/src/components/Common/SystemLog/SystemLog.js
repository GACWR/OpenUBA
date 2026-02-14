import React from 'react';
import {SystemLogContext} from './Contexts/SystemLogContext'
import {Toast, Container, Row, Col, Button, Card} from 'react-bootstrap'


/*
@name SystemLogStatus
@ddescription consumer for system log status
*/


//class SystemLogStatus extends React.Component {
const SystemLogStatus = (props) => {

  const [show, setShow] = React.useState(false);

  return (
    <SystemLogContext.Consumer>
      {({system_log_status}) => (
        <>
          <p className="systemlogp">
            System Status From Server: {system_log_status}
          </p>
        </>
      )}
    </SystemLogContext.Consumer>
  )
}


/*
@name SystemLog
@description component as provider for system log status
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
        <Container className="systemLogContainer">
          <Row>
            <Col lg={{span: 12, offset: 0}} className="system_log">
              <Card lg={{span: 12, offset: 1}}>
                <Card.Body>
                  <Card.Text>
                    <Container>
                      <Row>
                        <Col lg={{span: 12, offset: 0}}>
                          <SystemLogStatus/>
                        </Col>
                      </Row>
                    </Container>
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Container>
      </SystemLogContext.Provider>
    )
  }
}

export default SystemLog;
