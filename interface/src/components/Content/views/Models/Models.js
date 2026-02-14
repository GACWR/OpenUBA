import React from 'react';
import {Tabs,
        Tab,
        ListGroup,
        Spinner,
        Container,
        Row,
        Col,
        Card,
        InputGroup,
        FormControl,
        Button}  from 'react-bootstrap';

/*
@name ModelContext
@description
*/
export const ModelContext = React.createContext({
  model_library_search_term: "blank model library search term",
  model_local_search_term: "blank model local search term"
});


/*
@name ModelLibrarySearchBar
@description
*/
class ModelLibrarySearchBar extends React.Component{
  render(props){
    return (
      <>
        <Container>
          <Row>
            <Col lg={{span: 8, offset: 0}}>
              <InputGroup className="mb-3">
                <InputGroup.Prepend>
                  <InputGroup.Text  id="basic-addon3">
                    Search Model Library
                  </InputGroup.Text>
                </InputGroup.Prepend>
                <FormControl id="basic-url" aria-describedby="basic-addon3" placeholder="ex: Botnet, Regression" onChange={this.props.handle_ml_search_term_change} />
                <InputGroup.Append>
                  <Button variant="outline-info" onClick={this.props.handle_ml_search_term_submit}>Find</Button>
                </InputGroup.Append>
              </InputGroup>
            </Col>
          </Row>
        </Container>
      </>
    )
  }
}

/*
@name
@description
*/
class ModelLocalSearchBar extends React.Component{
  render(props){
    return (
      <>
      <br />
      <Container>
        <Row>
          <Col lg={{span: 8, offset: 0}}>
            <InputGroup className="mb-3">
              <InputGroup.Prepend>
                <InputGroup.Text  id="basic-addon3">
                  Search Local Models
                </InputGroup.Text>
              </InputGroup.Prepend>
              <FormControl id="basic-url" aria-describedby="basic-addon3" placeholder="ex: Botnet, Regression" onChange={this.props.handle_local_search_term_change} />
              <InputGroup.Append>
                <Button variant="outline-info" onClick={this.props.handle_local_search_term_submit}>Find</Button>
              </InputGroup.Append>
            </InputGroup>
          </Col>
        </Row>
      </Container>
      </>
    )
  }
}

const ModelTabs = (props) => (
  <Container>
    <Row>
      <Col>
        <Card>
          <Card.Header>
            <p style={{color: "black", textAlign: "left"}}>Models</p>
          </Card.Header>
          <Card.Body>
            <Tabs defaultActiveKey="manage" id="uncontrolled-tab-example">
              <Tab eventKey="manage" title="Library">
                <br/>
                <ModelLibrarySearchBar
                handle_ml_search_term_change={props.handle_ml_search_term_change}
                handle_ml_search_term_submit={props.handle_ml_search_term_submit}/>
                <Container>
                  <Row className="row">

                    <Col id="system_log">
                      <Card>
                        <Card.Body>
                          <p>Results</p>
                          <Spinner animation="border" role="status">
                            <span className="sr-only">Loading...</span>
                          </Spinner>
                        </Card.Body>
                      </Card>
                    </Col>

                  </Row>
                </Container>
              </Tab>

              <Tab eventKey="installed" title="Installed">
                <ModelLocalSearchBar
                handle_local_search_term_change={props.handle_local_search_term_change}
                handle_local_search_term_submit={props.handle_local_search_term_submit}
                />
                <Container>
                  <Row className="row">
                    <Col id="system_log">
                      <Card>
                        <Card.Body>
                          <ListGroup style={{color: "black"}}>
                            <ListGroup.Item>Model #1</ListGroup.Item>
                            <ListGroup.Item>Model #2</ListGroup.Item>
                            <ListGroup.Item>Model #3</ListGroup.Item>
                          </ListGroup>
                        </Card.Body>
                      </Card>
                    </Col>
                  </Row>
                </Container>
              </Tab>

              <Tab eventKey="Jobs" title="Jobs">
                <p>Model Jobs Scheduler</p>
                <ListGroup style={{color: "black"}}>
                  <ListGroup.Item>Job #1</ListGroup.Item>
                  <ListGroup.Item>Job #2</ListGroup.Item>
                  <ListGroup.Item>Job #3</ListGroup.Item>
                </ListGroup>
              </Tab>


            </Tabs>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  </Container>
);

//const Models = () => (
class Models extends React.Component {

  constructor(props){
    super(props)

    // on change
    this.handle_ml_search_term_change = this.handle_ml_search_term_change.bind(this);
    this.handle_local_search_term_change = this.handle_local_search_term_change.bind(this);

    //on submit
    this.handle_ml_search_term_submit = this.handle_ml_search_term_submit.bind(this);
    this.handle_local_search_term_submit = this.handle_local_search_term_submit.bind(this);


    this.state = {
      model_library_search_term: "blank model library search term",
      model_local_search_term: "blank model local search term"
    }

  }

  handle_ml_search_term_change(event){
    console.log("handle_ml_search_term_change")
    this.setState({
      model_library_search_term: event.target.value
    })
    event.preventDefault();
  }

  handle_local_search_term_change(event){
    console.log("handle_local_search_term_change")
    this.setState({
      model_local_search_term: event.target.value
    })
    event.preventDefault();
  }

  handle_ml_search_term_submit(event){
    console.log("handle_ml_search_term_submit")
    // send ml search submit
    window.ipcRenderer.send('model_library_search_call_message', this.state["model_library_search_term"])
    event.preventDefault();
  }

  handle_local_search_term_submit(event){
    console.log("handle_local_search_term_submit")
    // send local search submit
    window.ipcRenderer.send('local_search_call_message', this.state["model_local_search_term"])
    event.preventDefault();
  }

  async componentDidMount(props){
    //callback for model_library_search_call_reply
    window.ipcRenderer.on('model_library_search_call_reply', (event, result) => {
      console.log("model_library_search_call_reply returned result")
      console.log(result)
    })

    //callback for local_search_call_reply
    window.ipcRenderer.on('local_search_call_reply', (event, result) => {
      console.log("local_search_call_reply returned result")
      console.log(result)
    })
  }

  render(props){
    return (
      <ModelContext.Provider value={this.state}>
        <ModelContext.Consumer>
          {( {model_library_search_term} ) => (

            <div className="models">
              <ModelTabs
              handle_ml_search_term_change={this.handle_ml_search_term_change}
              handle_local_search_term_change={this.handle_local_search_term_change}
              handle_ml_search_term_submit={this.handle_ml_search_term_submit}
              handle_local_search_term_submit={this.handle_local_search_term_submit}
              />
            </div>

          )}
        </ModelContext.Consumer>
      </ModelContext.Provider>
    )
  }
}

export default Models;
