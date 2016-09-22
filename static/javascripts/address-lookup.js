var addressLookup = function(event) {
    var input = $("#address-lookup :input[name='search']"),
        searchValue = input.val().trim();
    event.preventDefault();
    $('#address-selector').hide();
    $('#addresses').empty();
    $('.message').empty();

    $.ajax({
          type: 'GET',
          url: '/address-search?q='+searchValue+'&q.options={fields:["postcode","street"]}&sort=street asc',
          contentType: 'application/json',
          success: function(data) {
                renderAddresses(data);
                $('#address-selector').show();
          },
          error: function(xhr, options, error) {
            console.log(error);
            $('#addresses').empty();
            $('.message').text('No results');
        }
    });
};

var renderAddresses = function(addresses) {
    $.each(addresses.hits.hit, function(index, address) {
        var template = $.templates("#address-template"),
            html = template.render({
                'address': address.fields.address,
                'property': address.fields.property,
                'street': address.fields.street,
                'town': address.fields.town
            });
        $('#addresses').append(html);
    });
};


$(document).ready(function(){
    $('#address-lookup').submit(addressLookup);
});
