// Set the dimensions of the canvas / graph
var margin = {
              top: 30,
              right: 20,
              bottom: 30,
              left: 30
            },
            width = 380 - margin.left - margin.right,
            height = 200 - margin.top - margin.bottom;

// Parse the date / time
var parseDate = d3.time.format("%d-%b-%y").parse;

// Set the ranges
var x = d3.time.scale().range([0, width]);
var y = d3.scale.linear().range([height, 0]);

// Define the axes
var xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(5);

var yAxis = d3.svg.axis().scale(y).orient("left").ticks(5);

// Define the line
var valueline = d3.svg.line()
    .x(function(d) { return x(d.date); })
    .y(function(d) { return y(d.x); });

// Adds the svg canvas
var svg = d3.select("#d3_main")
.append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
.append("g")
    .attr("transform",
          "translate(" + margin.left + "," + margin.top + ")");

// The new data variable.
var data = [
{date: "1-May-12", x: 58.13},
{date: "30-Apr-12", x: 68.13},
];

data.forEach(function(d) {
  d.date = parseDate(d.date);
  d.x = +d.x;
});

// The following code was contained in the callback function.
x.domain(data.map(function(d) { return d.date; }));
y.domain([0, d3.max(data, function(d) { return d.x; })]);

// Add the valueline path.
svg.append("path")
  .attr("class", "line")
  .attr("d", valueline(data));

// Add the X Axis
svg.append("g")
  .attr("class", "x axis")
  .attr("transform", "translate(0," + height + ")")
  .call(xAxis);

// Add the Y Axis
svg.append("g")
  .attr("class", "y axis")
  .call(yAxis);
