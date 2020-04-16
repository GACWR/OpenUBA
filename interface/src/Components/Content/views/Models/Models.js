import React from 'react';
import Tabs from 'react-bootstrap/Tabs';
import Tab from 'react-bootstrap/Tab';
import ListGroup from 'react-bootstrap/ListGroup';
import Spinner from 'react-bootstrap/Spinner';



const ModelSearchBar = () => (
  <div className="container">
    <div className="row">
      <div className="col-4">
      <div className="md-form active-pink active-pink-2 mb-3 mt-0">
        <br />
        <input className="form-control" type="text" placeholder="Search Model Repository" aria-label="Search"/>
      </div>
      </div>
    </div>
  </div>
)

const ModelTabs = () => (
  <div className="container">
    <div className="row">
      <div className="col-sm" id="system_log">
        <div className="card">
          <div className="card-body">
            <Tabs defaultActiveKey="manage" id="uncontrolled-tab-example">
              <Tab eventKey="manage" title="manage">
                <ModelSearchBar />
                <div className="container">
                  <div className="row">

                    <div className="col-sm" id="system_log">
                      <div className="card">
                        <div className="card-body">
                          <p>Results</p>
                          <Spinner animation="border" role="status">
                            <span className="sr-only">Loading...</span>
                          </Spinner>
                        </div>
                      </div>
                    </div>

                  </div>
                </div>
              </Tab>

              <Tab eventKey="installed" title="installed">
                <p>Installed Models</p>
                <ListGroup>
                  <ListGroup.Item>Model #1</ListGroup.Item>
                  <ListGroup.Item>Model #2</ListGroup.Item>
                  <ListGroup.Item>Model #3</ListGroup.Item>
                </ListGroup>
              </Tab>

              <Tab eventKey="Jobs" title="Jobs">
                <p>Model Jobs Scheduler</p>
                <ListGroup>
                  <ListGroup.Item>Model #1</ListGroup.Item>
                  <ListGroup.Item>Model #2</ListGroup.Item>
                  <ListGroup.Item>Model #3</ListGroup.Item>
                </ListGroup>
              </Tab>


            </Tabs>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const Models = () => (
  <div className="models">
    <h1>Models</h1>

    {/* SEARCH BAR */}

    <br />
    <ModelTabs />

  </div>
);

export default Models;
