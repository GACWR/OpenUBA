import React from 'react';


/*
@name Home
@ddescription component to render the home partial
*/
const Home = () => (
  <div className="home">

    {/********************* SUMMARY*/}
    <div className="container dashboardBaseText">
      <div className="row">
        <div className="col-sm">
          {/*<hr/>*/}
        </div>
      </div>
      <div className="row">
        <div className="col-sm">
          <div className="card">
            <div className="card-body">
              <h2><b>Summary</b></h2>
              {/*<hr/>*/}
              <div className="row">
                <div className="col-sm">
                  <h5>
                    Monitored Users:
                    <span className="badge badge-info">100</span>
                  </h5>
                </div>
                <div className="col-sm">
                  <h5>
                    High Risk:
                    <span className="badge badge-info">100</span>
                  </h5>
                </div>
                <div className="col-sm">
                  <h5>
                    Users Discovered from events:
                    <span className="badge badge-info">100</span>
                  </h5>
                </div>
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


    {/*********************END SUMMARY*/}

    {/*********************MONITORED USERS*/}
    <div className="container dashboardBaseText">
      <div className="row">
        <div className="col-sm">
          <hr/>
        </div>
      </div>


      {/*********************Second Row*/}
      <div className="row">
      {/*********************Monitored users*/}
        <div className="col-sm-4">
            <p className="lightGrayText">Monitored Users</p>
            <ul className="list-group">
                <li className="list-group-item d-flex justify-content-between align-items-center">
                  User 1
                  <p>Score: <span className="badge badge-danger badge-pill">14</span></p>
                </li>
                <li className="list-group-item d-flex justify-content-between align-items-center">
                  User 2
                  <p>Score: <span className="badge badge-warning badge-pill">14</span></p>
                </li>
                <li className="list-group-item d-flex justify-content-between align-items-center">
                  User 3
                  <p>Score: <span className="badge badge-info badge-pill">14</span></p>
                </li>
            </ul>
        </div>

        {/*********************recent offenses*/}
        <div className="col-sm-8">
          <div className="card">
            <div className="card-body">
              <div className="row">
                <div className="col-sm-5">
                      <p>Recent Offenses</p>
                      <ul className="list-group">
                          <li className="list-group-item d-flex justify-content-between align-items-center">
                            <p>Offense 1</p>
                            <p>Score: <span className="badge badge-warning badge-pill">14</span></p>
                          </li>
                          <li className="list-group-item d-flex justify-content-between align-items-center">
                            <p>Offense 2</p>
                            <p>Score: <span className="badge badge-warning badge-pill">14</span></p>
                          </li>
                          <li className="list-group-item d-flex justify-content-between align-items-center">
                            <p>Offense 3</p>
                            <p>Score: <span className="badge badge-info badge-pill">14</span></p>
                          </li>
                      </ul>
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
