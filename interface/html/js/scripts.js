/*
@name
@description
*/
class Network {

  /*
  @name make_request
  @description
  */
  make_request(url, data_object, network_callback){
    $.ajax({
      url: url,
      //data: data_object,
      headers: {

      },
      dataType: "json",
      type: "get",
      success: function( result ) {
        console.log("success")
        network_callback(result)
      },
      error: function( error ){
         console.info("Error: "+error)
         console.info(error)
      },
    });
  }
}

/*
@name
@description
*/
class API {

  API_SERVER = "http://localhost:5000"

  constructor() {
    this.network = new Network()
  }

  /*
  @name get_all_entities
  @description fetch all entities from server
  */
  get_all_entities(){
    let complete_endpoint = this.API_SERVER+"/display/get_all_entities"
    this.network.make_request(complete_endpoint, {
      endpoint: "data"
    },
    (function(network_response){
      console.log("Network response: "+network_response)
    }))
  }

  /*
  @name get_all_users
  @description fetch all entities from server
  */
  get_all_users(){
    let complete_endpoint = this.API_SERVER+"/display/get_all_users"
    this.network.make_request(complete_endpoint, {
      endpoint: "data"
    },
    (function(network_response){
      console.log("Network response: "+network_response)
    }))
  }

  /*
  @name get_system_log
  @description fetch system log
  */
  get_system_log(){
    let complete_endpoint = this.API_SERVER+"/display/get_system_log"
    this.network.make_request(complete_endpoint, {
      endpoint: "data"
    },
    (function(network_response){
      console.log("Network response: "+network_response)
    }))
  }
}

/*
@name Renderer
@description set any html element on the UI through this renderer
*/
class Renderer {
  constructor() {}

  /*
  @name set_element_html
  @description set the element
  */
  set_element_html(element_to_set, new_html){
    $( element_to_set ).html( new_html )
  }
}


/*
@name Sync
@description contain all sync behavior
*/
class Sync {

  /*
  @name interval
  @description the interval block
  */
  interval(){

    if (false){
      // perform sync actions
      let renderer = new Renderer()
      let api = new API()
      api.get_all_users()
      api.get_all_entities()
      api.get_system_log()
    }

    $("SystemLog").html("test system log")

  }

  /*
  @name initiate
  @description start the sync process for client side on interval
  */
  initiate(){
    console.log("Sync Initiated...")
    setInterval(this.interval, 5000)
  }
}

// make sync object
let sync = new Sync()
sync.initiate()
