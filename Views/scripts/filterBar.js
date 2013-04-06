
function showFilterBar()
{
    document.getElementById("filterBar").visibility = "show";
}

function hideFilterBar()
{
    document.getElementById("filterBar").visibility = "hidden";
}

document.write('<div id="filterBar" style="position: absolute; top: 10px; left: 10px;">' +
    '<div style="height:600px; background-color: #000000;">' +
    '<ul>' +
    '<li><a href="Javascript:hideFilterBar();">A</a></li>' +
    '<li>A</li>' +
    '<li>A</li>' +
    '<li>A</li>' +
    '<li>A</li>' +
    '<li>A</li>' +
    '<li>A</li>' +
    '<li>A</li>' +
    '</ul>' +
    '</div>' +
    '</div>');