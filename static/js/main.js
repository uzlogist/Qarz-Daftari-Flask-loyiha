$(document).ready(function () {
    $('#searchBox').on('input', function () {
        const query = $(this).val();
        if (query.length > 0) {
            $.get(`/search?query=${query}`, function (data) {
                const results = $('#searchResults');
                results.empty();
                if (Object.keys(data).length > 0) {
                    for (const [name, info] of Object.entries(data)) {
                        results.append(`<p><strong>${name}</strong>: ${info.debt} so'm qarz, ${info.paid} so'm to'lagan</p>`);
                    }
                } else {
                    results.append('<p>Hech narsa topilmadi.</p>');
                }
            });
        } else {
            $('#searchResults').empty();
        }
    });
});