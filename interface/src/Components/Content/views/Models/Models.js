import React from 'react';

const Models = () => (
  <div className="models">
    <h1>Models</h1>

    {/* SEARCH BAR */}
    <div className="container">
      <div className="row">
        <div className="col-sm" id="system_log">
          <div className="card">
            <div className="card-body">
              <div className="md-form active-pink active-pink-2 mb-3 mt-0">
                <input className="form-control" type="text" placeholder="Search" aria-label="Search"/>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <br/>
    {/* Model Results */}
    <div className="container">
      <div className="row">
        <div className="col-sm" id="system_log">
          <div className="card">
            <div className="card-body">
              Results
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
);

export default Models;
