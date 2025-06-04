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
import {Badge, Spinner, Row, Col, Container, Card} from 'react-bootstrap';



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
          <Badge variant="info">{monitored_users_count}</Badge>
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
      monitored_users_count: 0,
      high_risk_count: 0,
      users_discovered: 0,
      users_imported: 0,
      loading: true,
      error: null
    }
  }

  async componentDidMount() {
    try {
      console.log('Fetching dashboard data...');
      const response = await fetch('http://localhost:5001/api/dashboard/summary');
      console.log('Response status:', response.status);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Dashboard data received:', data);
      
      this.setState({
        monitored_users_count: data.monitored_users,
        high_risk_count: data.high_risk,
        users_discovered: data.users_discovered,
        users_imported: data.users_imported,
        loading: false
      });
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      this.setState({
        error: `Failed to load dashboard data: ${error.message}`,
        loading: false
      });
    }
  }

  render(){
    const { loading, error } = this.state;

    if (loading) {
      return (
        <Container className="text-center mt-5">
          <Spinner animation="border" />
          <div>Loading dashboard data...</div>
        </Container>
      );
    }

    if (error) {
      return (
        <Container className="text-center mt-5">
          <div className="text-danger">{error}</div>
        </Container>
      );
    }

    return (
      <HomeSummaryContext.Provider value={this.state}>
        <Container className="dashboardBaseText">
          <Row>
            <Col lg={{span: 12, offset: 0}}>
              <Card>
                <Card.Header>
                  <h4 className="address_status float-left">
                    Summary
                  </h4>
                </Card.Header>
                <Card.Body>
                  <div className="dashboard-content">
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
                            <Badge variant="danger" className="ml-2">{this.state.high_risk_count}</Badge>
                          </h5>
                        </Col>
                        <Col lg={{span: 3, offset: 0}}>
                          <h5>
                            Users Discovered:
                            <Badge variant="info" className="ml-2">{this.state.users_discovered}</Badge>
                          </h5>
                        </Col>
                        <Col lg={{span: 3, offset: 0}}>
                          <h5>
                            Users Imported:
                            <Badge variant="info" className="ml-2">{this.state.users_imported}</Badge>
                          </h5>
                        </Col>
                      </Row>
                    </Container>
                  </div>
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
    <HomeSummary/>
  </div>
);

export default Home;
