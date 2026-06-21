/*
Copyright (c) 2019–present GACWR
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
import React from 'react';
import {HomeSummaryContext} from './Contexts/HomeSummaryContext'
import {Badge, Spinner, ListGroup, Row, Col, Container, Card} from 'react-bootstrap';



/*
@name MonitoredUsers
@ddescription component for displaying the monitored users widget
*/
class MonitoredUsersWidget extends React.Component {
  render(){
    //          {/*<span className="badge badge-info">{monitored_users_count}</span>*/}

    return (
      <HomeSummaryContext.Consumer>
        {({monitored_users_count}) => (
          <span>
            <p>
              <Badge variant="info">{monitored_users_count}</Badge>
            </p>
          </span>
        )}
      </HomeSummaryContext.Consumer>
    )
  }
}

/*
@name HomeSummary
@ddescription component holding the summary for the home page
*/
class HomeSummary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      monitored_users_count: 1
    }
  }

  async loadMonitoredUsers() {
    try{


    }catch(e){

    }
  }

  async componentDidMount() {
    // TODO: perhaps set interval and call this.loadMonitoredUsers, and others?
  }

  render(){
    //TODO: create home summary context provider/consumer
    console.log("Rendering HomeSummary")
    return (
      <HomeSummaryContext.Provider value={this.state}>
        <Container className="dashboardBaseText">
          <Row>
            <Col lg={{span: 12, offset: 0}}>
              <Card lg={{span: 12, offset: 1}}>
                <Card.Header>
                  <h4 className="address_status float-left">
                    Summary
                  </h4>
                </Card.Header>
                <Card.Body>
                  <Card.Text>
                    <Container>
                      <Row>
                        <Col lg={{span: 3, offset: 0}}>
                          <h5>
                            Monitored Users: <MonitoredUsersWidget/>
                          </h5>
                        </Col>
                        <Col lg={{span: 3, offset: 0}}>
                          <h5>
                            High Risk:
                            <span className="badge badge-info">100</span>
                          </h5>
                        </Col>
                        <Col lg={{span: 3, offset: 0}}>
                          <h5>
                            Users Discovered from events:
                            <span className="badge badge-info">100</span>
                          </h5>
                        </Col>
                        <Col lg={{span: 3, offset: 0}}>
                          <h5>
                            Users imported from directory:
                            <span className="badge badge-info">100</span>
                          </h5>
                        </Col>
                      </Row>
                    </Container>
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Container>
      </HomeSummaryContext.Provider>
    )
  }
}


/*
@name Separator
@ddescription component for reusabl horizonal separator
*/
const Separator = () => (
  <div className="row">
    <div className="col-sm">
      <hr/>
    </div>
  </div>
)

/*
@name Home
@ddescription component to render the home partial
*/
const Home = () => (
  <div className="home">

    <HomeSummary></HomeSummary>



  </div>
);

export default Home;
