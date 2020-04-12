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
import Badge from 'react-bootstrap/Badge';
import Spinner from 'react-bootstrap/Spinner';
import ListGroup from 'react-bootstrap/ListGroup';


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
      // TODO: call API for monitored users count

      //let complete_endpoint = this.API_SERVER+"/display/get_all_entities"
      //const res = await fetch(complete_endpoint)
      //const json_response = await res.json()

      //this.setState({
      //  monitored_users_count: this.state.system_log_status + 1
      //});

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
        <div className="container dashboardBaseText">


          <div className="row">
            <div className="col-sm">
              <div className="card">
                <div className="card-body">
                  <h2>
                    <b>Summary</b>
                    <Spinner animation="border" role="status">
                      <span className="sr-only">Loading...</span>
                    </Spinner>
                  </h2>
                  <hr/>
                  {/*<hr/>*/}
                  <div className="row">
                    {/* Load monitored user */}
                    <div className="col-sm">
                      <h5>
                        Monitored Users: <MonitoredUsersWidget/>
                      </h5>
                    </div>
                    {/*load highest risk*/}
                    <div className="col-sm">
                      <h5>
                        High Risk:
                        <span className="badge badge-info">100</span>
                      </h5>
                    </div>
                    {/*load users discovere*/}
                    <div className="col-sm">
                      <h5>
                        Users Discovered from events:
                        <span className="badge badge-info">100</span>
                      </h5>
                    </div>
                    {/*load users imported*/}
                    <div className="col-sm">
                      <h5>
                        Users imported from directory:
                        <span className="badge badge-info">100</span>
                      </h5>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        </div>
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
@name HomeSecondRow
@ddescription component to hold the second row on home
*/
const HomeSecondRow = () => (
  <div className="row">

    {/*********************Monitored users*/}
    <div className="col-sm-4">
        <p className="lightGrayText">Monitored Users</p>
        <ListGroup>
          <ListGroup.Item>
          User 1
          <p>Score: <span className="badge badge-info badge-pill">14</span></p>
          </ListGroup.Item>
          <ListGroup.Item>
          User 2
          <p>Score: <span className="badge badge-info badge-pill">14</span></p>
          </ListGroup.Item>
          <ListGroup.Item>
          User 3
          <p>Score: <span className="badge badge-info badge-pill">14</span></p>
          </ListGroup.Item>
        </ListGroup>
    </div>

    {/*********************recent offenses*/}
    <div className="col-sm-8">
      <div className="card">
        <div className="card-body">
          <div className="row">
            <div className="col-sm-12">
                  <p>Recent Anomalies</p>
                  <ListGroup>
                    <ListGroup.Item>
                      <p>Offense 1</p>
                      <p>Score: <span className="badge badge-warning badge-pill">14</span></p>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <p>Offense 1</p>
                      <p>Score: <span className="badge badge-warning badge-pill">14</span></p>
                    </ListGroup.Item>
                    <ListGroup.Item>
                      <p>Offense 1</p>
                      <p>Score: <span className="badge badge-warning badge-pill">14</span></p>
                    </ListGroup.Item>
                  </ListGroup>
            </div>



            {/*********************recent offenses graph*/}
            <div className="col-sm-7">
              <div id="d3_main"></div>
            </div>

          </div>
        </div>
      </div>
    </div>
  </div>
)

/*
@name Home
@ddescription component to render the home partial
*/
const Home = () => (
  <div className="home">

    {/********************* SUMMARY*/}
    <HomeSummary></HomeSummary>
    {/*********************END SUMMARY*/}

    {/*********************MONITORED USERS*/}
    <div className="container dashboardBaseText">
      <Separator/>
      {/*********************Second Row*/}
      <HomeSecondRow />
      {/*********************END Second Row*/}
    </div>
    {/*********************END MONITORED USERS*/}

    {/*********************UNDER CONTENT*/}
    <div className="container dashboardBaseText">

      <div className="row">
        <div className="col-sm">
          <hr/>
        </div>
      </div>

      <div className="row">

        <div className="col-sm-6">
          <div className="list-group">
            <a href="#" className="list-group-item list-group-item-action flex-column align-items-start">
              <div className="d-flex w-100 justify-content-between">
                <h5 className="mb-1">List group item heading</h5>
                <small>3 days ago</small>
              </div>
              <p className="mb-1">Donec id elit non mi porta gravida at eget metus. Maecenas sed diam eget risus varius blandit.</p>
              <small>Donec id elit non mi porta.</small>
            </a>
            <a href="#" className="list-group-item list-group-item-action flex-column align-items-start">
              <div className="d-flex w-100 justify-content-between">
                <h5 className="mb-1">List group item heading</h5>
                <small className="text-muted">3 days ago</small>
              </div>
              <p className="mb-1">Donec id elit non mi porta gravida at eget metus. Maecenas sed diam eget risus varius blandit.</p>
              <small className="text-muted">Donec id elit non mi porta.</small>
            </a>
          </div>

        </div>

        <div className="col-sm-6">
          <div className="card">
            <div className="card-body">
              This is some text within a card body.
            </div>
          </div>
        </div>

      </div>
    </div>


    {/*END UNDER CONTENT*/}


  </div>
);

export default Home;
