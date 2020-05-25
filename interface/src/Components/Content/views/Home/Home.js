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
