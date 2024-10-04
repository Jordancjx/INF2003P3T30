// Material Design example
$(document).ready(function () {
    let table = $('#history-table', 'section.history');
    let trs = $('tbody tr', '#history-table');

    table.DataTable({
        ordering: true,
        order: [[1, 'asc']],
        paging: false,
        info: false,
        searching: false,
        language: { emptyTable: 'No purchase history.' },
        columnDefs: [{
            orderable: false,
            targets: 2
        }],
    });

    $('input[name="search"]', 'section.history').on('keyup', function() {
        let val = $(this).val().toLowerCase().replace(/</g, '&lt;').replace(/>/g, '&gt;');
        let shown = trs.length;

        trs.each(function() {
            let _this = $(this);

            if (val) {
                let tds = _this.children('td[headers]:not([id="empty-search"])');
                let show = false;

                for (let i = 0, n = tds.length; i < n && !show; i++) {
                    td = $(tds[i]);

                    if (td.text().toLowerCase().indexOf(val) > -1) {
                        show = true;
                    }
                }

                if (show && _this.attr('style')) {
                    _this.removeAttr('style');

                    _this.addClass('flipInX').one('animationend', function() {
                        _this.removeClass('flipInX');
                    });
                }
                else if (!show) {
                    if (!_this.attr('style')) {
                        _this.addClass('flipOutX').one('animationend', function() {
                            _this.removeClass('flipOutX');
                            _this.prop('style', 'display: none !important;');
                        });
                    }

                    shown--;
                }
            }
            else {
                if (_this.attr('style')) {
                    _this.removeAttr('style');
                    _this.addClass('flipInX').one('animationend', function() {
                        $(this).removeClass('flipInX');
                    });
                }
            }
        });

        $('#empty-search', '#history-table').remove();

        if (shown < 1) {
            $('tbody', '#history-table').prepend(`
                <tr id="empty-search">
                    <td class="rounded-bottom" colspan=100>
                        Couldn\'t find anything for <span class="font-weight-bolder">${val}</span>
                    </td>
                </tr>
            `);
        }
    });
});