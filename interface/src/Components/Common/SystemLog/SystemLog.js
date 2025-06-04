import React from 'react';
import {SystemLogContext} from './Contexts/SystemLogContext'
import {Container, Row, Col, Card} from 'react-bootstrap'

/*
@name SystemLogStatus
@ddescription consumer for system log status
*/

const SystemLogStatus = () => {
  return (
    <SystemLogContext.Consumer>
      {({system_log_status}) => (
        <div className="systemlogp">
          System Status From Server: {system_log_status}
        </div>
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
    this.API_SERVER = "http://localhost:5001"
    this.state = {
      system_log_status: 1
    }
  }

  async loadSystemStatus() {
    try {
      const res = await fetch(`${this.API_SERVER}/display/get_all_entities`)
      await res.json()
      this.setState(prevState => ({
        system_log_status: prevState.system_log_status + 1
      }));
    } catch(e) {
      console.log(e);
      this.setState(prevState => ({
        system_log_status: prevState.system_log_status + 1
      }));
    }
  }

  async componentDidMount() {
    try {
      setInterval(async () => {
        // Uncomment to enable status polling
        // await this.loadSystemStatus()
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
              <Card>
                <Card.Body>
                  <div className="system-log-content">
                    <Container>
                      <Row>
                        <Col lg={{span: 12, offset: 0}}>
                          <SystemLogStatus/>
                        </Col>
                      </Row>
                    </Container>
                  </div>
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
