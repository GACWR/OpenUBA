import React from 'react';
import { NavLink } from 'react-router-dom';


const NavbarBrand = () => (
  <a class="navbar-brand" href="#">OpenUBA</a>
);

const Navbar = () => (
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <NavbarBrand/>
  <button class="navbar-toggler" type="button"
      data-toggle="collapse"
      data-target="#navbarNavAltMarkup"
      aria-controls="navbarNavAltMarkup"
      aria-expanded="false"
      aria-label="Toggle navigation">
    <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse" id="navbarNavAltMarkup">
    <div class="navbar-nav">

      <a class="nav-item nav-link active" href="#">
        <NavLink to='/home'>
          Home <span class="sr-only">(current)</span>
        </NavLink>
      </a>
      <a class="nav-item nav-link">
        <NavLink to='/data'>
          Data
        </NavLink>
      </a>
      <a class="nav-item nav-link">
        <NavLink to='/models'>
          Models
        </NavLink>
      </a>
      <a class="nav-item nav-link">
        <NavLink to='/anomalies'>
          Anomalies
        </NavLink>
      </a>
      <a class="nav-item nav-link">
        <NavLink to='/cases'>
          Cases
        </NavLink>
      </a>
      <a class="nav-item nav-link">
        <NavLink to='/settings'>
          Settings
        </NavLink>
      </a>
    </div>
  </div>
</nav>
);

//
// const element = <TestProp name="dev" />;


/*
@name
@description global navigator
*/
const Navigation = () => (
  <Navbar/>
);



// export the navigation component
export default Navigation;
