/* credit: https://stackoverflow.com/questions/10683712/html-table-sort */

var lstindex = -1;
var lstcount = 0;

window.onload = function() {
    document.querySelectorAll('th').forEach((element) => { // Table headers
        element.addEventListener('click', function() {
            let table = this.closest('table');
            let idx = element.cellIndex; // index
            
            // If the column is sortable
            if (this.querySelector('span')) {
                
                if (idx != lstindex) {
                    lstindex = idx;
                    lstcount = 0;
                } else {
                    lstcount += 1;
                }
                let order = lstcount % 2 == 0 ? "asc" : "desc";

                let order_icon = this.querySelector('span');
                if (order === 'desc') {
                    order_icon.innerHTML = '&darr;';
                } else {
                    order_icon.innerHTML = '&uarr;';
                }
                $('.sortable-th').hide();
                //$(order_icon).show();

                
                let separator = '-----'; // Separate the value of it's index, so data keeps intact

                let value_list = {}; // <tr> Object
                let obj_key = []; // Values of selected column

                let string_count = 0;
                let number_count = 0;

                // <tbody> rows
                table.querySelectorAll('tbody tr').forEach((line, index_line) => {
                    // Value of each field

                    let key = line.children[idx].textContent.toUpperCase();

                    // Check if value is distance, numeric or string
                    if (line.children[idx].hasAttribute('distance')) {
                        // if value is distance, we can sort like a number
                        key = line.children[idx].getAttribute('distance');
                    } else if (key.replace('-', '').match(/^[0-9,.]*$/g)) {
                        number_count++;
                    } else {
                        string_count++;
                    }

                    value_list[key + separator + index_line] = line.outerHTML.replace(/(\t)|(\n)/g, ''); // Adding <tr> to object
                    obj_key.push(key + separator + index_line);
                });
                if (string_count === 0) { // If all values are numeric
                    obj_key.sort(function(a, b) {
                        return a.split(separator)[0] - b.split(separator)[0];
                    });
                } else {
                    obj_key.sort();
                }

                if (order === 'desc') {
                    obj_key.reverse();
                } else {
                }

                let html = '';
                obj_key.forEach(function(chave) {
                    html += value_list[chave];
                });
                table.getElementsByTagName('tbody')[0].innerHTML = html;
            }
        });
    });
};


